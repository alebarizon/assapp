from rest_framework import serializers

from .models import EVENTOS_VALIDOS, EntregaWebhook, WebhookSaida
from .services import UrlBloqueada, validar_url


class WebhookSaidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSaida
        fields = [
            "id", "url", "descricao", "eventos", "segredo", "ativo",
            "falhas_seguidas", "ultima_entrega_em", "created_at",
        ]
        read_only_fields = ["id", "segredo", "falhas_seguidas", "ultima_entrega_em", "created_at"]

    def validate_url(self, valor):
        try:
            validar_url(valor)
        except UrlBloqueada as exc:
            raise serializers.ValidationError(str(exc))
        return valor

    def validate_eventos(self, valor):
        if not isinstance(valor, list) or not valor:
            raise serializers.ValidationError("Escolha ao menos um evento.")
        invalidos = set(valor) - EVENTOS_VALIDOS
        if invalidos:
            raise serializers.ValidationError(f"Eventos desconhecidos: {', '.join(sorted(invalidos))}.")
        return sorted(set(valor))


class EntregaWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntregaWebhook
        fields = [
            "id", "evento", "dados", "status", "tentativas", "proxima_tentativa",
            "resposta_status", "ultimo_erro", "created_at", "entregue_em",
        ]
