"""Serializers — Eventos Acadêmicos (H3)."""
import json

from rest_framework import serializers

from .cientifico import (
    FluxoError,
    autoria_completa,
    chamada_aberta,
    criterios_da_chamada,
    normalizar_coautores,
    nota_media,
)
from .models import (
    AnaisPublicacao,
    AtividadeProgramacao,
    CallForPapers,
    EventoAcademico,
    InscricaoEvento,
    Parecer,
    SubmissaoTrabalho,
    TrabalhoPublicado,
)


class TrabalhoPublicadoSerializer(serializers.ModelSerializer):
    """Diretoria: ajustes por trabalho (DOI, ordem, PDF final)."""

    tem_arquivo = serializers.SerializerMethodField()
    url_publica = serializers.SerializerMethodField()
    arquivo = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = TrabalhoPublicado
        fields = (
            "id", "anais", "submissao", "slug", "ordem", "titulo", "autores", "area_tematica",
            "doi", "arquivo", "tem_arquivo", "url_publica", "publicado_em",
        )
        read_only_fields = ("anais", "submissao", "slug", "titulo", "autores", "area_tematica", "publicado_em")

    def get_tem_arquivo(self, obj):
        return bool(obj.arquivo)

    def get_url_publica(self, obj):
        from django.db import connection

        from .anais import url_publica

        return url_publica(connection.schema_name, obj)

    def validate_doi(self, value):
        value = value.strip()
        for prefixo in ("https://doi.org/", "http://doi.org/", "doi:"):
            if value.lower().startswith(prefixo):
                value = value[len(prefixo):]
        if value and not value.startswith("10."):
            raise serializers.ValidationError("DOI deve começar com 10. (ex.: 10.12345/anais.2026.001).")
        return value

    def validate_arquivo(self, value):
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Envie o trabalho final em PDF.")
        if value.size > 20 * 1024 * 1024:
            raise serializers.ValidationError("Arquivo acima de 20 MB.")
        return value


class AnaisPublicacaoSerializer(serializers.ModelSerializer):
    licenca_display = serializers.CharField(source="get_licenca_display", read_only=True)
    trabalhos = TrabalhoPublicadoSerializer(many=True, read_only=True)

    class Meta:
        model = AnaisPublicacao
        fields = (
            "id", "evento", "titulo", "issn", "isbn", "doi_prefix", "url_publicacao",
            "licenca", "licenca_display", "apresentacao", "editores", "cidade",
            "publicado_em", "metadata", "trabalhos",
        )
        read_only_fields = ("id", "evento", "doi_prefix", "url_publicacao", "publicado_em", "metadata")


class CallForPapersSerializer(serializers.ModelSerializer):
    submissoes_count = serializers.SerializerMethodField()
    criterios_efetivos = serializers.SerializerMethodField()
    aberta = serializers.SerializerMethodField()

    class Meta:
        model = CallForPapers
        fields = (
            "id", "evento", "titulo", "instrucoes",
            "data_abertura", "data_fechamento",
            "areas_tematicas", "max_submissoes_por_autor", "anonimo",
            "criterios", "criterios_efetivos", "nota_corte", "exige_arquivo", "aberta",
            "submissoes_count",
        )

    def get_submissoes_count(self, obj):
        return obj.submissoes.exclude(status="rascunho").count()

    def get_criterios_efetivos(self, obj):
        return criterios_da_chamada(obj)

    def get_aberta(self, obj):
        return chamada_aberta(obj)


class ParecerSerializer(serializers.ModelSerializer):
    parecerista_email = serializers.EmailField(source="parecerista.email", read_only=True)
    parecerista_nome = serializers.SerializerMethodField()
    recomendacao_display = serializers.CharField(
        source="get_recomendacao_display", read_only=True
    )

    class Meta:
        model = Parecer
        fields = (
            "id", "submissao", "parecerista", "parecerista_email", "parecerista_nome",
            "recomendacao", "recomendacao_display", "nota", "notas", "nota_ponderada", "prazo",
            "comentarios_autor", "comentarios_internos",
            "concluido", "concluido_em",
        )
        read_only_fields = ("concluido", "concluido_em", "parecerista")

    def get_parecerista_nome(self, obj):
        return obj.parecerista.get_full_name() or obj.parecerista.email


