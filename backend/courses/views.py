"""
API do módulo Cursos.

Diretoria: /api/courses/ (+ sections, lessons, attachments, questions, uploads)
Associado: /api/courses/my/
Público:   /api/courses/public/?schema=<schema>
"""
import os
import uuid
from decimal import Decimal, InvalidOperation

from django.core.files.storage import default_storage
from django.db import connection, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.models import CatalogItem, CatalogItemType
from mandatos.permissions import IsBoardOrAdmin
from membros.services import resolver_membro_do_user
from tenants.resolvers import resolve_tenant_from_request

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
from .serializers import (
    CourseListSerializer,
    CourseSectionSerializer,
    CourseSerializer,
    LessonAttachmentSerializer,
    LessonQuestionSerializer,
    LessonSerializer,
    PortalEnrollmentSerializer,
    PublicCourseDetailSerializer,
    PublicCourseSerializer,
    StudentEnrollmentSerializer,
    portal_lesson_payload,
)
from .services import (
    build_enrollment_certificate,
    completed_lesson_ids,
    enroll_membro,
    enrollment_has_access,
    grade_quiz,
    mark_lesson_complete,
    ordered_lessons,
    prefetch_course_tree,
    refresh_completion,
    submit_quiz,
    touch_last_lesson,
    unlocked_lesson_ids,
)

UUID_LOOKUP = r"[0-9a-fA-F-]{36}"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def _tenant_name(request) -> str:
    tenant = getattr(request.user, "_tenant", None) or getattr(connection, "tenant", None)
    return getattr(tenant, "name", "") or ""


class BoardMixin:
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "cursos"


