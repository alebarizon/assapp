"""Serializers — Memória Institucional (H1)."""
from rest_framework import serializers

from .models import ContextoHistorico, TimelineInstitucional


class ContextoHistoricoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    autor_email = serializers.EmailField(source="autor.email", read_only=True)
    autor_nome = serializers.SerializerMethodField()
    mandato_titulo = serializers.CharField(source="mandato.titulo", read_only=True)

    class Meta:
        model = ContextoHistorico
        fields = (
            "id",
            "mandato",
            "mandato_titulo",
            "autor",
            "autor_email",
            "autor_nome",
            "tipo",
            "tipo_display",
            "titulo",
            "conteudo",
            "decisao",
            "motivo",
            "entidade_tipo",
            "entidade_id",
            "tags",
            "visivel_diretoria",
            "arquivado",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "autor", "arquivado", "created_at", "updated_at")

    def get_autor_nome(self, obj):
        if not obj.autor:
            return None
        return obj.autor.get_full_name() or obj.autor.email


class ContextoHistoricoCreateSerializer(serializers.ModelSerializer):
    """H1 — exige motivo em decisões para preservação ativa."""

    class Meta:
        model = ContextoHistorico
        fields = (
            "mandato",
            "tipo",
            "titulo",
            "conteudo",
            "decisao",
            "motivo",
            "entidade_tipo",
            "entidade_id",
            "tags",
            "visivel_diretoria",
        )

    def validate(self, data):
        if data.get("tipo") == "decisao" and not data.get("motivo"):
            raise serializers.ValidationError(
                {"motivo": "H1: decisões devem registrar o motivo (por quê)."}
            )
        return data


class TimelineInstitucionalSerializer(serializers.ModelSerializer):
    mandato_titulo = serializers.CharField(source="mandato.titulo", read_only=True)

    class Meta:
        model = TimelineInstitucional
        fields = (
            "id",
            "mandato",
            "mandato_titulo",
            "tipo",
            "titulo",
            "descricao",
            "data_evento",
            "metadata",
            "contexto_id",
        )
        read_only_fields = fields
