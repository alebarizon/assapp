from django.contrib import admin

from .models import Conversa, Mensagem


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 0


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ("assunto", "membro", "status", "ultima_mensagem_em")
    list_filter = ("status",)
    search_fields = ("assunto", "membro__nome_completo", "membro__email")
    inlines = [MensagemInline]
