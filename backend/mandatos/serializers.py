"""Serializers — módulo Mandatos (H1 + H2)."""
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import (
    CargoMandato,
    Mandato,
    MandatoSnapshot,
    OnboardingEtapa,
    TransicaoMandato,
)


class CargoMandatoSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    cargo_display = serializers.CharField(source="get_cargo_display", read_only=True)

    class Meta:
        model = CargoMandato
        fields = (
            "id",
            "mandato",
            "usuario",
            "usuario_email",
            "usuario_nome",
            "cargo",
            "cargo_display",
            "cargo_custom",
            "data_inicio",
            "data_fim",
            "ativo",
        )

    def get_usuario_nome(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.email


class MandatoSnapshotSerializer(serializers.ModelSerializer):
    integridade_ok = serializers.SerializerMethodField()

    class Meta:
        model = MandatoSnapshot
        fields = (
            "id",
            "mandato",
            "tipo",
            "versao",
            "dados",
            "hash",
            "created_at",
            "integridade_ok",
        )
        read_only_fields = fields

    def get_integridade_ok(self, obj):
        return obj.verificar_integridade()


class OnboardingEtapaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingEtapa
        fields = (
            "id",
            "transicao",
            "codigo",
            "titulo",
            "descricao",
            "ordem",
            "obrigatoria",
            "concluida",
            "concluida_em",
            "dados_contexto",
            "perfil_minimo",
            "responsavel",
        )
        read_only_fields = ("concluida", "concluida_em", "transicao")


class TransicaoMandatoSerializer(serializers.ModelSerializer):
    etapas_onboarding = OnboardingEtapaSerializer(many=True, read_only=True)
    mandato_anterior_titulo = serializers.CharField(
        source="mandato_anterior.titulo", read_only=True
    )
    mandato_novo_titulo = serializers.CharField(
        source="mandato_novo.titulo", read_only=True
    )

    class Meta:
        model = TransicaoMandato
        fields = (
            "id",
            "mandato_anterior",
            "mandato_anterior_titulo",
            "mandato_novo",
            "mandato_novo_titulo",
            "status",
            "data_inicio_transicao",
            "data_conclusao",
            "progresso_percentual",
            "notas_transicao",
            "etapas_onboarding",
        )
        read_only_fields = (
            "status",
            "data_inicio_transicao",
            "data_conclusao",
            "progresso_percentual",
        )


class MandatoListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    cargos_count = serializers.SerializerMethodField()

    class Meta:
        model = Mandato
        fields = (
            "id",
            "titulo",
            "descricao",
            "data_inicio",
            "data_fim",
            "status",
            "status_display",
            "numero_sequencial",
            "encerrado_em",
            "cargos_count",
            "created_at",
        )

    def get_cargos_count(self, obj):
        return obj.cargos.filter(ativo=True).count()


class MandatoDetailSerializer(MandatoListSerializer):
    cargos = CargoMandatoSerializer(many=True, read_only=True)
    snapshots = MandatoSnapshotSerializer(many=True, read_only=True)

    class Meta(MandatoListSerializer.Meta):
        fields = MandatoListSerializer.Meta.fields + (
            "observacoes_encerramento",
            "cargos",
            "snapshots",
            "updated_at",
        )


class MandatoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mandato
        fields = (
            "titulo",
            "descricao",
            "data_inicio",
            "data_fim",
            "numero_sequencial",
            "status",
        )

    def validate_numero_sequencial(self, value):
        if value < 1:
            raise serializers.ValidationError("Número sequencial deve ser >= 1.")
        return value


class IniciarTransicaoSerializer(serializers.Serializer):
    """Payload para iniciar transição entre mandatos."""
    mandato_novo_id = serializers.UUIDField()
    notas_transicao = serializers.CharField(required=False, allow_blank=True)


class ConcluirEtapaSerializer(serializers.Serializer):
    dados_contexto = serializers.JSONField(required=False)
