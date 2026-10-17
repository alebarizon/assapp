from django.db import transaction
from rest_framework import serializers

from .models import Formulario, Pergunta, Resposta, Secao


class PerguntaSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Pergunta
        fields = ["id", "texto", "ajuda", "tipo", "opcoes", "escala_min", "escala_max", "obrigatoria"]

    def validate_opcoes(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Lista de opções inválida.")
        limpas = [str(v).strip()[:200] for v in value if str(v).strip()]
        if len(limpas) != len(set(limpas)):
            raise serializers.ValidationError("Há opções repetidas.")
        return limpas

    def validate(self, attrs):
        tipo = attrs.get("tipo", Pergunta.TEXTO_CURTO)
        if tipo in Pergunta.TIPOS_COM_OPCOES:
            if len(attrs.get("opcoes") or []) < 2:
                raise serializers.ValidationError({"opcoes": "Informe ao menos duas opções."})
        else:
            attrs["opcoes"] = []
        if tipo == Pergunta.ESCALA:
            minimo, maximo = attrs.get("escala_min", 1), attrs.get("escala_max", 5)
            if minimo not in (0, 1) or not (minimo < maximo <= 10):
                raise serializers.ValidationError({"escala_max": "Use escala de 0 ou 1 até no máximo 10."})
        return attrs


class SecaoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    perguntas = PerguntaSerializer(many=True, required=False)

    class Meta:
        model = Secao
        fields = ["id", "titulo", "descricao", "perguntas"]


class FormularioListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    evento_titulo = serializers.CharField(source="evento.titulo", read_only=True, default=None)
    respostas_enviadas = serializers.IntegerField(read_only=True)
    convites_pendentes = serializers.IntegerField(read_only=True)
    perguntas_count = serializers.IntegerField(read_only=True)
    aceitando_respostas = serializers.BooleanField(read_only=True)

    class Meta:
        model = Formulario
        fields = [
            "id",
            "titulo",
            "status",
            "status_display",
            "link_publico_ativo",
            "disponivel_no_portal",
            "evento",
            "evento_titulo",
            "encerra_em",
            "respostas_enviadas",
            "convites_pendentes",
            "perguntas_count",
            "aceitando_respostas",
            "created_at",
        ]


class FormularioSerializer(serializers.ModelSerializer):
    secoes = SecaoSerializer(many=True, required=False)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    evento_titulo = serializers.CharField(source="evento.titulo", read_only=True, default=None)
    aceitando_respostas = serializers.BooleanField(read_only=True)
    tem_respostas = serializers.SerializerMethodField()

    class Meta:
        model = Formulario
        fields = [
            "id",
            "titulo",
            "descricao",
            "status",
            "status_display",
            "link_publico_ativo",
            "pedir_identificacao",
            "disponivel_no_portal",
            "public_token",
            "evento",
            "evento_titulo",
            "encerra_em",
            "mensagem_confirmacao",
            "aceitando_respostas",
            "tem_respostas",
            "secoes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_token", "created_at", "updated_at"]

    def get_tem_respostas(self, obj):
        return obj.respostas.filter(status=Resposta.ENVIADA).exists()

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", Formulario.RASCUNHO))
        if status == Formulario.PUBLICADO:
            if "secoes" in attrs:
                tem_pergunta = any(s.get("perguntas") for s in attrs["secoes"])
            else:
                tem_pergunta = bool(
                    self.instance and Pergunta.objects.filter(secao__formulario=self.instance).exists()
                )
            if not tem_pergunta:
                raise serializers.ValidationError({"status": "Adicione ao menos uma pergunta antes de publicar."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        secoes = validated_data.pop("secoes", None)
        formulario = Formulario.objects.create(**validated_data)
        self._sync_secoes(formulario, secoes if secoes is not None else [{"titulo": "", "perguntas": []}])
        return formulario

    @transaction.atomic
    def update(self, instance, validated_data):
        secoes = validated_data.pop("secoes", None)
        instance = super().update(instance, validated_data)
        if secoes is not None:
            self._sync_secoes(instance, secoes)
        return instance

    def _sync_secoes(self, formulario, secoes_data):
        """Mantém os ids existentes (preserva respostas) e remove o que saiu do formulário."""
        secoes_atuais = {s.id: s for s in formulario.secoes.all()}
        perguntas_atuais = {p.id: p for p in Pergunta.objects.filter(secao__formulario=formulario)}
        secoes_mantidas, perguntas_mantidas = set(), set()

        for ordem, dados in enumerate(secoes_data):
            perguntas_data = dados.pop("perguntas", [])
            secao = secoes_atuais.get(dados.pop("id", None))
            if secao:
                for campo, valor in dados.items():
                    setattr(secao, campo, valor)
                secao.ordem = ordem
                secao.save()
            else:
                secao = Secao.objects.create(formulario=formulario, ordem=ordem, **dados)
            secoes_mantidas.add(secao.id)

            for p_ordem, p_dados in enumerate(perguntas_data):
                pergunta = perguntas_atuais.get(p_dados.pop("id", None))
                if pergunta:
                    for campo, valor in p_dados.items():
                        setattr(pergunta, campo, valor)
                    pergunta.secao = secao
                    pergunta.ordem = p_ordem
                    pergunta.save()
                else:
                    pergunta = Pergunta.objects.create(secao=secao, ordem=p_ordem, **p_dados)
                perguntas_mantidas.add(pergunta.id)

        Pergunta.objects.filter(secao__formulario=formulario).exclude(id__in=perguntas_mantidas).delete()
        formulario.secoes.exclude(id__in=secoes_mantidas).delete()


class RespostaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    origem_display = serializers.CharField(source="get_origem_display", read_only=True)
    valores = serializers.SerializerMethodField()

    class Meta:
        model = Resposta
        fields = [
            "id",
            "membro",
            "nome",
            "email",
            "origem",
            "origem_display",
            "status",
            "status_display",
            "token",
            "enviada_em",
            "created_at",
            "valores",
        ]
        read_only_fields = fields

    def get_valores(self, obj):
        if not self.context.get("incluir_valores"):
            return None
        return {
            str(i.pergunta_id): i.valor_lista if i.valor_lista is not None else i.valor_texto
            for i in obj.itens.all()
        }


def estrutura_publica(formulario: Formulario) -> dict:
    """Formulário para quem responde (sem dados internos)."""
    return {
        "id": str(formulario.id),
        "titulo": formulario.titulo,
        "descricao": formulario.descricao,
        "aceitando_respostas": formulario.aceitando_respostas,
        "pedir_identificacao": formulario.pedir_identificacao,
        "mensagem_confirmacao": formulario.mensagem_confirmacao,
        "evento_titulo": formulario.evento.titulo if formulario.evento_id else None,
        "secoes": [
            {
                "id": str(secao.id),
                "titulo": secao.titulo,
                "descricao": secao.descricao,
                "perguntas": [
                    {
                        "id": str(p.id),
                        "texto": p.texto,
                        "ajuda": p.ajuda,
                        "tipo": p.tipo,
                        "opcoes": p.opcoes,
                        "escala_min": p.escala_min,
                        "escala_max": p.escala_max,
                        "obrigatoria": p.obrigatoria,
                    }
                    for p in secao.perguntas.all()
                ],
            }
            for secao in formulario.secoes.prefetch_related("perguntas")
        ],
    }
