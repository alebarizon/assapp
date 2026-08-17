"""Serializers — website tenant."""
from rest_framework import serializers

from .models import SitePage, WebsiteConfig


class WebsiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteConfig
        fields = [
            "id",
            "site_title",
            "site_tagline",
            "site_description",
            "primary_color",
            "secondary_color",
            "logo_url",
            "favicon_url",
            "hero_title",
            "hero_subtitle",
            "hero_image_url",
            "hero_cta_label",
            "hero_cta_link",
            "about_title",
            "about_text",
            "associe_se_title",
            "associe_se_lead",
            "associe_se_categories",
            "associe_se_cta_label",
            "associe_se_cta_link",
            "contact_email",
            "contact_phone",
            "contact_address",
            "social_links",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SitePageSerializer(serializers.ModelSerializer):
    page_type_display = serializers.CharField(source="get_page_type_display", read_only=True)

    class Meta:
        model = SitePage
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "page_type",
            "page_type_display",
            "is_published",
            "is_featured",
            "published_at",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class PublicSitePayloadSerializer(serializers.Serializer):
    config = WebsiteConfigSerializer()
    news = SitePageSerializer(many=True)
    diretoria = serializers.DictField(required=False)
