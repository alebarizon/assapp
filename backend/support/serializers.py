from rest_framework import serializers

from .models import AnexoChamado, Chamado, MensagemChamado


class AnexoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = AnexoChamado
        fields = ["id", "nome", "tamanho", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        url = obj.arquivo.url if obj.arquivo else ""
        return request.build_absolute_uri(url) if request and url else url


class MensagemSerializer(serializers.ModelSerializer):
    anexos = AnexoSerializer(many=True, read_only=True)

    class Meta:
        model = MensagemChamado
        fields = ["id", "autor_nome", "da_equipe", "interna", "texto", "anexos", "created_at"]


class ChamadoListSerializer(serializers.ModelSerializer):
    associacao = serializers.CharField(source="tenant.name", read_only=True)
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    prioridade_display = serializers.CharField(source="get_prioridade_display", read_only=True)
    nao_lido = serializers.SerializerMethodField()

    class Meta:
        model = Chamado
        fields = [
            "id",
            "assunto",
            "associacao",
            "categoria",
            "categoria_display",
            "prioridade",
            "prioridade_display",
            "status",
            "status_display",
            "autor_nome",
            "autor_email",
            "nao_lido",
            "ultima_mensagem_em",
            "created_at",
        ]

    def get_nao_lido(self, obj):
        return not obj.lido_pela_equipe if self.context.get("equipe") else not obj.lido_pela_associacao


class ChamadoDetailSerializer(ChamadoListSerializer):
    mensagens = serializers.SerializerMethodField()

    class Meta(ChamadoListSerializer.Meta):
        fields = ChamadoListSerializer.Meta.fields + ["pagina", "mensagens"]

    def get_mensagens(self, obj):
        qs = obj.mensagens.prefetch_related("anexos")
        if not self.context.get("equipe"):
            qs = qs.filter(interna=False)
        return MensagemSerializer(qs, many=True, context=self.context).data


class AbrirChamadoSerializer(serializers.Serializer):
    assunto = serializers.CharField(max_length=200)
    categoria = serializers.ChoiceField(choices=Chamado.CATEGORIA_CHOICES, required=False)
    prioridade = serializers.ChoiceField(choices=Chamado.PRIORIDADE_CHOICES, required=False)
    mensagem = serializers.CharField(max_length=10000)
    pagina = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")

    def validate_assunto(self, value):
        if not value.strip():
            raise serializers.ValidationError("Informe o assunto.")
        return value.strip()

    def validate_mensagem(self, value):
        if not value.strip():
            raise serializers.ValidationError("Descreva o que aconteceu.")
        return value.strip()


class ResponderSerializer(serializers.Serializer):
    texto = serializers.CharField(max_length=10000)
    interna = serializers.BooleanField(required=False, default=False)

    def validate_texto(self, value):
        if not value.strip():
            raise serializers.ValidationError("Escreva a mensagem.")
        return value.strip()
