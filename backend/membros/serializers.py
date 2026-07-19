"""Serializers — Membros, Filiação e Anuidades."""
from rest_framework import serializers

from .models import Anuidade, Filiacao, Membro


class AnuidadeSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    membro_nome = serializers.CharField(source="filiacao.membro.nome_completo", read_only=True)

    class Meta:
        model = Anuidade
        fields = (
            "id",
            "filiacao",
            "membro_nome",
            "ano_referencia",
            "valor",
            "vencimento",
            "status",
            "status_display",
            "pago_em",
            "nf_numero",
            "stripe_payment_id",
        )
        read_only_fields = ("pago_em", "stripe_payment_id")


class FiliacaoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    anuidades = AnuidadeSerializer(many=True, read_only=True)

    class Meta:
        model = Filiacao
        fields = (
            "id",
            "membro",
            "membro_nome",
            "mandato",
            "tipo",
            "tipo_display",
            "status",
            "status_display",
            "data_inicio",
            "data_fim",
            "observacoes",
            "anuidades",
        )


class MembroListSerializer(serializers.ModelSerializer):
    filiacao_status = serializers.SerializerMethodField()
    filiacao_tipo = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)

    class Meta:
        model = Membro
        fields = (
            "id",
            "nome_completo",
            "email",
            "cpf",
            "instituicao",
            "area_atuacao",
            "ativo",
            "consentimento_lgpd",
            "filiacao_status",
            "filiacao_tipo",
            "user",
            "user_email",
            "created_at",
        )
        read_only_fields = ("user", "user_email")

    def get_filiacao_status(self, obj):
        f = obj.filiacao_ativa
        return f.get_status_display() if f else None

    def get_filiacao_tipo(self, obj):
        f = obj.filiacao_ativa
        return f.get_tipo_display() if f else None


class MembroDetailSerializer(MembroListSerializer):
    filiacoes = FiliacaoSerializer(many=True, read_only=True)

    class Meta(MembroListSerializer.Meta):
        fields = MembroListSerializer.Meta.fields + (
            "telefone",
            "cnpj",
            "lattes_url",
            "orcid",
            "consentimento_em",
            "filiacoes",
            "updated_at",
        )


class MembroCreateSerializer(serializers.ModelSerializer):
    tipo_filiacao = serializers.ChoiceField(
        choices=["efetivo", "estudante", "honorario", "institucional"],
        default="efetivo",
        write_only=True,
    )

    class Meta:
        model = Membro
        fields = (
            "nome_completo",
            "email",
            "cpf",
            "cnpj",
            "telefone",
            "instituicao",
            "area_atuacao",
            "lattes_url",
            "orcid",
            "consentimento_lgpd",
            "tipo_filiacao",
        )

    def validate_consentimento_lgpd(self, value):
        if not value:
            raise serializers.ValidationError(
                "Consentimento LGPD é obrigatório para cadastro de membros."
            )
        return value


class GerarAnuidadesSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2020, max_value=2100)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    vencimento = serializers.DateField(required=False)


class RegistrarPagamentoSerializer(serializers.Serializer):
    nf_numero = serializers.CharField(required=False, allow_blank=True)


class VincularUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("email"):
            raise serializers.ValidationError("Informe user_id ou email.")
        return attrs
