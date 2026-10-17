from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    ContentImageUploadView,
    CourseSectionViewSet,
    CourseViewSet,
    InstructorQuestionViewSet,
    LessonAttachmentViewSet,
    LessonViewSet,
    MyCoursesViewSet,
    PublicCertificateVerifyView,
    PublicCourseDetailView,
    PublicCourseListView,
    PublicLessonPreviewView,
)

app_name = "courses"

# SimpleRouter: o DefaultRouter registraria a API root em "" e esconderia a lista de cursos.
router = SimpleRouter()
router.register(r"sections", CourseSectionViewSet, basename="course-section")
router.register(r"lessons", LessonViewSet, basename="course-lesson")
router.register(r"attachments", LessonAttachmentViewSet, basename="course-attachment")
router.register(r"questions", InstructorQuestionViewSet, basename="course-question")
router.register(r"my", MyCoursesViewSet, basename="my-course")
router.register(r"", CourseViewSet, basename="course")

urlpatterns = [
    path("public/", PublicCourseListView.as_view(), name="public-courses"),
    path(
        "public/certificates/<str:code>/",
        PublicCertificateVerifyView.as_view(),
        name="public-certificate",
    ),
    path("public/<slug:slug>/", PublicCourseDetailView.as_view(), name="public-course-detail"),
    path(
        "public/<slug:slug>/lessons/<uuid:lesson_id>/",
        PublicLessonPreviewView.as_view(),
        name="public-course-lesson",
    ),
    path("uploads/image/", ContentImageUploadView.as_view(), name="course-image-upload"),
    path("", include(router.urls)),
]
