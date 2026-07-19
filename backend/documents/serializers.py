from rest_framework import serializers

from membros.models import Membro

from .models import Document, DocumentAudience


class DocumentSerializer(serializers.ModelSerializer):
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True, allow_null=True)
    uploaded_by_email = serializers.EmailField(
        source="uploaded_by.email", read_only=True, allow_null=True
    )
    audience_display = serializers.CharField(source="get_audience_display", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "file",
            "file_url",
            "file_type",
            "description",
            "audience",
            "audience_display",
            "membro",
            "membro_nome",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
        )
        read_only_fields = ("id", "file_type", "uploaded_by", "created_at")

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        if obj.file:
            return obj.file.url
        return None

    def validate(self, data):
        audience = data.get("audience") or getattr(self.instance, "audience", DocumentAudience.GERAL)
        membro = data.get("membro", getattr(self.instance, "membro", None))
        if audience == DocumentAudience.MEMBRO and not membro:
            raise serializers.ValidationError({"membro": "Obrigatório para audience=membro."})
        if audience != DocumentAudience.MEMBRO:
            data["membro"] = None
        return data