class SubmissaoTrabalhoSerializer(serializers.ModelSerializer):
    """Visão da comissão organizadora (sempre identificada)."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    autor_email = serializers.EmailField(source="autor.email", read_only=True)
    membro_nome = serializers.CharField(source="membro.nome_completo", read_only=True)
    pareceres = ParecerSerializer(many=True, read_only=True)
    autoria = serializers.SerializerMethodField()
    nota_media = serializers.SerializerMethodField()
    tem_arquivo = serializers.SerializerMethodField()

    class Meta:
        model = SubmissaoTrabalho
        fields = (
            "id", "cfp", "autor", "autor_email", "membro", "membro_nome", "autoria", "coautores",
            "titulo", "resumo", "palavras_chave", "area_tematica", "tem_arquivo",
            "status", "status_display", "submetido_em", "pareceres", "nota_media",
            "decisao_comentario", "decidido_em",
            "created_at",
        )
        read_only_fields = ("autor", "status", "submetido_em", "membro")

    def get_autoria(self, obj):
        return autoria_completa(obj)

    def get_nota_media(self, obj):
        media = nota_media(obj)
        return str(media) if media is not None else None

    def get_tem_arquivo(self, obj):
        return bool(obj.arquivo)


class ListaJsonField(serializers.JSONField):
    """Aceita lista nativa (JSON) ou texto JSON (multipart)."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data or "[]")
            except ValueError:
                raise serializers.ValidationError("JSON inválido.")
        if not isinstance(data, list):
            raise serializers.ValidationError("Informe uma lista.")
        return data


class CoautoresMixin:
    def validate_coautores(self, value):
        try:
            return normalizar_coautores(value)
        except FluxoError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_palavras_chave(self, value):
        if not isinstance(value, list) or not all(isinstance(p, str) for p in value):
            raise serializers.ValidationError("Envie uma lista de palavras-chave.")
        limpas = [" ".join(p.split()) for p in value if p.strip()]
        if len(limpas) > 10:
            raise serializers.ValidationError("Máximo de 10 palavras-chave.")
        return limpas


