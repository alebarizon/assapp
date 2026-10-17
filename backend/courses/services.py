"""
Regras do módulo Cursos: ordem das aulas, desbloqueio, progresso, matrícula, quiz, certificado.
"""
import re
import secrets

from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    Course,
    CourseEnrollment,
    CourseSection,
    Lesson,
    LessonProgress,
    QuizAttempt,
    QuizQuestion,
)

ACCESS_STATUSES = (CourseEnrollment.ACTIVE, CourseEnrollment.COMPLETED)

_YOUTUBE_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?(?:.*&)?v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtu\.be/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com/(?:embed|shorts|live)/)([A-Za-z0-9_-]{11})"),
]


def youtube_video_id(url: str | None) -> str | None:
    if not url:
        return None
    for pattern in _YOUTUBE_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def prefetch_course_tree(qs):
    return qs.prefetch_related(
        Prefetch(
            "sections",
            queryset=CourseSection.objects.order_by("position", "created_at").prefetch_related(
                Prefetch(
                    "lessons",
                    queryset=Lesson.objects.order_by("position", "created_at").prefetch_related(
                        "attachments",
                        Prefetch(
                            "questions",
                            queryset=QuizQuestion.objects.order_by("position", "id").prefetch_related(
                                "options"
                            ),
                        ),
                    ),
                )
            ),
        )
    )


def ordered_lessons(course: Course) -> list[Lesson]:
    """Aulas na ordem de exibição (seção.position, lesson.position)."""
    return list(
        Lesson.objects.filter(section__course=course)
        .select_related("section")
        .order_by("section__position", "section__created_at", "position", "created_at")
    )


def completed_lesson_ids(enrollment: CourseEnrollment) -> set:
    return set(enrollment.lesson_progress.values_list("lesson_id", flat=True))


def unlocked_lesson_ids(enrollment: CourseEnrollment, lessons=None, completed=None) -> set:
    """Livre: todas. Sequencial: até a primeira aula ainda não concluída (inclusive)."""
    lessons = lessons if lessons is not None else ordered_lessons(enrollment.course)
    if enrollment.course.progression_mode == Course.FREE:
        return {lesson.id for lesson in lessons}
    completed = completed if completed is not None else completed_lesson_ids(enrollment)
    unlocked = set()
    for lesson in lessons:
        unlocked.add(lesson.id)
        if lesson.id not in completed:
            break
    return unlocked


def progress_summary(enrollment: CourseEnrollment, lessons=None, completed=None) -> dict:
    lessons = lessons if lessons is not None else ordered_lessons(enrollment.course)
    completed = completed if completed is not None else completed_lesson_ids(enrollment)
    total = len(lessons)
    done = len([lesson for lesson in lessons if lesson.id in completed])
    next_lesson = next((lesson for lesson in lessons if lesson.id not in completed), None)
    return {
        "total_lessons": total,
        "completed_lessons": done,
        "percent_complete": int(round(done * 100 / total)) if total else 0,
        "next_lesson_id": str(next_lesson.id) if next_lesson else None,
        "next_lesson_title": next_lesson.title if next_lesson else None,
    }


def enrollment_has_access(enrollment: CourseEnrollment) -> bool:
    return (
        enrollment.status in ACCESS_STATUSES
        and enrollment.course.status in (Course.PUBLISHED, Course.ARCHIVED)
    )


def mark_lesson_complete(enrollment: CourseEnrollment, lesson: Lesson) -> bool:
    """Registra conclusão e fecha o curso se todas as aulas estiverem concluídas."""
    _, created = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    refresh_completion(enrollment)
    return created


def refresh_completion(enrollment: CourseEnrollment):
    if enrollment.status != CourseEnrollment.ACTIVE:
        return
    summary = progress_summary(enrollment)
    if summary["total_lessons"] and summary["completed_lessons"] >= summary["total_lessons"]:
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.completed_at = timezone.now()
        if enrollment.course.certificate_enabled and not enrollment.certificate_code:
            enrollment.certificate_code = secrets.token_hex(5).upper()
        enrollment.save(update_fields=["status", "completed_at", "certificate_code"])


def grade_quiz(lesson: Lesson, answers: dict) -> dict:
    """
    answers = {question_id: [option_id, ...]}.
    Questão correta quando o conjunto marcado é exatamente o conjunto correto.
    """
    answers = answers if isinstance(answers, dict) else {}
    results = []
    correct_count = 0
    questions = list(lesson.questions.prefetch_related("options").order_by("position", "id"))
    for question in questions:
        raw = answers.get(str(question.id)) or []
        if not isinstance(raw, list):
            raw = [raw]
        option_ids = {str(o.id) for o in question.options.all()}
        selected = {str(v) for v in raw if str(v) in option_ids}
        correct = {str(o.id) for o in question.options.all() if o.is_correct}
        is_correct = bool(correct) and selected == correct
        if is_correct:
            correct_count += 1
        results.append(
            {
                "question_id": str(question.id),
                "selected_option_ids": sorted(selected),
                "correct_option_ids": sorted(correct),
                "is_correct": is_correct,
                "explanation": question.explanation,
            }
        )
    total = len(questions)
    return {
        "answers": {r["question_id"]: r["selected_option_ids"] for r in results},
        "results": results,
        "correct_count": correct_count,
        "total_count": total,
        "score_percent": int(round(correct_count * 100 / total)) if total else 0,
    }


