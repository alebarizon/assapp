from rest_framework import serializers

from .models import Conversa, Mensagem


class MensagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensagem
        fields = ["id", "autor_nome", "da_diretoria", "texto", "created_at"]


class ConversaListSerializer(serializers.ModelSerializer):
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    membro_email = serializers.CharField(source="membro.email", read_only=True)
    nao_lida = serializers.SerializerMethodField()
    previa = serializers.SerializerMethodField()

    class Meta:
        model = Conversa
        fields = [
            "id",
            "assunto",
            "membro",
            "membro_nome",
            "membro_email",
            "status",
            "iniciada_pela_diretoria",
            "nao_lida",
            "previa",
            "ultima_mensagem_em",
            "created_at",
        ]

    def get_nao_lida(self, obj):
        return not obj.lida_pela_diretoria if self.context.get("diretoria") else not obj.lida_pelo_associado

    def get_previa(self, obj):
        ultima = obj.mensagens.order_by("-created_at").first()
        if not ultima:
            return ""
        texto = ultima.texto.replace("\n", " ")
        return texto[:140] + ("…" if len(texto) > 140 else "")


class ConversaDetailSerializer(ConversaListSerializer):
    mensagens = MensagemSerializer(many=True, read_only=True)

    class Meta(ConversaListSerializer.Meta):
        fields = ConversaListSerializer.Meta.fields + ["mensagens"]


def _texto(value: str, msg: str) -> str:
    value = (value or "").strip()
    if not value:
        raise serializers.ValidationError(msg)
    return value


class NovaConversaSerializer(serializers.Serializer):
    assunto = serializers.CharField(max_length=200)
    texto = serializers.CharField(max_length=10000)

    def validate_assunto(self, value):
        return _texto(value, "Informe o assunto.")

    def validate_texto(self, value):
        return _texto(value, "Escreva a mensagem.")


class NovaConversaDiretoriaSerializer(NovaConversaSerializer):
    membros = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    todos_ativos = serializers.BooleanField(required=False, default=False)
    notificar = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        if not attrs["todos_ativos"] and not attrs["membros"]:
            raise serializers.ValidationError({"membros": "Escolha ao menos um associado."})
        return attrs


class RespostaSerializer(serializers.Serializer):
    texto = serializers.CharField(max_length=10000)

    def validate_texto(self, value):
        return _texto(value, "Escreva a mensagem.")