class MinhaSubmissaoSerializer(CoautoresMixin, serializers.ModelSerializer):
    """Autor: rascunho editável; após a decisão, vê o resultado e os comentários anônimos dos pareceres."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    evento_id = serializers.UUIDField(source="cfp.evento_id", read_only=True)
    evento_titulo = serializers.CharField(source="cfp.evento.titulo", read_only=True)
    palavras_chave = ListaJsonField(required=False)
    coautores = ListaJsonField(required=False)
    arquivo = serializers.FileField(write_only=True, required=False, allow_null=True)
    tem_arquivo = serializers.SerializerMethodField()
    comentarios_pareceres = serializers.SerializerMethodField()
    certificado_codigo = serializers.SerializerMethodField()

    class Meta:
        model = SubmissaoTrabalho
        fields = (
            "id", "cfp", "evento_id", "evento_titulo", "titulo", "resumo", "palavras_chave", "coautores",
            "area_tematica", "arquivo", "tem_arquivo", "status", "status_display", "submetido_em",
            "decidido_em", "decisao_comentario", "comentarios_pareceres", "certificado_codigo", "created_at",
        )
        read_only_fields = (
            "status", "submetido_em", "decidido_em", "decisao_comentario", "created_at",
        )

    def validate_arquivo(self, value):
        if value and value.size > 15 * 1024 * 1024:
            raise serializers.ValidationError("Arquivo acima de 15 MB.")
        if value and not value.name.lower().endswith((".pdf", ".doc", ".docx", ".odt")):
            raise serializers.ValidationError("Envie PDF, DOC, DOCX ou ODT.")
        return value

    def validate_cfp(self, value):
        if self.instance and value != self.instance.cfp:
            raise serializers.ValidationError("Não é possível mudar a chamada do trabalho.")
        return value

    def get_tem_arquivo(self, obj):
        return bool(obj.arquivo)

    def get_comentarios_pareceres(self, obj):
        if not obj.decidido_em:
            return []
        return [p.comentarios_autor for p in obj.pareceres.all() if p.concluido and p.comentarios_autor]

    def get_certificado_codigo(self, obj):
        cert = obj.certificados.filter(papel="autor").first()
        return cert.codigo if cert else None


class MeuParecerSerializer(serializers.ModelSerializer):
    """Parecerista: trabalho sem identificação dos autores quando a chamada é duplo-cega."""

    submissao = serializers.SerializerMethodField()
    criterios = serializers.SerializerMethodField()
    editavel = serializers.SerializerMethodField()
    recomendacao_display = serializers.CharField(source="get_recomendacao_display", read_only=True)

    class Meta:
        model = Parecer
        fields = (
            "id", "prazo", "concluido", "concluido_em", "recomendacao", "recomendacao_display",
            "notas", "nota_ponderada", "comentarios_autor", "comentarios_internos",
            "submissao", "criterios", "editavel",
        )
        read_only_fields = fields

    def get_submissao(self, obj):
        sub = obj.submissao
        cfp = sub.cfp
        dados = {
            "id": str(sub.id),
            "titulo": sub.titulo,
            "resumo": sub.resumo,
            "palavras_chave": sub.palavras_chave,
            "area_tematica": sub.area_tematica,
            "tem_arquivo": bool(sub.arquivo),
            "evento_titulo": cfp.evento.titulo,
            "chamada_titulo": cfp.titulo,
            "anonimo": cfp.anonimo,
            "autoria": None,
        }
        if not cfp.anonimo:
            dados["autoria"] = autoria_completa(sub)
        return dados

    def get_criterios(self, obj):
        return criterios_da_chamada(obj.submissao.cfp)

    def get_editavel(self, obj):
        return obj.submissao.decidido_em is None


class ConcluirMeuParecerSerializer(serializers.Serializer):
    recomendacao = serializers.ChoiceField(choices=["aceitar", "aceitar_com_revisoes", "rejeitar"])
    notas = serializers.DictField(child=serializers.IntegerField(min_value=1, max_value=5))
    comentarios_autor = serializers.CharField(required=False, allow_blank=True, default="")
    comentarios_internos = serializers.CharField(required=False, allow_blank=True, default="")


class ChamadaAbertaSerializer(serializers.ModelSerializer):
    evento_id = serializers.UUIDField(source="evento.id", read_only=True)
    evento_titulo = serializers.CharField(source="evento.titulo", read_only=True)
    evento_inicio = serializers.DateTimeField(source="evento.data_inicio", read_only=True)
    minhas_enviadas = serializers.SerializerMethodField()

    class Meta:
        model = CallForPapers
        fields = (
            "id", "evento_id", "evento_titulo", "evento_inicio", "titulo", "instrucoes",
            "data_abertura", "data_fechamento", "areas_tematicas", "max_submissoes_por_autor",
            "anonimo", "exige_arquivo", "minhas_enviadas",
        )
        read_only_fields = fields

    def get_minhas_enviadas(self, obj):
        from .cientifico import STATUS_CONTA_LIMITE

        user = self.context["request"].user
        return obj.submissoes.filter(autor=user, status__in=STATUS_CONTA_LIMITE).count()


class DecidirSerializer(serializers.Serializer):
    decisao = serializers.ChoiceField(choices=["aceitar", "aceitar_com_revisoes", "rejeitar"])
    comentario = serializers.CharField(required=False, allow_blank=True, default="")
    notificar = serializers.BooleanField(default=True)


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
            "confirmada", "pago_em", "presente",
            "certificado_codigo", "certificado_emitido_em", "created_at",
        )
        read_only_fields = ("pago_em", "certificado_codigo", "certificado_emitido_em", "created_at")
        extra_kwargs = {"nome": {"required": False}, "email": {"required": False}}

    def validate(self, attrs):
        membro = attrs.get("membro")
        if membro:
            attrs.setdefault("nome", membro.nome_completo)
            attrs.setdefault("email", membro.email)
        if not self.instance and (not attrs.get("nome") or not attrs.get("email")):
            raise serializers.ValidationError("Informe o associado ou nome e e-mail do participante.")
        evento = attrs.get("evento")
        if not self.instance and evento and attrs.get("email"):
            if evento.inscricoes.filter(email__iexact=attrs["email"]).exists():
                raise serializers.ValidationError("Este e-mail já está inscrito no evento.")
        return attrs


def _url_arquivo(request, arquivo):
    if not arquivo:
        return None
    return request.build_absolute_uri(arquivo.url) if request else arquivo.url


class EventoListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tem_cfp = serializers.SerializerMethodField()
    submissoes_count = serializers.SerializerMethodField()
    capa_url = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcademico
        fields = (
            "id", "titulo", "slug", "data_inicio", "data_fim",
            "local", "modalidade", "status", "status_display",
            "valor_inscricao", "tem_cfp", "submissoes_count", "created_at",
            "publicado_site", "resumo", "capa_url",
        )

    def get_capa_url(self, obj):
        return _url_arquivo(self.context.get("request"), obj.capa)

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
            "certificado_habilitado", "carga_horaria", "item_loja",
        )

    item_loja = serializers.SerializerMethodField()

    def get_inscricoes_count(self, obj):
        return obj.inscricoes.filter(confirmada=True).count()

    def get_item_loja(self, obj):
        from .services import item_inscricao

        item = item_inscricao(obj)
        if not item:
            return None
        return {
            "id": str(item.id),
            "slug": item.slug,
            "price": str(item.price),
            "member_price": str(item.member_price) if item.member_price is not None else None,
            "is_active": item.is_active,
        }


class EventoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoAcademico
        fields = (
            "titulo", "slug", "descricao", "data_inicio", "data_fim",
            "local", "modalidade", "capacidade_max", "valor_inscricao", "status",
            "certificado_habilitado", "carga_horaria", "publicado_site", "resumo",
        )


class AtividadeProgramacaoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = AtividadeProgramacao
        fields = (
            "id", "evento", "titulo", "tipo", "tipo_display", "inicio", "fim",
            "sala", "responsaveis", "descricao", "link_transmissao",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        inicio = attrs.get("inicio", getattr(self.instance, "inicio", None))
        fim = attrs.get("fim", getattr(self.instance, "fim", None))
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError({"fim": "O término deve ser depois do início."})
        return attrs


class ItemLojaSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    member_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    is_active = serializers.BooleanField(default=True)


class PublicAtividadeSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = AtividadeProgramacao
        fields = (
            "id", "titulo", "tipo", "tipo_display", "inicio", "fim",
            "sala", "responsaveis", "descricao", "link_transmissao",
        )


class PublicEventoListSerializer(serializers.ModelSerializer):
    modalidade_display = serializers.CharField(source="get_modalidade_display", read_only=True)
    capa_url = serializers.SerializerMethodField()
    inscricao = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcademico
        fields = (
            "id", "titulo", "slug", "resumo", "data_inicio", "data_fim",
            "local", "modalidade", "modalidade_display", "status", "capa_url", "inscricao",
        )

    def get_capa_url(self, obj):
        return _url_arquivo(self.context.get("request"), obj.capa)

    def get_inscricao(self, obj):
        from .services import situacao_inscricao

        return situacao_inscricao(obj)


class PublicEventoDetailSerializer(PublicEventoListSerializer):
    programacao = PublicAtividadeSerializer(many=True, read_only=True)
    chamada = serializers.SerializerMethodField()
    anais = serializers.SerializerMethodField()

    class Meta(PublicEventoListSerializer.Meta):
        fields = PublicEventoListSerializer.Meta.fields + (
            "descricao", "carga_horaria", "certificado_habilitado", "programacao", "chamada", "anais",
        )

    def get_chamada(self, obj):
        cfp = getattr(obj, "call_for_papers", None)
        if not cfp:
            return None
        from django.utils import timezone

        agora = timezone.now()
        return {
            "titulo": cfp.titulo,
            "instrucoes": cfp.instrucoes,
            "data_abertura": cfp.data_abertura,
            "data_fechamento": cfp.data_fechamento,
            "areas_tematicas": cfp.areas_tematicas,
            "max_submissoes_por_autor": cfp.max_submissoes_por_autor,
            "anonimo": cfp.anonimo,
            "aberta": cfp.data_abertura <= agora <= cfp.data_fechamento,
        }

    def get_anais(self, obj):
        anais = getattr(obj, "anais", None)
        if not anais or not anais.publicado_em:
            return None
        return {
            "titulo": anais.titulo,
            "issn": anais.issn,
            "url_publicacao": anais.url_publicacao,
            "total_trabalhos": anais.trabalhos.count(),
        }


class AbrirCfpSerializer(serializers.Serializer):
    titulo = serializers.CharField()
    instrucoes = serializers.CharField()
    data_abertura = serializers.DateTimeField()
    data_fechamento = serializers.DateTimeField()
    areas_tematicas = serializers.ListField(child=serializers.CharField(), required=False)
    max_submissoes_por_autor = serializers.IntegerField(default=2, min_value=1)
    anonimo = serializers.BooleanField(default=True)
    criterios = serializers.ListField(child=serializers.DictField(), required=False)
    nota_corte = serializers.DecimalField(
        max_digits=3, decimal_places=2, min_value=1, max_value=5, required=False, allow_null=True
    )
    exige_arquivo = serializers.BooleanField(required=False, default=False)

    def validate_criterios(self, value):
        limpos, nomes = [], set()
        for c in value:
            nome = " ".join(str(c.get("nome") or "").split())
            if not nome:
                continue
            if nome.lower() in nomes:
                raise serializers.ValidationError(f"Critério repetido: {nome}.")
            try:
                peso = int(c.get("peso") or 1)
            except (TypeError, ValueError):
                raise serializers.ValidationError(f"Peso inválido em {nome}.")
            if not 1 <= peso <= 10:
                raise serializers.ValidationError("Pesos vão de 1 a 10.")
            nomes.add(nome.lower())
            limpos.append({"nome": nome, "peso": peso})
        return limpos

    def validate(self, attrs):
        if attrs["data_fechamento"] <= attrs["data_abertura"]:
            raise serializers.ValidationError({"data_fechamento": "O fechamento deve ser depois da abertura."})
        return attrs


class AtribuirPareceristaSerializer(serializers.Serializer):
    parecerista_id = serializers.UUIDField()
    prazo = serializers.DateField(required=False, allow_null=True)
    notificar = serializers.BooleanField(default=True)


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


class PublicTrabalhoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrabalhoPublicado
        fields = ("slug", "ordem", "titulo", "autores", "area_tematica", "palavras_chave", "doi")


class PublicAnaisSerializer(serializers.ModelSerializer):
    licenca_display = serializers.CharField(source="get_licenca_display", read_only=True)
    licenca_url = serializers.SerializerMethodField()
    evento = serializers.SerializerMethodField()
    trabalhos = PublicTrabalhoResumoSerializer(many=True, read_only=True)

    class Meta:
        model = AnaisPublicacao
        fields = (
            "titulo", "issn", "isbn", "licenca", "licenca_display", "licenca_url", "apresentacao",
            "editores", "cidade", "publicado_em", "evento", "trabalhos",
        )

    def get_licenca_url(self, obj):
        from .anais import LICENCA_URL

        return LICENCA_URL.get(obj.licenca)

    def get_evento(self, obj):
        e = obj.evento
        return {"titulo": e.titulo, "slug": e.slug, "data_inicio": e.data_inicio, "local": e.local}
