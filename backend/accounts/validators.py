"""Validadores de signup / tenant."""
import re

from django.core.exceptions import ValidationError

RESERVED_SLUGS = frozenset(
    {
        "sistema",
        "public",
        "www",
        "api",
        "admin",
        "app",
        "static",
        "media",
        "health",
        "login",
        "signup",
        "register",
    }
)

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{2,31}$")


def validate_tenant_slug(value: str) -> str:
    slug = (value or "").strip().lower()
    if not _SLUG_RE.match(slug):
        raise ValidationError(
            "Slug inválido: use 3–32 caracteres, começando com letra "
            "(apenas a-z, 0-9 e hífen)."
        )
    if slug in RESERVED_SLUGS:
        raise ValidationError(f"O slug '{slug}' é reservado. Escolha outro.")
    if "--" in slug or slug.endswith("-"):
        raise ValidationError("Slug não pode terminar com hífen nem ter hífens duplos.")
    return slug
