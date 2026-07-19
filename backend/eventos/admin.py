from django.contrib import admin

from .models import (
    AnaisPublicacao,
    CallForPapers,
    EventoAcademico,
    InscricaoEvento,
    Parecer,
    SubmissaoTrabalho,
)


@admin.register(EventoAcademico)
class EventoAcademicoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "data_inicio", "modalidade")
    list_filter = ("status", "modalidade")
    search_fields = ("titulo", "slug")


@admin.register(CallForPapers)
class CallForPapersAdmin(admin.ModelAdmin):
    list_display = ("evento", "data_abertura", "data_fechamento")


@admin.register(SubmissaoTrabalho)
class SubmissaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "cfp", "status", "autor", "submetido_em")
    list_filter = ("status",)


@admin.register(Parecer)
class ParecerAdmin(admin.ModelAdmin):
    list_display = ("submissao", "parecerista", "recomendacao", "concluido")


@admin.register(InscricaoEvento)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "evento", "confirmada", "created_at")


@admin.register(AnaisPublicacao)
class AnaisAdmin(admin.ModelAdmin):
    list_display = ("titulo", "evento", "publicado_em")
