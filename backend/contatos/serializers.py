from rest_framework import serializers

from .models import Contato, Etiqueta, Nota


class EtiquetaSerializer(serializers.ModelSerializer):
    contatos_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Etiqueta
        fields = ["id", "nome", "cor", "contatos_count"]

    def validate_nome(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome da etiqueta.")
        qs = Etiqueta.objects.filter(nome__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe uma etiqueta com esse nome.")
        return value


class NotaSerializer(serializers.ModelSerializer):
    autor_nome = serializers.SerializerMethodField()

    class Meta:
        model = Nota
        fields = ["id", "tipo", "texto", "autor_nome", "created_at"]
        read_only_fields = ["tipo", "autor_nome", "created_at"]

    def get_autor_nome(self, obj):
        if not obj.autor:
            return ""
        return obj.autor.get_full_name() or obj.autor.email

    def validate_texto(self, value):
        if not value.strip():
            raise serializers.ValidationError("Escreva a anotação.")
        return value.strip()


class ContatoSerializer(serializers.ModelSerializer):
    etiquetas = EtiquetaSerializer(many=True, read_only=True)
    etiqueta_ids = serializers.PrimaryKeyRelatedField(
        queryset=Etiqueta.objects.all(), many=True, write_only=True, required=False, source="etiquetas"
    )
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True, default=None)
    responsavel_nome = serializers.SerializerMethodField()
    notas_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Contato
        fields = [
            "id",
            "nome",
            "email",
            "telefone",
            "instituicao",
            "assunto",
            "mensagem",
            "etapa",
            "origem",
            "etiquetas",
            "etiqueta_ids",
            "responsavel",
            "responsavel_nome",
            "membro",
            "membro_nome",
            "consentimento_lgpd",
            "ultima_interacao_em",
            "notas_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["membro", "consentimento_lgpd", "ultima_interacao_em", "created_at", "updated_at"]

    def get_responsavel_nome(self, obj):
        if not obj.responsavel:
            return ""
        return obj.responsavel.get_full_name() or obj.responsavel.email

    def validate_email(self, value):
        return value.strip().lower()


class ContatoPublicoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    instituicao = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    assunto = serializers.ChoiceField(choices=Contato.ASSUNTO_CHOICES, required=False, default="outro")
    mensagem = serializers.CharField(max_length=5000)
    origem = serializers.ChoiceField(
        choices=[Contato.SITE_CONTATO, Contato.SITE_ASSOCIE_SE], required=False, default=Contato.SITE_CONTATO
    )
    consentimento_lgpd = serializers.BooleanField()
    # Honeypot: campo invisível no site; bots costumam preenchê-lo.
    website = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_nome(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Informe seu nome.")
        return value

    def validate_mensagem(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Escreva sua mensagem.")
        return value

    def validate_consentimento_lgpd(self, value):
        if not value:
            raise serializers.ValidationError("É preciso autorizar o uso dos dados para o retorno do contato.")
        return value
