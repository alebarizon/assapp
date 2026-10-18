from django.db import transaction
from django.db.models import Sum
from django.utils.text import slugify
from rest_framework import serializers

from ecommerce.models import CatalogItemType

from .html_sanitizer import sanitize_html
from .models import (
    Course,
    CourseEnrollment,
    CourseSection,
    Lesson,
    LessonAttachment,
    LessonQuestion,
    LessonQuestionReply,
    QuizOption,
    QuizQuestion,
)
from .services import progress_summary, youtube_video_id

# Mantenha abaixo de client_max_body_size nos configs do nginx (nginx/*.conf)
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024


def _absolute(request, file_field):
    if not file_field:
        return None
    url = file_field.url
    return request.build_absolute_uri(url) if request else url


def _clean_text(value, message):
    if not value or not str(value).strip():
        raise serializers.ValidationError(message)
    return " ".join(str(value).strip().split())


def _catalog_payload(item):
    if not item:
        return None
    return {
        "id": str(item.id),
        "slug": item.slug,
        "name": item.name,
        "price": str(item.price),
        "member_price": str(item.member_price) if item.member_price is not None else None,
        "currency": item.currency,
        "is_active": item.is_active,
    }


def _short_name(nome_completo: str) -> str:
    """"Ana Maria Silva" → "Ana S." (exibição em perguntas visíveis aos colegas)."""
    parts = (nome_completo or "").split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


# ---------------------------------------------------------------- Builder (diretoria)


class QuizOptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = QuizOption
        fields = ["id", "text", "is_correct", "position"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    options = QuizOptionSerializer(many=True)

    class Meta:
        model = QuizQuestion
        fields = ["id", "prompt", "question_type", "explanation", "position", "options"]

    def validate(self, attrs):
        options = attrs.get("options") or []
        if len(options) < 2:
            raise serializers.ValidationError({"options": "Informe ao menos duas alternativas."})
        correct = [o for o in options if o.get("is_correct")]
        if not correct:
            raise serializers.ValidationError({"options": "Marque ao menos uma alternativa correta."})
        if attrs.get("question_type") != QuizQuestion.MULTIPLE and len(correct) > 1:
            raise serializers.ValidationError(
                {"options": "Este tipo de questão aceita apenas uma alternativa correta."}
            )
        return attrs


class LessonAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LessonAttachment
        fields = ["id", "lesson", "title", "file", "file_url", "file_type", "size_bytes", "position", "created_at"]
        read_only_fields = ["id", "file_url", "file_type", "size_bytes", "created_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_url(self, obj):
        return _absolute(self.context.get("request"), obj.file)

    def validate_title(self, value):
        return _clean_text(value, "Título é obrigatório.")

    def validate_file(self, value):
        if getattr(value, "size", 0) > MAX_ATTACHMENT_BYTES:
            raise serializers.ValidationError("O arquivo deve ter no máximo 20 MB.")
        return value

    def create(self, validated_data):
        upload = validated_data["file"]
        validated_data["size_bytes"] = getattr(upload, "size", 0) or 0
        name = getattr(upload, "name", "") or ""
        validated_data["file_type"] = name.rsplit(".", 1)[-1].lower()[:20] if "." in name else ""
        if "position" not in validated_data:
            last = validated_data["lesson"].attachments.order_by("-position").first()
            validated_data["position"] = (last.position + 1) if last else 1
        return super().create(validated_data)


class LessonSerializer(serializers.ModelSerializer):
    attachments = LessonAttachmentSerializer(many=True, read_only=True)
    questions = QuizQuestionSerializer(many=True, required=False)
    youtube_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "section",
            "title",
            "lesson_type",
            "content",
            "video_url",
            "youtube_id",
            "duration_minutes",
            "is_preview",
            "position",
            "attachments",
            "questions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "youtube_id", "attachments", "created_at", "updated_at"]

    def get_youtube_id(self, obj):
        return youtube_video_id(obj.video_url)

    def validate_title(self, value):
        return _clean_text(value, "Título é obrigatório.")

    def validate_content(self, value):
        return sanitize_html(value)

    def validate(self, attrs):
        lesson_type = attrs.get("lesson_type") or (self.instance.lesson_type if self.instance else Lesson.TEXT)
        video_url = attrs.get("video_url", self.instance.video_url if self.instance else "")
        if lesson_type == Lesson.VIDEO and not youtube_video_id(video_url):
            raise serializers.ValidationError({"video_url": "Informe um link válido do YouTube."})
        if lesson_type == Lesson.QUIZ and attrs.get("is_preview"):
            attrs["is_preview"] = False
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        questions = validated_data.pop("questions", None)
        if "position" not in validated_data:
            last = validated_data["section"].lessons.order_by("-position").first()
            validated_data["position"] = (last.position + 1) if last else 1
        lesson = Lesson.objects.create(**validated_data)
        if questions is not None:
            self._sync_questions(lesson, questions)
        return lesson

    @transaction.atomic
    def update(self, instance, validated_data):
        questions = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions is not None:
            self._sync_questions(instance, questions)
        return instance

    def _sync_questions(self, lesson, questions):
        keep = []
        for q_index, q_data in enumerate(questions, start=1):
            options = q_data.pop("options", [])
            q_id = q_data.pop("id", None)
            q_data["position"] = q_index
            question = lesson.questions.filter(pk=q_id).first() if q_id else None
            if question:
                for attr, value in q_data.items():
                    setattr(question, attr, value)
                question.save()
            else:
                question = QuizQuestion.objects.create(lesson=lesson, **q_data)
            keep.append(question.id)
            keep_options = []
            for o_index, o_data in enumerate(options, start=1):
                o_id = o_data.pop("id", None)
                o_data["position"] = o_index
                option = question.options.filter(pk=o_id).first() if o_id else None
                if option:
                    for attr, value in o_data.items():
                        setattr(option, attr, value)
                    option.save()
                else:
                    option = QuizOption.objects.create(question=question, **o_data)
                keep_options.append(option.id)
            question.options.exclude(id__in=keep_options).delete()
        lesson.questions.exclude(id__in=keep).delete()


class CourseSectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = CourseSection
        fields = ["id", "course", "title", "position", "lessons", "created_at"]
        read_only_fields = ["id", "lessons", "created_at"]

    def validate_title(self, value):
        return _clean_text(value, "Título é obrigatório.")

    def create(self, validated_data):
        if "position" not in validated_data:
            last = validated_data["course"].sections.order_by("-position").first()
            validated_data["position"] = (last.position + 1) if last else 1
        return super().create(validated_data)


class CourseListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    catalog_item_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    lessons_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    unanswered_questions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "cover_image_url",
            "level",
            "status",
            "status_display",
            "visibility",
            "progression_mode",
            "catalog_item",
            "catalog_item_info",
            "lessons_count",
            "students_count",
            "unanswered_questions_count",
            "created_at",
            "updated_at",
        ]

    def get_cover_image_url(self, obj):
        return _absolute(self.context.get("request"), obj.cover_image)

    def get_catalog_item_info(self, obj):
        return _catalog_payload(obj.catalog_item)


class CourseSerializer(serializers.ModelSerializer):
    sections = CourseSectionSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    catalog_item_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    remove_cover_image = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "description",
            "cover_image",
            "cover_image_url",
            "remove_cover_image",
            "instructor_name",
            "workload_hours",
            "level",
            "progression_mode",
            "status",
            "status_display",
            "visibility",
            "catalog_item",
            "catalog_item_info",
            "certificate_enabled",
            "sections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "cover_image_url",
            "catalog_item_info",
            "status_display",
            "sections",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "cover_image": {"write_only": True, "required": False},
            "slug": {"required": False},
        }

    def get_cover_image_url(self, obj):
        return _absolute(self.context.get("request"), obj.cover_image)

    def get_catalog_item_info(self, obj):
        return _catalog_payload(obj.catalog_item)

    def validate_title(self, value):
        return _clean_text(value, "Título é obrigatório.")

    def validate_description(self, value):
        return sanitize_html(value)

    def validate_slug(self, value):
        value = slugify(value or "")
        if not value:
            return value
        qs = Course.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um curso com este endereço.")
        return value

    def validate_catalog_item(self, value):
        if value and value.item_type != CatalogItemType.CURSO:
            raise serializers.ValidationError("Vincule um item do catálogo do tipo Curso / workshop.")
        return value

    def update(self, instance, validated_data):
        if validated_data.pop("remove_cover_image", False):
            instance.cover_image = None
        if validated_data.get("slug") == "":
            validated_data.pop("slug")
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data.pop("remove_cover_image", None)
        if not validated_data.get("slug"):
            validated_data.pop("slug", None)
        return super().create(validated_data)


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    membro_email = serializers.CharField(source="membro.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    progress = serializers.SerializerMethodField()
    average_quiz_score = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "membro",
            "membro_nome",
            "membro_email",
            "status",
            "status_display",
            "enrolled_at",
            "completed_at",
            "last_accessed_at",
            "certificate_code",
            "progress",
            "average_quiz_score",
        ]
        read_only_fields = fields

    def get_progress(self, obj):
        return progress_summary(obj, lessons=self.context.get("lessons"))

    def get_average_quiz_score(self, obj):
        latest = {}
        for attempt in obj.quiz_attempts.order_by("created_at"):
            latest[attempt.lesson_id] = attempt.score_percent
        if not latest:
            return None
        return int(round(sum(latest.values()) / len(latest)))


