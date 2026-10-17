"""Testes do módulo Cursos."""
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from courses.html_sanitizer import sanitize_html
from courses.models import (
    Course,
    CourseEnrollment,
    CourseSection,
    Lesson,
    LessonQuestion,
    QuizOption,
    QuizQuestion,
)
from courses.services import youtube_video_id
from courses.views import (
    CourseViewSet,
    InstructorQuestionViewSet,
    LessonViewSet,
    MyCoursesViewSet,
    PublicCertificateVerifyView,
    PublicCourseDetailView,
    PublicCourseListView,
    PublicLessonPreviewView,
)

factory = APIRequestFactory()


def _call(viewset_cls, actions, user, method, data=None, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return viewset_cls.as_view(actions)(request, **kwargs)


@pytest.fixture
def course(test_tenant, board_user):
    from ecommerce.models import CatalogItem, CatalogItemType

    with schema_context(test_tenant.schema_name):
        item = CatalogItem.objects.create(
            name="Curso Base", item_type=CatalogItemType.CURSO, price=Decimal("97.00")
        )
        course = Course.objects.create(
            title="Metodologia Científica",
            status=Course.PUBLISHED,
            catalog_item=item,
            workload_hours=8,
            created_by=board_user,
        )
        s1 = CourseSection.objects.create(course=course, title="Intro", position=1)
        s2 = CourseSection.objects.create(course=course, title="Prática", position=2)
        l1 = Lesson.objects.create(section=s1, title="Boas-vindas", lesson_type=Lesson.TEXT, content="<p>Oi</p>", position=1, is_preview=True)
        l2 = Lesson.objects.create(section=s1, title="Vídeo", lesson_type=Lesson.VIDEO, video_url="https://youtu.be/dQw4w9WgXcQ", position=2)
        l3 = Lesson.objects.create(section=s2, title="Quiz", lesson_type=Lesson.QUIZ, position=1)
        q = QuizQuestion.objects.create(lesson=l3, prompt="2+2?", question_type=QuizQuestion.SINGLE, position=1)
        right = QuizOption.objects.create(question=q, text="4", is_correct=True, position=1)
        wrong = QuizOption.objects.create(question=q, text="5", is_correct=False, position=2)
    return {"course": course, "item": item, "lessons": [l1, l2, l3], "question": q, "right": right, "wrong": wrong}


class TestHelpers:
    def test_youtube_id_formats(self):
        assert youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10") == "dQw4w9WgXcQ"
        assert youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert youtube_video_id("https://vimeo.com/123") is None

    def test_sanitize_html_strips_scripts_and_handlers(self):
        dirty = '<p onclick="x()">Oi<script>alert(1)</script></p><a href="javascript:alert(1)">x</a><img src="data:image/png;base64,AA">'
        clean = sanitize_html(dirty)
        assert "script" not in clean
        assert "onclick" not in clean
        assert "javascript:" not in clean
        assert "data:" not in clean
        assert clean.startswith("<p>Oi</p>")


@pytest.mark.django_db
class TestBuilder:
    def test_member_cannot_manage_courses(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _call(CourseViewSet, {"post": "create"}, user, "post", {"title": "X"})
            assert resp.status_code == 403

    def test_create_course_section_and_quiz_lesson(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            resp = _call(CourseViewSet, {"post": "create"}, board_user, "post", {"title": "Meu Curso", "description": "<p>ok</p><script>x</script>"})
            assert resp.status_code == 201, resp.data
            course = Course.objects.get(pk=resp.data["id"])
            assert course.slug == "meu-curso"
            assert course.created_by == board_user
            assert "script" not in course.description

            section = CourseSection.objects.create(course=course, title="S1")
            payload = {
                "section": str(section.id),
                "title": "Quiz 1",
                "lesson_type": "quiz",
                "questions": [
                    {"prompt": "Verdade?", "question_type": "true_false", "options": [
                        {"text": "Verdadeiro", "is_correct": True},
                        {"text": "Falso", "is_correct": False},
                    ]},
                ],
            }
            resp = _call(LessonViewSet, {"post": "create"}, board_user, "post", payload)
            assert resp.status_code == 201, resp.data
            lesson = Lesson.objects.get(pk=resp.data["id"])
            assert lesson.questions.first().options.filter(is_correct=True).count() == 1

    def test_video_lesson_requires_youtube_url(self, test_tenant, board_user, course):
        with schema_context(test_tenant.schema_name):
            section = course["course"].sections.first()
            resp = _call(LessonViewSet, {"post": "create"}, board_user, "post", {
                "section": str(section.id), "title": "V", "lesson_type": "video", "video_url": "https://vimeo.com/1",
            })
            assert resp.status_code == 400
            assert "video_url" in resp.data

    def test_create_catalog_item_links_course(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            course = Course.objects.create(title="Sem Item")
            resp = _call(CourseViewSet, {"post": "create_catalog_item"}, board_user, "post", {"price": "49.90"}, pk=str(course.id))
            assert resp.status_code == 200, resp.data
            course.refresh_from_db()
            assert course.catalog_item.item_type == "curso"
            assert course.catalog_item.price == Decimal("49.90")

    def test_catalog_item_must_be_course_type(self, test_tenant, board_user):
        from ecommerce.models import CatalogItem, CatalogItemType

        with schema_context(test_tenant.schema_name):
            material = CatalogItem.objects.create(
                name="Livro", item_type=CatalogItemType.MATERIAL, price=Decimal("10"), inventory_count=5
            )
            course = Course.objects.create(title="C")
            resp = _call(CourseViewSet, {"patch": "partial_update"}, board_user, "patch", {"catalog_item": str(material.id)}, pk=str(course.id))
            assert resp.status_code == 400
            assert "catalog_item" in resp.data

    def test_manual_enrollment_by_board(self, test_tenant, board_user, member, course):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            resp = _call(CourseViewSet, {"post": "students"}, board_user, "post", {"membro": str(membro.id)}, pk=str(course["course"].id))
            assert resp.status_code == 201, resp.data
            assert CourseEnrollment.objects.filter(course=course["course"], membro=membro).exists()


@pytest.mark.django_db
class TestEcommerceIntegration:
    def test_checkout_enrolls_member_and_blocks_second_purchase(self, test_tenant, member, course):
        from django.core.exceptions import ValidationError

        from ecommerce.services import create_order_from_cart, get_or_create_cart, validate_cart_item_for_membro
        from ecommerce.models import CartItem

        user, membro = member
        with schema_context(test_tenant.schema_name):
            cart = get_or_create_cart(membro)
            CartItem.objects.create(cart=cart, catalog_item=course["item"], quantity=1)
            order = create_order_from_cart(membro, user=user)
            assert order.status == "fulfilled"
            enrollment = CourseEnrollment.objects.get(course=course["course"], membro=membro)
            assert enrollment.order == order
            ref = order.items.first().fulfillment_ref
            assert ref["type"] == "curso"
            assert ref["enrollments"][0]["reason"] == "created"

            with pytest.raises(ValidationError):
                validate_cart_item_for_membro(course["item"], membro, 1)

    def test_draft_course_is_not_enrolled(self, test_tenant, member, course):
        from courses.services import enroll_from_catalog_item

        _, membro = member
        with schema_context(test_tenant.schema_name):
            Course.objects.filter(pk=course["course"].pk).update(status=Course.DRAFT)
            assert enroll_from_catalog_item(membro, course["item"])[0]["reason"] == "inactive_course"


@pytest.mark.django_db
class TestPortal:
    def test_sequential_progression_quiz_and_certificate(self, test_tenant, member, course):
        user, membro = member
        l1, l2, l3 = course["lessons"]
        with schema_context(test_tenant.schema_name):
            enrollment = CourseEnrollment.objects.create(course=course["course"], membro=membro)
            eid = str(enrollment.id)

            resp = _call(MyCoursesViewSet, {"get": "lesson"}, user, "get", pk=eid, lesson_id=str(l2.id))
            assert resp.status_code == 403

            resp = _call(MyCoursesViewSet, {"post": "complete"}, user, "post", pk=eid, lesson_id=str(l1.id))
            assert resp.status_code == 200, resp.data
            resp = _call(MyCoursesViewSet, {"get": "lesson"}, user, "get", pk=eid, lesson_id=str(l2.id))
            assert resp.status_code == 200
            assert resp.data["youtube_id"] == "dQw4w9WgXcQ"
            _call(MyCoursesViewSet, {"post": "complete"}, user, "post", pk=eid, lesson_id=str(l2.id))

            resp = _call(MyCoursesViewSet, {"get": "lesson"}, user, "get", pk=eid, lesson_id=str(l3.id))
            assert "is_correct" not in str(resp.data["questions"])

            answers = {str(course["question"].id): [str(course["wrong"].id)]}
            resp = _call(MyCoursesViewSet, {"post": "quiz"}, user, "post", {"answers": answers}, pk=eid, lesson_id=str(l3.id))
            assert resp.status_code == 201, resp.data
            assert resp.data["lesson"]["last_attempt"]["score_percent"] == 0
            assert resp.data["enrollment"]["status"] == "completed"
            assert resp.data["enrollment"]["certificate_available"] is True

            resp = _call(MyCoursesViewSet, {"get": "certificate"}, user, "get", pk=eid)
            assert resp.status_code == 200
            assert resp["Content-Type"] == "application/pdf"
            assert resp.content.startswith(b"%PDF")

    def test_free_progression_unlocks_all(self, test_tenant, member, course):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            Course.objects.filter(pk=course["course"].pk).update(progression_mode=Course.FREE)
            enrollment = CourseEnrollment.objects.create(course=course["course"], membro=membro)
            resp = _call(MyCoursesViewSet, {"get": "lesson"}, user, "get", pk=str(enrollment.id), lesson_id=str(course["lessons"][2].id))
            assert resp.status_code == 200

    def test_revoked_enrollment_has_no_access(self, test_tenant, member, course):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            enrollment = CourseEnrollment.objects.create(course=course["course"], membro=membro, status=CourseEnrollment.REVOKED)
            resp = _call(MyCoursesViewSet, {"get": "retrieve"}, user, "get", pk=str(enrollment.id))
            assert resp.status_code == 404

    def test_question_and_instructor_reply(self, test_tenant, board_user, member, course):
        user, membro = member
        l1 = course["lessons"][0]
        with schema_context(test_tenant.schema_name):
            enrollment = CourseEnrollment.objects.create(course=course["course"], membro=membro)
            eid = str(enrollment.id)
            resp = _call(MyCoursesViewSet, {"post": "questions"}, user, "post", {"body": "Dúvida?"}, pk=eid, lesson_id=str(l1.id))
            assert resp.status_code == 201, resp.data
            assert resp.data["author_name"] == "Ana S."
            qid = resp.data["id"]

            resp = _call(InstructorQuestionViewSet, {"get": "list"}, board_user, "get", {"answered": "false"})
            assert [q["id"] for q in resp.data] == [qid]

            resp = _call(InstructorQuestionViewSet, {"post": "reply"}, board_user, "post", {"body": "Resposta"}, pk=qid)
            assert resp.status_code == 200, resp.data
            assert resp.data["is_answered"] is True
            assert resp.data["replies"][0]["is_instructor"] is True
            assert LessonQuestion.objects.get(pk=qid).is_answered


@pytest.mark.django_db
class TestPublic:
    def test_catalog_lists_only_public_published(self, test_tenant, course):
        with schema_context(test_tenant.schema_name):
            Course.objects.create(title="Rascunho")
            Course.objects.create(title="Oculto", status=Course.PUBLISHED, visibility=Course.UNLISTED)
        resp = PublicCourseListView.as_view()(factory.get("/", {"schema": test_tenant.schema_name}))
        assert resp.status_code == 200
        assert [c["title"] for c in resp.data] == ["Metodologia Científica"]
        assert resp.data[0]["catalog_item_info"]["price"] == "97.00"

    def test_detail_outline_and_preview(self, test_tenant, course):
        slug = course["course"].slug
        l1, l2, _ = course["lessons"]
        q = {"schema": test_tenant.schema_name}
        resp = PublicCourseDetailView.as_view()(factory.get("/", q), slug=slug)
        assert resp.status_code == 200
        lessons = resp.data["sections"][0]["lessons"]
        assert "content" not in lessons[0]
        assert lessons[0]["is_preview"] is True

        resp = PublicLessonPreviewView.as_view()(factory.get("/", q), slug=slug, lesson_id=l1.id)
        assert resp.status_code == 200
        assert resp.data["content"] == "<p>Oi</p>"
        resp = PublicLessonPreviewView.as_view()(factory.get("/", q), slug=slug, lesson_id=l2.id)
        assert resp.status_code == 404

    def test_certificate_verification(self, test_tenant, member, course):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            CourseEnrollment.objects.create(
                course=course["course"], membro=membro, status=CourseEnrollment.COMPLETED, certificate_code="ABC123DEF0"
            )
        q = {"schema": test_tenant.schema_name}
        resp = PublicCertificateVerifyView.as_view()(factory.get("/", q), code="abc123def0")
        assert resp.status_code == 200
        assert resp.data["participant_name"] == "Ana Maria Silva"
        assert resp.data["workload_hours"] == 8
        resp = PublicCertificateVerifyView.as_view()(factory.get("/", q), code="NAOEXISTE")
        assert resp.status_code == 404
