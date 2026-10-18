from django.db import transaction
from rest_framework import serializers

from eventos.serializers import ListaJsonField

from .models import AcessoPublicacao, Publicacao
from .services import publicar, sincronizar_item_loja


def _url(request, arquivo):
    if not arquivo:
        return None
    return request.build_absolute_uri(arquivo.url) if request else arquivo.url


def _preco(item, campo):
    if not item or not item.is_active:
        return None
    valor = getattr(item, campo)
    return f"{valor:.2f}" if valor is not None else None


class PublicacaoBaseSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    acesso_display = serializers.CharField(source="get_acesso_display", read_only=True)
    capa_url = serializers.SerializerMethodField()
    tem_arquivo = serializers.SerializerMethodField()

    class Meta:
        model = Publicacao
        fields = [
            "id", "tipo", "tipo_display", "titulo", "slug", "subtitulo", "resumo", "autores", "palavras_chave",
            "ano", "edicao", "isbn", "issn", "acesso", "acesso_display", "capa_url", "tem_arquivo", "publicado_em",
        ]

    def get_capa_url(self, obj):
        return _url(self.context.get("request"), obj.capa)

    def get_tem_arquivo(self, obj):
        return bool(obj.arquivo)


class PublicacaoSerializer(PublicacaoBaseSerializer):
    """Painel: cadastro completo, com preço na loja."""

    autores = ListaJsonField(required=False)
    palavras_chave = ListaJsonField(required=False)
    capa = serializers.ImageField(required=False, allow_null=True, write_only=True)
    arquivo = serializers.FileField(required=False, allow_null=True, write_only=True)
    remover_capa = serializers.BooleanField(required=False, write_only=True)
    remover_arquivo = serializers.BooleanField(required=False, write_only=True)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0)
    preco_socio = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0
    )
    arquivo_nome = serializers.SerializerMethodField()
    vendas = serializers.SerializerMethodField()

    class Meta(PublicacaoBaseSerializer.Meta):
        fields = PublicacaoBaseSerializer.Meta.fields + [
            "capa", "arquivo", "remover_capa", "remover_arquivo", "arquivo_nome", "publicada", "downloads",
            "preco", "preco_socio", "catalog_item", "vendas", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "publicado_em", "downloads", "catalog_item"]

    def get_arquivo_nome(self, obj):
        return obj.arquivo.name.rsplit("/", 1)[-1] if obj.arquivo else ""

    def get_vendas(self, obj):
        if not obj.catalog_item_id:
            return 0
        return obj.catalog_item.order_items.filter(order__paid_at__isnull=False).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["preco"] = _preco(instance.catalog_item, "price")
        data["preco_socio"] = _preco(instance.catalog_item, "member_price")
        return data

    def to_internal_value(self, data):
        if data.get("ano") == "":
            data = data.copy()
            data["ano"] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        acesso = attrs.get("acesso", getattr(self.instance, "acesso", AcessoPublicacao.ASSOCIADOS))
        item = getattr(self.instance, "catalog_item", None)
        preco = attrs.get("preco", item.price if item and item.is_active else None)
        preco_socio = attrs.get("preco_socio", item.member_price if item and item.is_active else None)
        if acesso == AcessoPublicacao.VENDA and preco is None:
            raise serializers.ValidationError({"preco": "Informe o preço para vender na loja."})
        if preco is not None and preco_socio is not None and preco_socio > preco:
            raise serializers.ValidationError({"preco_socio": "Preço de sócio não pode ser maior que o preço cheio."})
        attrs["_preco"] = (preco, preco_socio)
        return attrs

    @transaction.atomic
    def _salvar(self, instance, attrs):
        preco, preco_socio = attrs.pop("_preco")
        attrs.pop("preco", None)
        attrs.pop("preco_socio", None)
        publicada = attrs.pop("publicada", instance.publicada if instance.pk else False)
        if attrs.pop("remover_capa", False):
            instance.capa = None
        if attrs.pop("remover_arquivo", False):
            instance.arquivo = None
        for campo, valor in attrs.items():
            setattr(instance, campo, valor)
        instance.save()
        publicar(instance, publicada)
        sincronizar_item_loja(instance, preco, preco_socio, self.context["request"].user)
        return instance

    def create(self, validated_data):
        return self._salvar(Publicacao(created_by=self.context["request"].user), validated_data)

    def update(self, instance, validated_data):
        return self._salvar(instance, validated_data)


class PublicacaoPublicaSerializer(PublicacaoBaseSerializer):
    preco = serializers.SerializerMethodField()
    preco_socio = serializers.SerializerMethodField()

    class Meta(PublicacaoBaseSerializer.Meta):
        fields = PublicacaoBaseSerializer.Meta.fields + ["preco", "preco_socio"]

    def get_preco(self, obj):
        return _preco(obj.catalog_item, "price")

    def get_preco_socio(self, obj):
        return _preco(obj.catalog_item, "member_price")
