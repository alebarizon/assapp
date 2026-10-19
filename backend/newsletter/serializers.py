from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from contatos.models import Etiqueta
from eventos.models import EventoAcademico

from .models import Campanha, Descadastro, EnvioCampanha, EnvioRegua, Regua, StatusCampanha, TipoRegua
from .services import SITUACOES, estatisticas

TIPOS_FILIACAO = ("efetivo", "estudante", "honorario", "institucional")


def validar_publico(valor) -> dict:
    if not isinstance(valor, dict):
        raise serializers.ValidationError("Formato inválido.")
    publico = {}
    associados = valor.get("associados")
    if associados is not None:
        if not isinstance(associados, dict):
            raise serializers.ValidationError("Formato inválido para associados.")
        situacoes = [s for s in associados.get("situacoes") or [] if s in SITUACOES]
        tipos = [t for t in associados.get("tipos") or [] if t in TIPOS_FILIACAO]
        publico["associados"] = {"situacoes": situacoes, "tipos": tipos}
    eventos = [str(e) for e in valor.get("eventos") or []]
    if eventos:
        validos = {str(i) for i in EventoAcademico.objects.filter(id__in=eventos).values_list("id", flat=True)}
        publico["eventos"] = [e for e in eventos if e in validos]
    etiquetas = valor.get("etiquetas") or []
    if etiquetas:
        publico["etiquetas"] = list(Etiqueta.objects.filter(id__in=etiquetas).values_list("id", flat=True))
    return publico


class CampanhaSerializer(serializers.ModelSerializer):
    estatisticas = serializers.SerializerMethodField()
    created_by_nome = serializers.SerializerMethodField()

    class Meta:
        model = Campanha
        fields = [
            "id", "assunto", "corpo", "link", "link_label", "publico", "status",
            "enviada_em", "concluida_em", "created_by_nome", "created_at", "updated_at", "estatisticas",
        ]
        read_only_fields = ["status", "enviada_em", "concluida_em", "created_at", "updated_at"]

    def get_estatisticas(self, obj):
        return estatisticas(obj) if obj.status != StatusCampanha.RASCUNHO else None

    def get_created_by_nome(self, obj):
        u = obj.created_by
        return (u.get_full_name() or u.email) if u else None

    def validate_publico(self, value):
        return validar_publico(value)

    def validate(self, attrs):
        if self.instance and self.instance.status != StatusCampanha.RASCUNHO:
            raise serializers.ValidationError("Só é possível editar campanhas em rascunho.")
        link = attrs.get("link", getattr(self.instance, "link", ""))
        if link and not attrs.get("link_label", getattr(self.instance, "link_label", "")):
            attrs["link_label"] = "Saiba mais"
        return attrs


class EnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvioCampanha
        fields = ["id", "email", "nome", "status", "tentativas", "erro", "enviado_em"]


class ReguaSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="get_tipo_display", read_only=True)
    padrao = serializers.SerializerMethodField()
    enviados_30_dias = serializers.SerializerMethodField()
    enviados_total = serializers.SerializerMethodField()

    class Meta:
        model = Regua
        fields = [
            "tipo", "nome", "ativa", "assunto", "corpo", "dias", "padrao",
            "enviados_30_dias", "enviados_total", "updated_at",
        ]
        read_only_fields = ["tipo", "updated_at"]

    def get_padrao(self, obj):
        from .reguas import PADROES

        p = PADROES[obj.tipo]
        return {"assunto": p["assunto"], "corpo": p["corpo"], "dias": p["dias"]}

    def _envios(self, obj):
        return EnvioRegua.objects.filter(tipo=obj.tipo)

    def get_enviados_30_dias(self, obj):
        return self._envios(obj).filter(enviado_em__gte=timezone.now() - timedelta(days=30)).count()

    def get_enviados_total(self, obj):
        return self._envios(obj).count()

    def validate_dias(self, value):
        limite = 24 if self.instance and self.instance.tipo == TipoRegua.INATIVOS else 90
        if not 1 <= value <= limite:
            raise serializers.ValidationError(f"Use um valor entre 1 e {limite}.")
        return value

    def validate(self, attrs):
        for campo in ("assunto", "corpo"):
            if campo in attrs and not attrs[campo].strip():
                raise serializers.ValidationError({campo: "Não pode ficar em branco."})
        return attrs


class EnvioReguaSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = EnvioRegua
        fields = ["id", "tipo", "tipo_nome", "email", "nome", "membro", "detalhe", "enviado_em"]


class DescadastroSerializer(serializers.ModelSerializer):
    campanha_assunto = serializers.CharField(source="campanha.assunto", default=None, read_only=True)

    class Meta:
        model = Descadastro
        fields = ["id", "email", "campanha_assunto", "created_at"]
