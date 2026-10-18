from django.db import connection
from rest_framework import serializers

from core.emails import frontend_url

from .models import Cobranca, ConfiguracaoPagamento


class CobrancaSerializer(serializers.ModelSerializer):
    metodo_display = serializers.CharField(source="get_metodo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Cobranca
        fields = (
            "id",
            "anuidade",
            "pedido",
            "descricao",
            "valor",
            "metodo",
            "metodo_display",
            "provedor",
            "status",
            "status_display",
            "url_pagamento",
            "pix_copia_cola",
            "pix_qrcode_base64",
            "vencimento",
            "pago_em",
            "created_at",
        )
        read_only_fields = fields


class CobrarSerializer(serializers.Serializer):
    metodo = serializers.ChoiceField(choices=[m for m, _ in Cobranca.METODO_CHOICES])


class ConfiguracaoPagamentoSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tem_api_key = serializers.SerializerMethodField()
    api_key_final = serializers.SerializerMethodField()
    webhook_url = serializers.SerializerMethodField()

    class Meta:
        model = ConfiguracaoPagamento
        fields = (
            "provedor",
            "ativo",
            "sandbox",
            "api_key",
            "tem_api_key",
            "api_key_final",
            "webhook_url",
            "webhook_token",
            "aceita_pix",
            "aceita_cartao",
            "aceita_boleto",
            "updated_at",
        )
        read_only_fields = ("provedor", "webhook_token", "updated_at")

    def get_tem_api_key(self, obj) -> bool:
        return bool(obj.api_key)

    def get_api_key_final(self, obj) -> str:
        chave = obj.api_key
        return f"…{chave[-4:]}" if chave else ""

    def get_webhook_url(self, obj) -> str:
        return frontend_url(f"/api/pagamentos/webhook/asaas/?schema={connection.schema_name}")

    def validate(self, attrs):
        chave = attrs.get("api_key")
        tem_chave = bool(chave) or (chave is None and bool(self.instance and self.instance.api_key))
        if attrs.get("ativo", getattr(self.instance, "ativo", False)) and not tem_chave:
            raise serializers.ValidationError({"api_key": "Informe a chave de API para ativar."})
        return attrs

    def update(self, instance, validated_data):
        chave = validated_data.pop("api_key", None)
        if chave:
            instance.api_key = chave.strip()
        return super().update(instance, validated_data)