def submit_quiz(enrollment: CourseEnrollment, lesson: Lesson, answers: dict) -> tuple[QuizAttempt, dict]:
    graded = grade_quiz(lesson, answers)
    attempt = QuizAttempt.objects.create(
        enrollment=enrollment,
        lesson=lesson,
        answers=graded["answers"],
        correct_count=graded["correct_count"],
        total_count=graded["total_count"],
        score_percent=graded["score_percent"],
    )
    mark_lesson_complete(enrollment, lesson)
    return attempt, graded


def enroll_membro(course: Course, membro, order=None, notify: bool = True) -> tuple[CourseEnrollment | None, str]:
    """Idempotente. reason: created | already_enrolled | reactivated | inactive_course."""
    if course.status != Course.PUBLISHED:
        return None, "inactive_course"
    enrollment = CourseEnrollment.objects.filter(course=course, membro=membro).first()
    if enrollment:
        if enrollment.status == CourseEnrollment.REVOKED:
            enrollment.status = CourseEnrollment.ACTIVE
            enrollment.order = order or enrollment.order
            enrollment.save(update_fields=["status", "order"])
            refresh_completion(enrollment)
            if notify:
                _notify_enrollment(enrollment)
            return enrollment, "reactivated"
        return enrollment, "already_enrolled"
    enrollment = CourseEnrollment.objects.create(course=course, membro=membro, order=order)
    if notify:
        _notify_enrollment(enrollment)
    return enrollment, "created"


def _notify_enrollment(enrollment: CourseEnrollment):
    """E-mail de boas-vindas ao curso, enviado só após o commit da matrícula."""
    from django.db import transaction

    from core.emails import enviar_email, frontend_url, nome_associacao

    email = enrollment.membro.email
    if not email:
        return
    course = enrollment.course
    associacao = nome_associacao()
    texto = (
        f"Olá, {enrollment.membro.nome_completo}!\n\n"
        f"Sua matrícula no curso {course.title} está ativa. "
        f"Acesse pelo portal do associado de {associacao}, em “Meus cursos”."
    )
    if course.workload_hours:
        texto += f"\n\nCarga horária: {course.workload_hours} h."
    link = frontend_url("/app/portal/cursos")
    transaction.on_commit(
        lambda: enviar_email(email, f"Matrícula confirmada — {course.title}", texto, link=link, link_label="Começar o curso")
    )


def enroll_from_catalog_item(membro, catalog_item, order=None) -> list[dict]:
    """Fulfillment do e-commerce: matricula o associado nos cursos ligados ao item comprado."""
    results = []
    for course in Course.objects.filter(catalog_item=catalog_item):
        enrollment, reason = enroll_membro(course, membro, order=order)
        results.append(
            {
                "course_id": str(course.id),
                "enrollment_id": str(enrollment.id) if enrollment else None,
                "reason": reason,
            }
        )
    return results


def membro_already_has_courses(membro, catalog_item) -> bool:
    """True quando o item tem cursos e o associado já acessa todos eles."""
    course_ids = set(
        Course.objects.filter(catalog_item=catalog_item).values_list("id", flat=True)
    )
    if not course_ids:
        return False
    enrolled = set(
        CourseEnrollment.objects.filter(
            membro=membro, course_id__in=course_ids, status__in=ACCESS_STATUSES
        ).values_list("course_id", flat=True)
    )
    return enrolled == course_ids


def build_enrollment_certificate(enrollment: CourseEnrollment, issuer: str) -> bytes:
    from django.db import connection

    from core.certificates import build_certificate_pdf, certificate_verify_url

    course = enrollment.course
    details = []
    if course.workload_hours:
        details.append(f"Carga horária: {course.workload_hours} h")
    if course.instructor_name:
        details.append(f"Instrutor(a): {course.instructor_name}")
    return build_certificate_pdf(
        participant_name=enrollment.membro.nome_completo,
        title=course.title,
        details=" · ".join(details),
        issued_at=timezone.localtime(enrollment.completed_at or timezone.now()),
        code=enrollment.certificate_code,
        issuer=issuer,
        verify_url=certificate_verify_url(connection.schema_name, enrollment.certificate_code),
    )


def touch_last_lesson(enrollment: CourseEnrollment, lesson: Lesson):
    enrollment.last_lesson = lesson
    enrollment.last_accessed_at = timezone.now()
    enrollment.save(update_fields=["last_lesson", "last_accessed_at"])
