from django.contrib import admin

from .models import Contato, Etiqueta, Nota


class NotaInline(admin.TabularInline):
    model = Nota
    extra = 0


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "etapa", "origem", "created_at")
    list_filter = ("etapa", "origem", "assunto")
    search_fields = ("nome", "email", "instituicao")
    inlines = [NotaInline]


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor")
