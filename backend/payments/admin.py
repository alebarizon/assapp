from django.contrib import admin

from .models import Cobranca, ConfiguracaoPagamento


@admin.register(ConfiguracaoPagamento)
class ConfiguracaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ("provedor", "ativo", "sandbox", "updated_at")
    exclude = ("api_key_cifrada", "webhook_token")


@admin.register(Cobranca)
class CobrancaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "membro", "metodo", "provedor", "status", "valor", "created_at")
    list_filter = ("status", "metodo", "provedor")
    search_fields = ("descricao", "membro__nome_completo", "external_id")
