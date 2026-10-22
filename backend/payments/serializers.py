from rest_framework import serializers

from .models import Cobranca, ConfiguracaoPagamento
from .services import notificacao_automatica, url_webhook


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
    notificacao_automatica = serializers.SerializerMethodField()

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
            "notificacao_automatica",
            "aceita_pix",
            "aceita_cartao",
            "aceita_boleto",
            "updated_at",
        )
        read_only_fields = ("webhook_token", "updated_at")

    def get_tem_api_key(self, obj) -> bool:
        return bool(obj.api_key)

    def get_api_key_final(self, obj) -> str:
        chave = obj.api_key
        return f"…{chave[-4:]}" if chave else ""

    def get_webhook_url(self, obj) -> str:
        return url_webhook(obj)

    def get_notificacao_automatica(self, obj) -> bool:
        return notificacao_automatica()

    def _troca_provedor(self, attrs) -> bool:
        return bool(self.instance) and attrs.get("provedor", self.instance.provedor) != self.instance.provedor

    def validate(self, attrs):
        chave = attrs.get("api_key")
        chave_atual = bool(self.instance and self.instance.api_key) and not self._troca_provedor(attrs)
        tem_chave = bool(chave) or (chave is None and chave_atual)
        if attrs.get("ativo", getattr(self.instance, "ativo", False)) and not tem_chave:
            if self._troca_provedor(attrs):
                raise serializers.ValidationError({"api_key": "Informe a chave de API do novo provedor."})
            raise serializers.ValidationError({"api_key": "Informe a chave de API para ativar."})
        return attrs

    def update(self, instance, validated_data):
        chave = validated_data.pop("api_key", None)
        if self._troca_provedor(validated_data):
            instance.api_key = ""
        if chave:
            instance.api_key = chave.strip()
        return super().update(instance, validated_data)