class CourseViewSet(BoardMixin, viewsets.ModelViewSet):
    lookup_value_regex = UUID_LOOKUP
    pagination_class = None
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_class(self):
        return CourseListSerializer if self.action == "list" else CourseSerializer

    def get_queryset(self):
        qs = Course.objects.select_related("catalog_item")
        if self.action == "list":
            qs = qs.annotate(
                lessons_count=Count("sections__lessons", distinct=True),
                students_count=Count(
                    "enrollments",
                    filter=~Q(enrollments__status=CourseEnrollment.REVOKED),
                    distinct=True,
                ),
                unanswered_questions_count=Count(
                    "sections__lessons__student_questions",
                    filter=Q(sections__lessons__student_questions__is_answered=False),
                    distinct=True,
                ),
            )
            status_param = self.request.query_params.get("status")
            if status_param:
                qs = qs.filter(status=status_param)
            search = self.request.query_params.get("search")
            if search:
                qs = qs.filter(Q(title__icontains=search) | Q(short_description__icontains=search))
        else:
            qs = prefetch_course_tree(qs)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _detail_response(self, request, course_id, status_code=status.HTTP_200_OK):
        course = prefetch_course_tree(Course.objects.select_related("catalog_item").filter(pk=course_id)).get()
        return Response(CourseSerializer(course, context={"request": request}).data, status=status_code)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        source = self.get_object()
        with transaction.atomic():
            clone = Course.objects.create(
                title=f"{source.title} (cópia)",
                short_description=source.short_description,
                description=source.description,
                cover_image=source.cover_image,
                instructor_name=source.instructor_name,
                workload_hours=source.workload_hours,
                level=source.level,
                progression_mode=source.progression_mode,
                visibility=source.visibility,
                certificate_enabled=source.certificate_enabled,
                status=Course.DRAFT,
                created_by=request.user,
            )
            for section in source.sections.order_by("position", "created_at"):
                new_section = CourseSection.objects.create(
                    course=clone, title=section.title, position=section.position
                )
                for lesson in section.lessons.order_by("position", "created_at"):
                    new_lesson = Lesson.objects.create(
                        section=new_section,
                        title=lesson.title,
                        lesson_type=lesson.lesson_type,
                        content=lesson.content,
                        video_url=lesson.video_url,
                        duration_minutes=lesson.duration_minutes,
                        is_preview=lesson.is_preview,
                        position=lesson.position,
                    )
                    for att in lesson.attachments.all():
                        LessonAttachment.objects.create(
                            lesson=new_lesson,
                            title=att.title,
                            file=att.file,
                            file_type=att.file_type,
                            size_bytes=att.size_bytes,
                            position=att.position,
                        )
                    for question in lesson.questions.all():
                        new_q = QuizQuestion.objects.create(
                            lesson=new_lesson,
                            prompt=question.prompt,
                            question_type=question.question_type,
                            explanation=question.explanation,
                            position=question.position,
                        )
                        QuizOption.objects.bulk_create(
                            [
                                QuizOption(
                                    question=new_q,
                                    text=o.text,
                                    is_correct=o.is_correct,
                                    position=o.position,
                                )
                                for o in question.options.all()
                            ]
                        )
        return self._detail_response(request, clone.pk, status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="create-catalog-item")
    def create_catalog_item(self, request, pk=None):
        """Cria o item do catálogo (tipo curso) para vender o curso na loja e o vincula."""
        course = self.get_object()
        if course.catalog_item_id:
            raise ValidationError({"detail": "Este curso já está vinculado a um item do catálogo."})
        try:
            price = Decimal(str(request.data.get("price"))).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            price = None
        if price is None or price < 0:
            raise ValidationError({"price": "Informe um valor igual ou maior que zero."})
        member_price = None
        if request.data.get("member_price") not in (None, ""):
            try:
                member_price = Decimal(str(request.data.get("member_price"))).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError, ValueError):
                raise ValidationError({"member_price": "Valor inválido."})
            if member_price < 0 or member_price > price:
                raise ValidationError({"member_price": "Preço de sócio deve ficar entre zero e o preço cheio."})
        item = CatalogItem.objects.create(
            name=course.title,
            description=course.short_description or "",
            item_type=CatalogItemType.CURSO,
            price=price,
            member_price=member_price,
            currency="BRL",
            image_url=request.build_absolute_uri(course.cover_image.url) if course.cover_image else None,
            is_active=True,
            created_by=request.user,
        )
        course.catalog_item = item
        course.save(update_fields=["catalog_item", "updated_at"])
        return self._detail_response(request, course.pk)

    @action(detail=True, methods=["post"], url_path="reorder")
    def reorder(self, request, pk=None):
        """
        Body: {"sections": [{"id": <section>, "lesson_ids": [<lesson>, ...]}, ...]}
        Permite mover aulas entre seções.
        """
        course = self.get_object()
        payload = request.data.get("sections")
        if not isinstance(payload, list):
            raise ValidationError({"sections": "Envie a lista de seções na nova ordem."})
        sections = {str(s.id): s for s in course.sections.all()}
        lessons = {str(lesson.id): lesson for lesson in Lesson.objects.filter(section__course=course)}
        with transaction.atomic():
            for s_index, item in enumerate(payload, start=1):
                section = sections.get(str(item.get("id")))
                if not section:
                    raise ValidationError({"sections": "Seção inválida na lista."})
                section.position = s_index
                section.save(update_fields=["position"])
                for l_index, lesson_id in enumerate(item.get("lesson_ids") or [], start=1):
                    lesson = lessons.get(str(lesson_id))
                    if not lesson:
                        raise ValidationError({"sections": "Aula inválida na lista."})
                    lesson.section = section
                    lesson.position = l_index
                    lesson.save(update_fields=["section", "position", "updated_at"])
        return self._detail_response(request, course.pk)

    @action(detail=True, methods=["get", "post"], url_path="students")
    def students(self, request, pk=None):
        """GET: alunos + progresso. POST {membro}: matrícula manual pela diretoria."""
        course = self.get_object()
        lessons = ordered_lessons(course)
        if request.method == "POST":
            from membros.models import Membro

            membro = Membro.objects.filter(pk=request.data.get("membro")).first()
            if not membro:
                raise ValidationError({"membro": "Associado não encontrado."})
            enrollment, reason = enroll_membro(course, membro)
            if not enrollment:
                raise ValidationError({"detail": "Publique o curso antes de matricular associados."})
            data = StudentEnrollmentSerializer(enrollment, context={"lessons": lessons}).data
            return Response(
                {**data, "reason": reason},
                status=status.HTTP_201_CREATED if reason == "created" else status.HTTP_200_OK,
            )
        qs = course.enrollments.select_related("membro", "course").prefetch_related(
            "lesson_progress", "quiz_attempts"
        )
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return Response(StudentEnrollmentSerializer(qs, many=True, context={"lessons": lessons}).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"students/(?P<enrollment_id>[0-9a-fA-F-]{36})",
    )
    def student_status(self, request, pk=None, enrollment_id=None):
        """Revogar ou reativar o acesso de um aluno (ex.: estorno)."""
        course = self.get_object()
        enrollment = get_object_or_404(course.enrollments, pk=enrollment_id)
        new_status = request.data.get("status")
        if new_status == CourseEnrollment.REVOKED:
            enrollment.status = CourseEnrollment.REVOKED
            enrollment.save(update_fields=["status"])
        elif new_status == CourseEnrollment.ACTIVE:
            enrollment.status = CourseEnrollment.ACTIVE
            enrollment.save(update_fields=["status"])
            refresh_completion(enrollment)
        else:
            raise ValidationError({"status": "Status inválido."})
        enrollment.refresh_from_db()
        return Response(
            StudentEnrollmentSerializer(enrollment, context={"lessons": ordered_lessons(course)}).data
        )


