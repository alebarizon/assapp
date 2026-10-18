"""Publicações da associação: dossiês, ebooks, boletins e livros."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class TipoPublicacao(models.TextChoices):
    DOSSIE = "dossie", "Dossiê"
    EBOOK = "ebook", "E-book"
    BOLETIM = "boletim", "Boletim"
    LIVRO = "livro", "Livro"
    RELATORIO = "relatorio", "Relatório técnico"
    OUTRO = "outro", "Outro"


class AcessoPublicacao(models.TextChoices):
    PUBLICO = "publico", "Aberto a todos"
    ASSOCIADOS = "associados", "Associados em dia"
    VENDA = "venda", "Venda na loja"


class Publicacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=TipoPublicacao.choices, default=TipoPublicacao.EBOOK)
    titulo = models.CharField(max_length=300)
    slug = models.SlugField(max_length=200, unique=True)
    subtitulo = models.CharField(max_length=300, blank=True)
    resumo = models.TextField(blank=True)
    autores = models.JSONField(default=list, blank=True, help_text='[{"nome", "instituicao", "orcid"}]')
    palavras_chave = models.JSONField(default=list, blank=True)
    ano = models.PositiveSmallIntegerField(null=True, blank=True)
    edicao = models.CharField(max_length=60, blank=True, help_text="Ex.: v. 3, n. 2 ou 2ª edição")
    isbn = models.CharField(max_length=20, blank=True)
    issn = models.CharField(max_length=12, blank=True)
    capa = models.ImageField(upload_to="publicacoes/capas/%Y/", blank=True, null=True)
    arquivo = models.FileField(upload_to="publicacoes/arquivos/%Y/", blank=True, null=True)
    acesso = models.CharField(
        max_length=20, choices=AcessoPublicacao.choices, default=AcessoPublicacao.ASSOCIADOS, db_index=True
    )
    catalog_item = models.ForeignKey(
        "ecommerce.CatalogItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publicacoes",
        help_text="Item da loja que dá acesso à publicação após o pagamento",
    )
    publicada = models.BooleanField(default=False, db_index=True)
    publicado_em = models.DateTimeField(null=True, blank=True)
    downloads = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Publicação"
        verbose_name_plural = "Publicações"
        ordering = ["-publicado_em", "-created_at"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)[:180] or "publicacao"
            slug, n = base, 1
            while Publicacao.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)
