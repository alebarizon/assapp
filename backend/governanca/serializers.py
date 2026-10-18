from django.db import transaction
from rest_framework import serializers

from .models import (
    Assembleia,
    AssembleiaStatus,
    OpcaoVotacao,
    PresencaAssembleia,
    Votacao,
    VotacaoStatus,
)


class OpcaoVotacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcaoVotacao
        fields = ["id", "titulo", "descricao", "integrantes", "ordem"]
        read_only_fields = ["id", "ordem"]


class VotacaoSerializer(serializers.ModelSerializer):
    opcoes = OpcaoVotacaoSerializer(many=True, required=False)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    censo_display = serializers.CharField(source="get_censo_display", read_only=True)
    assembleia_titulo = serializers.CharField(source="assembleia.titulo", read_only=True, default=None)

    class Meta:
        model = Votacao
        fields = [
            "id", "assembleia", "assembleia_titulo", "mandato", "titulo", "descricao", "tipo", "tipo_display",
            "status", "status_display", "censo", "censo_display", "secreta", "max_escolhas", "permite_branco",
            "fecha_em", "aberta_em", "encerrada_em", "resultado", "opcoes", "created_at",
        ]
        read_only_fields = ["status", "mandato", "aberta_em", "encerrada_em", "resultado", "created_at"]

    def validate(self, attrs):
        if self.instance and self.instance.status != VotacaoStatus.RASCUNHO:
            editaveis = {"descricao", "fecha_em"}
            if set(attrs) - editaveis:
                raise serializers.ValidationError("Depois de aberta, só a descrição e o prazo podem mudar.")
        return attrs

    @transaction.atomic
    def _salvar_opcoes(self, votacao, opcoes):
        if opcoes is None:
            return
        votacao.opcoes.all().delete()
        OpcaoVotacao.objects.bulk_create(
            OpcaoVotacao(votacao=votacao, ordem=i, **{k: v for k, v in o.items() if k != "id"})
            for i, o in enumerate(opcoes)
        )

    def create(self, validated_data):
        opcoes = validated_data.pop("opcoes", None)
        votacao = Votacao.objects.create(created_by=self.context["request"].user, **validated_data)
        self._salvar_opcoes(votacao, opcoes)
        return votacao

    def update(self, instance, validated_data):
        opcoes = validated_data.pop("opcoes", None)
        instance = super().update(instance, validated_data)
        self._salvar_opcoes(instance, opcoes)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status == VotacaoStatus.ABERTA:
            data["resultado"] = None
        return data


class AssembleiaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    modalidade_display = serializers.CharField(source="get_modalidade_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    presentes = serializers.IntegerField(source="presencas.count", read_only=True)
    votacoes = serializers.SerializerMethodField()

    class Meta:
        model = Assembleia
        fields = [
            "id", "titulo", "tipo", "tipo_display", "data_hora", "modalidade", "modalidade_display", "local",
            "link_online", "convocacao", "pauta", "quorum_minimo", "status", "status_display", "mandato",
            "convocada_em", "encerrada_em", "ata", "ata_publicada_em", "ata_hash", "presentes", "votacoes",
            "created_at",
        ]
        read_only_fields = [
            "status", "mandato", "convocada_em", "encerrada_em", "ata_publicada_em", "ata_hash", "created_at",
        ]

    def get_votacoes(self, obj):
        return [
            {"id": str(v.id), "titulo": v.titulo, "status": v.status, "status_display": v.get_status_display()}
            for v in obj.votacoes.all()
        ]

    def validate_pauta(self, value):
        if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
            raise serializers.ValidationError("Informe a pauta como lista de itens.")
        return [i.strip() for i in value if i.strip()]

    def validate(self, attrs):
        if self.instance:
            if self.instance.ata_publicada_em and "ata" in attrs:
                raise serializers.ValidationError({"ata": "A ata já foi publicada e não pode mudar."})
            fechada = self.instance.status in (AssembleiaStatus.ENCERRADA, AssembleiaStatus.CANCELADA)
            if fechada and set(attrs) - {"ata"}:
                raise serializers.ValidationError("Assembleia encerrada: só a ata pode ser editada.")
        return attrs

    def create(self, validated_data):
        return Assembleia.objects.create(created_by=self.context["request"].user, **validated_data)


class PresencaSerializer(serializers.ModelSerializer):
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    forma_display = serializers.CharField(source="get_forma_display", read_only=True)

    class Meta:
        model = PresencaAssembleia
        fields = ["id", "membro", "membro_nome", "forma", "forma_display", "registrada_em"]
