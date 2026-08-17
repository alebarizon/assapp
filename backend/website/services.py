"""Serviços do website tenant."""
from django.utils import timezone

from .models import WebsiteConfig


DEFAULT_ASSOCIE_SE_CATEGORIES = [
    {"label": "Alunos de graduação", "hint": "Anuidade reduzida"},
    {"label": "Alunos de pós-graduação", "hint": "Benefícios em eventos"},
    {"label": "Profissionais de educação", "hint": "Participação em comissões"},
    {"label": "Profissionais de mercado", "hint": "Networking associativo"},
]


def get_or_create_config() -> WebsiteConfig:
    config = WebsiteConfig.objects.first()
    if config:
        return config
    return WebsiteConfig.objects.create(
        site_title="Associação",
        associe_se_categories=DEFAULT_ASSOCIE_SE_CATEGORIES,
        is_published=False,
    )


def seed_default_config(
    *,
    site_title: str = "Associação Demo",
    publish: bool = True,
) -> WebsiteConfig:
    existing = WebsiteConfig.objects.first()
    if existing:
        if publish and not existing.is_published:
            existing.is_published = True
            existing.save(update_fields=["is_published", "updated_at"])
        return existing
    return WebsiteConfig.objects.create(
        site_title=site_title,
        site_tagline="Gestão e memória institucional",
        site_description="Associação científica demo na plataforma Gesttora.",
        hero_title=site_title,
        hero_subtitle="Congregamos pesquisadores e instituições em torno da ciência associativa.",
        hero_cta_label="Saiba mais",
        hero_cta_link="#sobre",
        about_title="A instituição",
        about_text=(
            "Entidade científica sem fins lucrativos. Nossa missão é apoiar a comunidade "
            "associativa com eventos, publicações e governança transparente."
        ),
        associe_se_title="Associe-se",
        associe_se_lead=(
            "Apoie a pesquisa científica e associe-se. A filiação anual oferece descontos "
            "em eventos promovidos pela associação."
        ),
        associe_se_categories=DEFAULT_ASSOCIE_SE_CATEGORIES,
        associe_se_cta_label="Quero me associar",
        associe_se_cta_link="auto:loja",
        contact_email="contato@demo.org",
        contact_address="São Paulo, SP",
        is_published=publish,
    )


def seed_default_pages() -> None:
    from .models import PageType, SitePage

    now = timezone.now()
    pages = [
        {
            "title": "Boas-vindas à nova gestão",
            "slug": "boas-vindas-nova-gestao",
            "summary": "Diretoria publica prioridades do mandato.",
            "content": "Conteúdo demo — substituível pelo painel Website.",
            "page_type": PageType.NOTICIA,
            "is_featured": True,
        },
        {
            "title": "História da associação",
            "slug": "historia",
            "summary": "Trajetória institucional.",
            "content": "Texto institucional demo. Em produção, editável no CMS.",
            "page_type": PageType.INSTITUCIONAL,
            "is_featured": False,
        },
    ]
    for data in pages:
        SitePage.objects.get_or_create(
            slug=data["slug"],
            defaults={
                **data,
                "is_published": True,
                "published_at": now,
            },
        )
