from rest_framework import serializers

from contatos.models import Etiqueta
from eventos.models import EventoAcademico

from .models import Campanha, Descadastro, EnvioCampanha, StatusCampanha
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


class DescadastroSerializer(serializers.ModelSerializer):
    campanha_assunto = serializers.CharField(source="campanha.assunto", default=None, read_only=True)

    class Meta:
        model = Descadastro
        fields = ["id", "email", "campanha_assunto", "created_at"]
