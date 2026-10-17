from django.contrib import admin

from .models import Course, CourseEnrollment, CourseSection, Lesson


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "visibility", "catalog_item", "created_at")
    list_filter = ("status", "visibility")
    search_fields = ("title", "slug")
    inlines = [CourseSectionInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "lesson_type", "position")
    list_filter = ("lesson_type",)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "membro", "status", "enrolled_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("membro__nome_completo", "membro__email", "certificate_code")
