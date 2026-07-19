from django.contrib import admin

from .models import ContextoHistorico, TimelineInstitucional


@admin.register(ContextoHistorico)
class ContextoHistoricoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "mandato", "autor", "arquivado", "created_at")
    list_filter = ("tipo", "arquivado", "visivel_diretoria")
    search_fields = ("titulo", "decisao", "motivo", "conteudo")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TimelineInstitucional)
class TimelineInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "mandato", "data_evento")
    list_filter = ("tipo", "mandato")
    ordering = ("-data_evento",)
