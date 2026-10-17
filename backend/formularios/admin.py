from django.contrib import admin

from .models import Formulario, ItemResposta, Pergunta, Resposta, Secao


class SecaoInline(admin.TabularInline):
    model = Secao
    extra = 0


@admin.register(Formulario)
class FormularioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "link_publico_ativo", "disponivel_no_portal", "created_at")
    list_filter = ("status",)
    search_fields = ("titulo",)
    inlines = [SecaoInline]


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ("texto", "tipo", "obrigatoria", "secao")
    list_filter = ("tipo",)


class ItemRespostaInline(admin.TabularInline):
    model = ItemResposta
    extra = 0


@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display = ("formulario", "nome", "email", "origem", "status", "enviada_em")
    list_filter = ("status", "origem")
    inlines = [ItemRespostaInline]
