from django.contrib import admin

from .models import SitePage, WebsiteConfig


@admin.register(WebsiteConfig)
class WebsiteConfigAdmin(admin.ModelAdmin):
    list_display = ("site_title", "is_published", "updated_at")


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    list_display = ("title", "page_type", "is_published", "is_featured", "published_at")
    list_filter = ("page_type", "is_published")
    prepopulated_fields = {"slug": ("title",)}
