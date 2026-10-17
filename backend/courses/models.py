"""
Cursos da associação: curso → seções → aulas (texto, vídeo YouTube, quiz), anexos,
matrícula do associado via pedido pago no e-commerce, progresso, quiz, perguntas e certificado.

Adaptado do módulo Cursos do WellSaaS.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    STATUS_CHOICES = [
        (DRAFT, "Rascunho"),
        (PUBLISHED, "Publicado"),
        (ARCHIVED, "Arquivado"),
    ]

    PUBLIC = "public"
    UNLISTED = "unlisted"
    VISIBILITY_CHOICES = [
        (PUBLIC, "Público (catálogo)"),
        (UNLISTED, "Não listado (somente link)"),
    ]

    SEQUENTIAL = "sequential"
    FREE = "free"
    PROGRESSION_CHOICES = [
        (SEQUENTIAL, "Sequencial"),
        (FREE, "Navegação livre"),
    ]

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    LEVEL_CHOICES = [
        (BEGINNER, "Iniciante"),
        (INTERMEDIATE, "Intermediário"),
        (ADVANCED, "Avançado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=300, blank=True, default="")
    description = models.TextField(blank=True, default="", help_text="HTML sanitizado")
    cover_image = models.ImageField(upload_to="courses/covers/%Y/%m/%d/", blank=True, null=True)
    instructor_name = models.CharField(max_length=200, blank=True, default="")
    workload_hours = models.PositiveIntegerField(
        null=True, blank=True, help_text="Carga horária impressa no certificado"
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=BEGINNER)
    progression_mode = models.CharField(
        max_length=20, choices=PROGRESSION_CHOICES, default=SEQUENTIAL
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=PUBLIC)
    catalog_item = models.ForeignKey(
        "ecommerce.CatalogItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        help_text="Pedido pago deste item matricula o associado no curso",
    )
    certificate_enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.title)[:200] or "curso"
        slug = base
        n = 2
        while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug


class CourseSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.position}. {self.title}"


class Lesson(models.Model):
    TEXT = "text"
    VIDEO = "video"
    QUIZ = "quiz"
    TYPE_CHOICES = [
        (TEXT, "Texto"),
        (VIDEO, "Vídeo"),
        (QUIZ, "Quiz"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TEXT)
    content = models.TextField(blank=True, default="", help_text="HTML sanitizado")
    video_url = models.URLField(max_length=500, blank=True, default="")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_preview = models.BooleanField(
        default=False, help_text="Aula de amostra visível no site sem matrícula"
    )
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.position}. {self.title} ({self.lesson_type})"


class LessonAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="courses/attachments/%Y/%m/%d/")
    file_type = models.CharField(max_length=20, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(default=0)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]


class QuizQuestion(models.Model):
    SINGLE = "single"
    MULTIPLE = "multiple"
    TRUE_FALSE = "true_false"
    TYPE_CHOICES = [
        (SINGLE, "Escolha única"),
        (MULTIPLE, "Múltipla escolha"),
        (TRUE_FALSE, "Verdadeiro / Falso"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=SINGLE)
    explanation = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["position", "id"]


class QuizOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["position", "id"]


class CourseEnrollment(models.Model):
    ACTIVE = "active"
    COMPLETED = "completed"
    REVOKED = "revoked"
    STATUS_CHOICES = [
        (ACTIVE, "Ativa"),
        (COMPLETED, "Concluída"),
        (REVOKED, "Revogada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    membro = models.ForeignKey(
        "membros.Membro", on_delete=models.CASCADE, related_name="course_enrollments"
    )
    order = models.ForeignKey(
        "ecommerce.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="course_enrollments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE, db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    certificate_code = models.CharField(max_length=20, blank=True, default="", db_index=True)

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(fields=["course", "membro"], name="unique_course_membro")
        ]

    def __str__(self):
        return f"{self.membro_id} → {self.course_id} ({self.status})"


class LessonProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        CourseEnrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson"], name="unique_enrollment_lesson_progress"
            )
        ]


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        CourseEnrollment, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quiz_attempts")
    answers = models.JSONField(default=dict, help_text="{question_id: [option_id, ...]}")
    correct_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    score_percent = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LessonQuestion(models.Model):
    """Pergunta de associado em uma aula; visível a todos os matriculados no curso."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="student_questions")
    membro = models.ForeignKey(
        "membros.Membro", on_delete=models.CASCADE, related_name="lesson_questions"
    )
    body = models.TextField()
    is_answered = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LessonQuestionReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(LessonQuestion, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_question_replies"
    )
    is_instructor = models.BooleanField(default=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
