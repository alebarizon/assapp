from django.contrib import admin

from .models import Anuidade, Filiacao, Membro


class FiliacaoInline(admin.TabularInline):
    model = Filiacao
    extra = 0


class AnuidadeInline(admin.TabularInline):
    model = Anuidade
    extra = 0


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "email", "instituicao", "ativo", "consentimento_lgpd")
    search_fields = ("nome_completo", "email", "cpf")
    list_filter = ("ativo", "consentimento_lgpd")
    inlines = [FiliacaoInline]


@admin.register(Filiacao)
class FiliacaoAdmin(admin.ModelAdmin):
    list_display = ("membro", "tipo", "status", "data_inicio", "data_fim")
    list_filter = ("status", "tipo")
    inlines = [AnuidadeInline]


@admin.register(Anuidade)
class AnuidadeAdmin(admin.ModelAdmin):
    list_display = ("filiacao", "ano_referencia", "valor", "vencimento", "status")
    list_filter = ("status", "ano_referencia")
