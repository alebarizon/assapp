"""Serializers — Eventos Acadêmicos (H3)."""
from rest_framework import serializers

from .models import (
    AnaisPublicacao,
    CallForPapers,
    EventoAcademico,
    InscricaoEvento,
    Parecer,
    SubmissaoTrabalho,
)


class AnaisPublicacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnaisPublicacao
        fields = (
            "id", "evento", "titulo", "issn", "doi_prefix",
            "url_publicacao", "publicado_em", "metadata",
        )
        read_only_fields = fields


class CallForPapersSerializer(serializers.ModelSerializer):
    submissoes_count = serializers.SerializerMethodField()

    class Meta:
        model = CallForPapers
        fields = (
            "id", "evento", "titulo", "instrucoes",
            "data_abertura", "data_fechamento",
            "areas_tematicas", "max_submissoes_por_autor", "anonimo",
            "submissoes_count",
        )

    def get_submissoes_count(self, obj):
        return obj.submissoes.exclude(status="rascunho").count()


class ParecerSerializer(serializers.ModelSerializer):
    parecerista_email = serializers.EmailField(source="parecerista.email", read_only=True)
    recomendacao_display = serializers.CharField(
        source="get_recomendacao_display", read_only=True
    )

    class Meta:
        model = Parecer
        fields = (
            "id", "submissao", "parecerista", "parecerista_email",
            "recomendacao", "recomendacao_display", "nota",
            "comentarios_autor", "comentarios_internos",
            "concluido", "concluido_em",
        )
        read_only_fields = ("concluido", "concluido_em", "parecerista")


class SubmissaoTrabalhoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    autor_email = serializers.EmailField(source="autor.email", read_only=True)
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    pareceres = ParecerSerializer(many=True, read_only=True)

    class Meta:
        model = SubmissaoTrabalho
        fields = (
            "id", "cfp", "autor", "autor_email", "membro", "membro_nome",
            "titulo", "resumo", "palavras_chave", "area_tematica",
            "status", "status_display", "submetido_em", "pareceres",
            "created_at",
        )
        read_only_fields = ("autor", "status", "submetido_em", "membro")


class SubmissaoCreateSerializer(serializers.ModelSerializer):
    membro_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = SubmissaoTrabalho
        fields = (
            "cfp", "titulo", "resumo", "palavras_chave",
            "area_tematica", "membro_id",
        )


class InscricaoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InscricaoEvento
        fields = (
            "id", "evento", "membro", "nome", "email",
            "confirmada", "pago_em", "created_at",
        )
        read_only_fields = ("pago_em", "created_at")


class EventoListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tem_cfp = serializers.SerializerMethodField()
    submissoes_count = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcademico
        fields = (
            "id", "titulo", "slug", "data_inicio", "data_fim",
            "local", "modalidade", "status", "status_display",
            "valor_inscricao", "tem_cfp", "submissoes_count", "created_at",
        )

    def get_tem_cfp(self, obj):
        return hasattr(obj, "call_for_papers")

    def get_submissoes_count(self, obj):
        if hasattr(obj, "call_for_papers"):
            return obj.call_for_papers.submissoes.exclude(status="rascunho").count()
        return 0


class EventoDetailSerializer(EventoListSerializer):
    call_for_papers = CallForPapersSerializer(read_only=True)
    anais = AnaisPublicacaoSerializer(read_only=True)
    inscricoes_count = serializers.SerializerMethodField()
    mandato_titulo = serializers.CharField(source="mandato.titulo", read_only=True)

    class Meta(EventoListSerializer.Meta):
        fields = EventoListSerializer.Meta.fields + (
            "descricao", "capacidade_max", "mandato", "mandato_titulo",
            "call_for_papers", "anais", "inscricoes_count", "updated_at",
        )

    def get_inscricoes_count(self, obj):
        return obj.inscricoes.filter(confirmada=True).count()


class EventoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoAcademico
        fields = (
            "titulo", "slug", "descricao", "data_inicio", "data_fim",
            "local", "modalidade", "capacidade_max", "valor_inscricao", "status",
        )


class AbrirCfpSerializer(serializers.Serializer):
    titulo = serializers.CharField()
    instrucoes = serializers.CharField()
    data_abertura = serializers.DateTimeField()
    data_fechamento = serializers.DateTimeField()
    areas_tematicas = serializers.ListField(child=serializers.CharField(), required=False)
    max_submissoes_por_autor = serializers.IntegerField(default=2, min_value=1)
    anonimo = serializers.BooleanField(default=True)


class AtribuirPareceristaSerializer(serializers.Serializer):
    parecerista_id = serializers.UUIDField()


class ConcluirParecerSerializer(serializers.Serializer):
    recomendacao = serializers.ChoiceField(
        choices=["aceitar", "aceitar_com_revisoes", "rejeitar"]
    )
    nota = serializers.IntegerField(min_value=1, max_value=5, required=False)
    comentarios_autor = serializers.CharField(required=False, allow_blank=True)
    comentarios_internos = serializers.CharField(required=False, allow_blank=True)


class GerarAnaisSerializer(serializers.Serializer):
    titulo = serializers.CharField(required=False)
    issn = serializers.CharField(required=False, allow_blank=True)
