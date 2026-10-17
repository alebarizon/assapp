from django.contrib import admin

from .models import AnexoChamado, Chamado, MensagemChamado


class MensagemInline(admin.TabularInline):
    model = MensagemChamado
    extra = 0
    fields = ("autor_nome", "da_equipe", "interna", "texto", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ("id", "assunto", "tenant", "categoria", "prioridade", "status", "ultima_mensagem_em")
    list_filter = ("status", "categoria", "prioridade")
    search_fields = ("assunto", "autor_email", "tenant__name")
    inlines = [MensagemInline]


admin.site.register(AnexoChamado)