class CourseSectionViewSet(
    BoardMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CourseSectionSerializer
    lookup_value_regex = UUID_LOOKUP
    queryset = CourseSection.objects.all()


class LessonViewSet(
    BoardMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LessonSerializer
    lookup_value_regex = UUID_LOOKUP

    def get_queryset(self):
        return Lesson.objects.prefetch_related("attachments", "questions__options")


class LessonAttachmentViewSet(
    BoardMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LessonAttachmentSerializer
    lookup_value_regex = UUID_LOOKUP
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = LessonAttachment.objects.all()


class ContentImageUploadView(BoardMixin, APIView):
    """Upload de imagem inline do editor de conteúdo. Retorna a URL pública."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("image")
        if not upload:
            raise ValidationError({"image": "Envie uma imagem."})
        ext = os.path.splitext(upload.name)[1].lower().lstrip(".")
        if ext not in IMAGE_EXTENSIONS:
            raise ValidationError({"image": "Formato de imagem não suportado."})
        if upload.size > MAX_IMAGE_BYTES:
            raise ValidationError({"image": "Imagem maior que 5 MB."})
        path = default_storage.save(f"courses/content/{uuid.uuid4().hex}.{ext}", upload)
        return Response(
            {"url": request.build_absolute_uri(default_storage.url(path))},
            status=status.HTTP_201_CREATED,
        )


class InstructorQuestionViewSet(
    BoardMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Caixa de perguntas dos alunos para a diretoria / instrutores."""

    serializer_class = LessonQuestionSerializer
    lookup_value_regex = UUID_LOOKUP
    pagination_class = None
    LIST_LIMIT = 200

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()[: self.LIST_LIMIT]
        return Response(self.get_serializer(qs, many=True).data)

    def get_queryset(self):
        qs = LessonQuestion.objects.select_related(
            "membro", "lesson__section__course"
        ).prefetch_related("replies__author__membro_perfil")
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(lesson__section__course_id=course_id)
        answered = self.request.query_params.get("answered")
        if answered in ("true", "false"):
            qs = qs.filter(is_answered=answered == "true")
        return qs.order_by("is_answered", "-created_at")

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, pk=None):
        question = self.get_object()
        body = (request.data.get("body") or "").strip()
        if not body:
            raise ValidationError({"body": "Escreva a resposta."})
        LessonQuestionReply.objects.create(
            question=question, author=request.user, is_instructor=True, body=body
        )
        question.is_answered = True
        question.save(update_fields=["is_answered"])
        return Response(self.get_serializer(self.get_queryset().get(pk=question.pk)).data)


# ---------------------------------------------------------------- Portal do associado


class MyCoursesViewSet(viewsets.GenericViewSet):
    """
    GET  my/                                   cursos matriculados
    GET  my/{id}/                              estrutura + progresso
    GET  my/{id}/lessons/{lesson}/             conteúdo da aula
    POST my/{id}/lessons/{lesson}/complete/    concluir aula (texto/vídeo)
    POST my/{id}/lessons/{lesson}/quiz/        enviar respostas do quiz
    GET/POST my/{id}/lessons/{lesson}/questions/
    POST my/{id}/questions/{question}/replies/
    GET  my/{id}/certificate/                  PDF
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PortalEnrollmentSerializer
    lookup_value_regex = UUID_LOOKUP

    def get_membro(self):
        membro = resolver_membro_do_user(self.request.user, auto_link=True)
        if not membro:
            raise NotFound("Perfil de associado não encontrado.")
        return membro

    def get_queryset(self):
        return (
            CourseEnrollment.objects.filter(membro=self.get_membro())
            .exclude(status=CourseEnrollment.REVOKED)
            .exclude(course__status=Course.DRAFT)
            .select_related("course", "membro")
            .order_by("-last_accessed_at", "-enrolled_at")
        )

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        enrollment = self.get_object()
        serializer = self.get_serializer(
            enrollment, context={"request": request, "include_outline": True}
        )
        return Response(serializer.data)

    def _enrollment_and_lesson(self, pk, lesson_id, require_unlocked=True):
        enrollment = self.get_object()
        if not enrollment_has_access(enrollment):
            raise PermissionDenied("Sem acesso a este curso.")
        lesson = (
            Lesson.objects.filter(pk=lesson_id, section__course=enrollment.course)
            .prefetch_related("attachments", "questions__options")
            .first()
        )
        if not lesson:
            raise NotFound("Aula não encontrada.")
        if require_unlocked and lesson.id not in unlocked_lesson_ids(enrollment):
            raise PermissionDenied("Conclua as aulas anteriores para liberar esta.")
        return enrollment, lesson

    def _neighbours(self, enrollment, lesson):
        ids = [item.id for item in ordered_lessons(enrollment.course)]
        index = ids.index(lesson.id)
        prev_id = ids[index - 1] if index > 0 else None
        next_id = ids[index + 1] if index + 1 < len(ids) else None
        return (str(prev_id) if prev_id else None, str(next_id) if next_id else None)

    def _lesson_response(self, request, enrollment, lesson):
        payload = portal_lesson_payload(lesson, request)
        payload["completed"] = lesson.id in completed_lesson_ids(enrollment)
        payload["previous_lesson_id"], payload["next_lesson_id"] = self._neighbours(enrollment, lesson)
        if lesson.lesson_type == Lesson.QUIZ:
            attempt = enrollment.quiz_attempts.filter(lesson=lesson).first()
            payload["last_attempt"] = None
            if attempt:
                graded = grade_quiz(lesson, attempt.answers)
                payload["last_attempt"] = {
                    "id": str(attempt.id),
                    "created_at": attempt.created_at,
                    "score_percent": attempt.score_percent,
                    "correct_count": attempt.correct_count,
                    "total_count": attempt.total_count,
                    "results": graded["results"],
                }
        return payload

    def _with_enrollment(self, request, enrollment, lesson, status_code=status.HTTP_200_OK):
        enrollment.refresh_from_db()
        return Response(
            {
                "lesson": self._lesson_response(request, enrollment, lesson),
                "enrollment": self.get_serializer(
                    enrollment, context={"request": request, "include_outline": True}
                ).data,
            },
            status=status_code,
        )

    @action(detail=True, methods=["get"], url_path=rf"lessons/(?P<lesson_id>{UUID_LOOKUP})")
    def lesson(self, request, pk=None, lesson_id=None):
        enrollment, lesson = self._enrollment_and_lesson(pk, lesson_id)
        touch_last_lesson(enrollment, lesson)
        return Response(self._lesson_response(request, enrollment, lesson))

    @action(
        detail=True,
        methods=["post"],
        url_path=rf"lessons/(?P<lesson_id>{UUID_LOOKUP})/complete",
    )
    def complete(self, request, pk=None, lesson_id=None):
        enrollment, lesson = self._enrollment_and_lesson(pk, lesson_id)
        if lesson.lesson_type == Lesson.QUIZ:
            raise ValidationError({"detail": "Envie as respostas do quiz para concluir."})
        mark_lesson_complete(enrollment, lesson)
        return self._with_enrollment(request, enrollment, lesson)

    @action(
        detail=True,
        methods=["post"],
        url_path=rf"lessons/(?P<lesson_id>{UUID_LOOKUP})/quiz",
    )
    def quiz(self, request, pk=None, lesson_id=None):
        enrollment, lesson = self._enrollment_and_lesson(pk, lesson_id)
        if lesson.lesson_type != Lesson.QUIZ:
            raise ValidationError({"detail": "Esta aula não é um quiz."})
        if not lesson.questions.exists():
            raise ValidationError({"detail": "Este quiz ainda não tem questões."})
        submit_quiz(enrollment, lesson, request.data.get("answers") or {})
        return self._with_enrollment(request, enrollment, lesson, status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path=rf"lessons/(?P<lesson_id>{UUID_LOOKUP})/questions",
    )
    def questions(self, request, pk=None, lesson_id=None):
        enrollment, lesson = self._enrollment_and_lesson(pk, lesson_id, require_unlocked=False)
        context = {"request": request, "membro": enrollment.membro}
        if request.method == "POST":
            body = (request.data.get("body") or "").strip()
            if not body:
                raise ValidationError({"body": "Escreva sua pergunta."})
            question = LessonQuestion.objects.create(lesson=lesson, membro=enrollment.membro, body=body)
            return Response(
                LessonQuestionSerializer(question, context=context).data,
                status=status.HTTP_201_CREATED,
            )
        qs = (
            lesson.student_questions.select_related("membro", "lesson__section__course")
            .prefetch_related("replies__author__membro_perfil")
            .order_by("-created_at")
        )
        return Response(LessonQuestionSerializer(qs, many=True, context=context).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=rf"questions/(?P<question_id>{UUID_LOOKUP})/replies",
    )
    def reply(self, request, pk=None, question_id=None):
        enrollment = self.get_object()
        if not enrollment_has_access(enrollment):
            raise PermissionDenied("Sem acesso a este curso.")
        question = get_object_or_404(
            LessonQuestion.objects.select_related("membro", "lesson__section__course"),
            pk=question_id,
            lesson__section__course=enrollment.course,
        )
        body = (request.data.get("body") or "").strip()
        if not body:
            raise ValidationError({"body": "Escreva a resposta."})
        LessonQuestionReply.objects.create(question=question, author=request.user, body=body)
        question = (
            LessonQuestion.objects.prefetch_related("replies__author__membro_perfil")
            .select_related("membro", "lesson__section__course")
            .get(pk=question.pk)
        )
        return Response(
            LessonQuestionSerializer(
                question, context={"request": request, "membro": enrollment.membro}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="certificate")
    def certificate(self, request, pk=None):
        enrollment = self.get_object()
        if not (
            enrollment.course.certificate_enabled
            and enrollment.status == CourseEnrollment.COMPLETED
            and enrollment.certificate_code
        ):
            raise NotFound("Certificado indisponível.")
        pdf = build_enrollment_certificate(enrollment, _tenant_name(request))
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="certificado-{enrollment.course.slug}.pdf"'
        )
        return response


# ---------------------------------------------------------------- Rotas públicas


def _tenant_schema(request) -> str:
    tenant = resolve_tenant_from_request(request)
    if not tenant:
        raise NotFound("Associação não encontrada. Informe ?schema=.")
    return tenant.schema_name


def _public_courses():
    return Course.objects.filter(status=Course.PUBLISHED).select_related("catalog_item")


class PublicCourseListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        with schema_context(_tenant_schema(request)):
            qs = _public_courses().filter(visibility=Course.PUBLIC).order_by("-created_at")
            return Response(PublicCourseSerializer(qs, many=True, context={"request": request}).data)


class PublicCourseDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        with schema_context(_tenant_schema(request)):
            course = _public_courses().filter(slug=slug).first()
            if not course:
                raise NotFound("Curso não encontrado.")
            return Response(PublicCourseDetailSerializer(course, context={"request": request}).data)


class PublicLessonPreviewView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, lesson_id):
        with schema_context(_tenant_schema(request)):
            lesson = (
                Lesson.objects.filter(
                    pk=lesson_id,
                    section__course__slug=slug,
                    section__course__status=Course.PUBLISHED,
                    is_preview=True,
                )
                .exclude(lesson_type=Lesson.QUIZ)
                .prefetch_related("attachments")
                .first()
            )
            if not lesson:
                raise NotFound("Aula de amostra não encontrada.")
            return Response(portal_lesson_payload(lesson, request, include_quiz=False))


class PublicCertificateVerifyView(APIView):
    """Validação pública de certificado pelo código impresso no PDF."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, code):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        with schema_context(tenant.schema_name):
            enrollment = (
                CourseEnrollment.objects.filter(
                    certificate_code=code.strip().upper(),
                    status=CourseEnrollment.COMPLETED,
                )
                .select_related("course", "membro")
                .first()
            )
            if not enrollment:
                raise NotFound("Certificado não encontrado.")
            completed = timezone.localtime(enrollment.completed_at) if enrollment.completed_at else None
            return Response(
                {
                    "valid": True,
                    "code": enrollment.certificate_code,
                    "participant_name": enrollment.membro.nome_completo,
                    "course_title": enrollment.course.title,
                    "workload_hours": enrollment.course.workload_hours,
                    "completed_at": completed.date().isoformat() if completed else None,
                    "issuer": tenant.name,
                }
            )