# ---------------------------------------------------------------- Perguntas e respostas


class LessonQuestionReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuestionReply
        fields = ["id", "author_name", "is_instructor", "body", "created_at"]
        read_only_fields = fields

    def get_author_name(self, obj):
        if obj.is_instructor:
            return obj.author.get_full_name() or obj.author.email
        membro = getattr(obj.author, "membro_perfil", None)
        if membro is not None:
            return _short_name(membro.nome_completo)
        return obj.author.first_name or obj.author.email


class LessonQuestionSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    replies = LessonQuestionReplySerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course_id = serializers.UUIDField(source="lesson.section.course_id", read_only=True)
    course_title = serializers.CharField(source="lesson.section.course.title", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuestion
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "course_id",
            "course_title",
            "author_name",
            "is_mine",
            "body",
            "is_answered",
            "replies",
            "created_at",
        ]
        read_only_fields = fields

    def get_author_name(self, obj):
        return _short_name(obj.membro.nome_completo)

    def get_is_mine(self, obj):
        membro = self.context.get("membro")
        return bool(membro and obj.membro_id == membro.id)


# ---------------------------------------------------------------- Portal (associado)


def _lesson_outline(lesson, completed, unlocked):
    return {
        "id": str(lesson.id),
        "title": lesson.title,
        "lesson_type": lesson.lesson_type,
        "duration_minutes": lesson.duration_minutes,
        "completed": lesson.id in completed,
        "locked": lesson.id not in unlocked,
    }


class PortalEnrollmentSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    certificate_available = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "status",
            "enrolled_at",
            "completed_at",
            "last_lesson",
            "course",
            "progress",
            "certificate_available",
        ]
        read_only_fields = fields

    def _state(self, obj):
        cache = self.context.setdefault("_state", {})
        if obj.id not in cache:
            from .services import completed_lesson_ids, ordered_lessons, unlocked_lesson_ids

            lessons = ordered_lessons(obj.course)
            completed = completed_lesson_ids(obj)
            cache[obj.id] = (lessons, completed, unlocked_lesson_ids(obj, lessons, completed))
        return cache[obj.id]

    def get_progress(self, obj):
        lessons, completed, _ = self._state(obj)
        return progress_summary(obj, lessons=lessons, completed=completed)

    def get_certificate_available(self, obj):
        return (
            obj.course.certificate_enabled
            and obj.status == CourseEnrollment.COMPLETED
            and bool(obj.certificate_code)
        )

    def get_course(self, obj):
        course = obj.course
        data = {
            "id": str(course.id),
            "title": course.title,
            "slug": course.slug,
            "short_description": course.short_description,
            "cover_image_url": _absolute(self.context.get("request"), course.cover_image),
            "instructor_name": course.instructor_name,
            "workload_hours": course.workload_hours,
            "level": course.level,
            "progression_mode": course.progression_mode,
        }
        if self.context.get("include_outline"):
            lessons, completed, unlocked = self._state(obj)
            by_section = {}
            for lesson in lessons:
                by_section.setdefault(lesson.section_id, []).append(lesson)
            data["description"] = course.description
            data["sections"] = [
                {
                    "id": str(section.id),
                    "title": section.title,
                    "lessons": [
                        _lesson_outline(lesson, completed, unlocked)
                        for lesson in by_section.get(section.id, [])
                    ],
                }
                for section in course.sections.order_by("position", "created_at")
            ]
        return data


def portal_lesson_payload(lesson, request, include_quiz=True):
    payload = {
        "id": str(lesson.id),
        "section_id": str(lesson.section_id),
        "title": lesson.title,
        "lesson_type": lesson.lesson_type,
        "content": lesson.content,
        "youtube_id": youtube_video_id(lesson.video_url),
        "duration_minutes": lesson.duration_minutes,
        "attachments": [
            {
                "id": str(a.id),
                "title": a.title,
                "file_url": _absolute(request, a.file),
                "file_type": a.file_type,
                "size_bytes": a.size_bytes,
            }
            for a in lesson.attachments.order_by("position", "created_at")
        ],
    }
    if include_quiz and lesson.lesson_type == Lesson.QUIZ:
        payload["questions"] = [
            {
                "id": str(q.id),
                "prompt": q.prompt,
                "question_type": q.question_type,
                "options": [
                    {"id": str(o.id), "text": o.text} for o in q.options.order_by("position", "id")
                ],
            }
            for q in lesson.questions.order_by("position", "id")
        ]
    return payload


# ---------------------------------------------------------------- Catálogo público


class PublicCourseSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    catalog_item_info = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "title",
            "short_description",
            "cover_image_url",
            "instructor_name",
            "workload_hours",
            "level",
            "progression_mode",
            "certificate_enabled",
            "catalog_item_info",
            "lessons_count",
            "total_duration_minutes",
        ]

    def _lessons(self, obj):
        return Lesson.objects.filter(section__course=obj)

    def get_cover_image_url(self, obj):
        return _absolute(self.context.get("request"), obj.cover_image)

    def get_catalog_item_info(self, obj):
        if obj.catalog_item and obj.catalog_item.is_active:
            return _catalog_payload(obj.catalog_item)
        return None

    def get_lessons_count(self, obj):
        return self._lessons(obj).count()

    def get_total_duration_minutes(self, obj):
        return self._lessons(obj).aggregate(total=Sum("duration_minutes"))["total"] or 0


class PublicCourseDetailSerializer(PublicCourseSerializer):
    sections = serializers.SerializerMethodField()

    class Meta(PublicCourseSerializer.Meta):
        fields = PublicCourseSerializer.Meta.fields + ["description", "sections"]

    def get_sections(self, obj):
        return [
            {
                "id": str(section.id),
                "title": section.title,
                "lessons": [
                    {
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "lesson_type": lesson.lesson_type,
                        "duration_minutes": lesson.duration_minutes,
                        "is_preview": lesson.is_preview and lesson.lesson_type != Lesson.QUIZ,
                    }
                    for lesson in section.lessons.order_by("position", "created_at")
                ],
            }
            for section in obj.sections.order_by("position", "created_at")
        ]
