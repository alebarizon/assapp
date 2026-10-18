"""API REST — Eventos Acadêmicos (H3)."""
from django.db import connection
from django.db.models import Prefetch
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.emails import nome_associacao
from mandatos.permissions import IsBoardOrAdmin
from membros.models import Membro
from tenants.resolvers import resolve_tenant_from_request

from .cientifico import (
    FluxoError,
    candidatos_parecer,
    chamada_aberta,
    decidir_submissao,
    emitir_certificados_cientificos,
    submeter_pelo_autor,
)
from .models import (
    AnaisPublicacao,
    TrabalhoPublicado,
    AtividadeProgramacao,
    CallForPapers,
    EventoAcademico,
    InscricaoEvento,
    Parecer,
    SubmissaoTrabalho,
)
from .serializers import (
    AbrirCfpSerializer,
    AtividadeProgramacaoSerializer,
    AtribuirPareceristaSerializer,
    CallForPapersSerializer,
    ChamadaAbertaSerializer,
    ConcluirMeuParecerSerializer,
    DecidirSerializer,
    ConcluirParecerSerializer,
    EventoCreateSerializer,
    EventoDetailSerializer,
    EventoListSerializer,
    GerarAnaisSerializer,
    InscricaoEventoSerializer,
    ItemLojaSerializer,
    AnaisPublicacaoSerializer,
    PublicAnaisSerializer,
    PublicTrabalhoResumoSerializer,
    TrabalhoPublicadoSerializer,
    MeuParecerSerializer,
    MinhaSubmissaoSerializer,
    ParecerSerializer,
    PublicEventoDetailSerializer,
    PublicEventoListSerializer,
    SubmissaoCreateSerializer,
    SubmissaoTrabalhoSerializer,
)
from .services import (
    abrir_cfp,
    atribuir_parecerista,
    build_inscricao_certificate,
    concluir_parecer,
    emitir_certificados,
    criar_evento_com_mandato,
    gerar_anais,
    resumo_eventos,
    salvar_item_inscricao,
    submeter_trabalho,
)


class EventoAcademicoViewSet(viewsets.ModelViewSet):
    """H3 — Eventos científicos integrados a membros e mandatos."""
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return EventoAcademico.objects.select_related(
            "mandato", "call_for_papers", "anais"
        ).order_by("-data_inicio")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EventoDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return EventoCreateSerializer
        return EventoListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evento = criar_evento_com_mandato(serializer.validated_data)
        return Response(
            EventoListSerializer(evento, context={"request": request}).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post", "delete"])
    def capa(self, request, pk=None):
        """POST multipart {capa} troca a imagem do hotsite; DELETE remove."""
        evento = self.get_object()
        if request.method == "DELETE":
            evento.capa.delete(save=False)
            evento.capa = None
        else:
            arquivo = request.FILES.get("capa")
            if not arquivo:
                return Response({"capa": "Envie uma imagem."}, status=status.HTTP_400_BAD_REQUEST)
            if not (arquivo.content_type or "").startswith("image/"):
                return Response({"capa": "O arquivo precisa ser uma imagem."}, status=status.HTTP_400_BAD_REQUEST)
            evento.capa = arquivo
        evento.save(update_fields=["capa", "updated_at"])
        return Response(EventoDetailSerializer(evento, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="item-loja")
    def item_loja(self, request, pk=None):
        """Cria/atualiza o item de inscrição na loja (preço cheio e de sócio)."""
        evento = self.get_object()
        serializer = ItemLojaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            salvar_item_inscricao(evento, user=request.user, **serializer.validated_data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EventoDetailSerializer(evento, context={"request": request}).data)

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        return Response(resumo_eventos())

    @action(detail=True, methods=["post"])
    def abrir_cfp(self, request, pk=None):
        evento = self.get_object()
        serializer = AbrirCfpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cfp = abrir_cfp(evento, serializer.validated_data)
        return Response(CallForPapersSerializer(cfp).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def gerar_anais(self, request, pk=None):
        """Publica/atualiza os anais a partir das submissões aceitas."""
        evento = self.get_object()
        serializer = GerarAnaisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            anais = gerar_anais(
                evento,
                titulo=serializer.validated_data.get("titulo"),
                issn=serializer.validated_data.get("issn"),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AnaisPublicacaoSerializer(anais).data)

    @action(detail=True, methods=["patch"], url_path="anais")
    def editar_anais(self, request, pk=None):
        """Dados editoriais dos anais: título, ISSN, ISBN, licença, apresentação, editores, cidade."""
        anais = get_object_or_404(AnaisPublicacao, evento=self.get_object())
        serializer = AnaisPublicacaoSerializer(anais, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def presencas(self, request, pk=None):
        """POST {inscricoes: [ids], presente: bool} — marca/desmarca presença em lote."""
        evento = self.get_object()
        ids = request.data.get("inscricoes")
        if not isinstance(ids, list) or not ids:
            return Response({"inscricoes": "Selecione ao menos uma inscrição."}, status=status.HTTP_400_BAD_REQUEST)
        presente = bool(request.data.get("presente", True))
        alteradas = evento.inscricoes.filter(pk__in=ids).update(presente=presente)
        return Response({"alteradas": alteradas})

    @action(detail=True, methods=["post"], url_path="emitir-certificados")
    def emitir_certificados(self, request, pk=None):
        """POST {notificar?: bool} — emite certificados para os presentes ainda sem código."""
        evento = self.get_object()
        try:
            resultado = emitir_certificados(
                evento,
                connection.schema_name,
                nome_associacao(request),
                notificar=bool(request.data.get("notificar", True)),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado)

    @action(detail=True, methods=["get"])
    def submissoes(self, request, pk=None):
        evento = self.get_object()
        if not hasattr(evento, "call_for_papers"):
            return Response([])
        qs = evento.call_for_papers.submissoes.exclude(status="rascunho").select_related(
            "autor", "membro"
        ).prefetch_related("pareceres__parecerista")
        return Response(SubmissaoTrabalhoSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def pareceristas(self, request):
        """Candidatos a parecerista: equipe, pareceristas cadastrados e associados com login."""
        return Response(
            [
                {
                    "id": str(u.id),
                    "nome": u.get_full_name() or u.email,
                    "email": u.email,
                    "papel": u.get_role_display(),
                    "pendentes": u.pareceres.filter(concluido=False).count(),
                }
                for u in candidatos_parecer()
            ]
        )

    @action(detail=True, methods=["post"], url_path="emitir-certificados-cientificos")
    def emitir_certificados_cientificos(self, request, pk=None):
        evento = self.get_object()
        try:
            resultado = emitir_certificados_cientificos(
                evento,
                connection.schema_name,
                nome_associacao(request),
                notificar=bool(request.data.get("notificar", True)),
            )
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado)


class AtividadeProgramacaoViewSet(viewsets.ModelViewSet):
    """Grade do evento — `?evento=<id>`."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    serializer_class = AtividadeProgramacaoSerializer
    pagination_class = None

    def get_queryset(self):
        qs = AtividadeProgramacao.objects.all()
        evento_id = self.request.query_params.get("evento")
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs


def _tenant_publico(request):
    tenant = resolve_tenant_from_request(request)
    if not tenant:
        raise NotFound("Associação não encontrada. Informe ?schema=.")
    return tenant


def _schema_publico(request) -> str:
    return _tenant_publico(request).schema_name


def _eventos_publicos():
    return (
        EventoAcademico.objects.filter(publicado_site=True)
        .exclude(status__in=["rascunho", "cancelado"])
        .select_related("call_for_papers", "anais")
    )


class PublicEventoListView(APIView):
    """GET /api/eventos/public/?schema= — eventos publicados no site (próximos primeiro)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        with schema_context(_schema_publico(request)):
            qs = _eventos_publicos().order_by("-data_inicio")
            return Response(PublicEventoListSerializer(qs, many=True, context={"request": request}).data)


class PublicEventoDetailView(APIView):
    """GET /api/eventos/public/<slug>/?schema= — hotsite do evento."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        with schema_context(_schema_publico(request)):
            evento = (
                _eventos_publicos()
                .prefetch_related(Prefetch("programacao", queryset=AtividadeProgramacao.objects.all()))
                .filter(slug=slug)
                .first()
            )
            if not evento:
                raise NotFound("Evento não encontrado.")
            return Response(PublicEventoDetailSerializer(evento, context={"request": request}).data)


class SubmissaoTrabalhoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return SubmissaoTrabalho.objects.select_related(
            "cfp", "autor", "membro"
        ).prefetch_related("pareceres")

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissaoCreateSerializer
        return SubmissaoTrabalhoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data.copy()
        membro_id = dados.pop("membro_id", None)

        submissao = SubmissaoTrabalho.objects.create(
            autor=request.user,
            **dados,
        )
        if membro_id:
            submissao.membro = get_object_or_404(Membro, pk=membro_id)
            submissao.save(update_fields=["membro"])

        return Response(
            SubmissaoTrabalhoSerializer(submissao).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def submeter(self, request, pk=None):
        submissao = self.get_object()
        submissao = submeter_trabalho(submissao)
        return Response(SubmissaoTrabalhoSerializer(submissao).data)

    @action(detail=True, methods=["post"])
    def atribuir_parecerista(self, request, pk=None):
        submissao = self.get_object()
        serializer = AtribuirPareceristaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parecerista = get_object_or_404(
            User, pk=serializer.validated_data["parecerista_id"], is_active=True
        )
        try:
            parecer = atribuir_parecerista(
                submissao,
                parecerista,
                prazo=serializer.validated_data.get("prazo"),
                notificar=serializer.validated_data["notificar"],
                associacao=nome_associacao(request),
            )
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ParecerSerializer(parecer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def decidir(self, request, pk=None):
        """Decisão da comissão: aceita, aceita com revisões ou rejeita — e envia a carta ao autor."""
        submissao = self.get_object()
        serializer = DecidirSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submissao = decidir_submissao(
                submissao,
                serializer.validated_data["decisao"],
                comentario=serializer.validated_data["comentario"],
                notificar=serializer.validated_data["notificar"],
                associacao=nome_associacao(request),
            )
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubmissaoTrabalhoSerializer(submissao).data)

    @action(detail=True, methods=["get"])
    def arquivo(self, request, pk=None):
        return _baixar_arquivo(self.get_object())


class ParecerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    serializer_class = ParecerSerializer

    def get_queryset(self):
        return Parecer.objects.select_related("submissao", "parecerista")

    def destroy(self, request, pk=None):
        parecer = self.get_object()
        if parecer.concluido:
            return Response({"detail": "Parecer concluído não pode ser removido."}, status=status.HTTP_400_BAD_REQUEST)
        parecer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        parecer = self.get_object()
        serializer = ConcluirParecerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            parecer = concluir_parecer(parecer, **serializer.validated_data)
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ParecerSerializer(parecer).data)


class InscricaoEventoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    serializer_class = InscricaoEventoSerializer

    def get_queryset(self):
        qs = InscricaoEvento.objects.select_related("evento", "membro")
        evento_id = self.request.query_params.get("evento")
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        membro_id = self.request.data.get("membro")
        save_kwargs = {}
        if membro_id:
            membro = Membro.objects.filter(pk=membro_id).first()
            if membro:
                save_kwargs["membro"] = membro
                if not serializer.validated_data.get("nome"):
                    save_kwargs["nome"] = membro.nome_completo
                if not serializer.validated_data.get("email"):
                    save_kwargs["email"] = membro.email
        serializer.save(**save_kwargs)

    @action(detail=True, methods=["get"])
    def certificado(self, request, pk=None):
        inscricao = self.get_object()
        if not inscricao.certificado_codigo:
            return Response({"detail": "Certificado ainda não emitido."}, status=status.HTTP_404_NOT_FOUND)
        pdf = build_inscricao_certificate(inscricao, connection.schema_name, nome_associacao(request))
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="certificado-{inscricao.evento.slug}.pdf"'
        return response


def _baixar_arquivo(submissao: SubmissaoTrabalho):
    if not submissao.arquivo:
        raise NotFound("Trabalho sem arquivo.")
    nome = submissao.arquivo.name.rsplit("/", 1)[-1]
    return FileResponse(submissao.arquivo.open("rb"), as_attachment=True, filename=nome)


class MinhasChamadasView(APIView):
    """GET /api/eventos/my/chamadas/ — chamadas de trabalhos recebendo submissões."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone

        agora = timezone.now()
        qs = (
            CallForPapers.objects.filter(data_abertura__lte=agora, data_fechamento__gte=agora)
            .exclude(evento__status__in=["rascunho", "cancelado"])
            .select_related("evento")
            .order_by("data_fechamento")
        )
        return Response(ChamadaAbertaSerializer(qs, many=True, context={"request": request}).data)


class MinhaSubmissaoViewSet(viewsets.ModelViewSet):
    """Trabalhos do próprio autor. Rascunho é editável/excluível; depois de submetido, só leitura."""

    permission_classes = [IsAuthenticated]
    serializer_class = MinhaSubmissaoSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = None

    def get_queryset(self):
        return (
            SubmissaoTrabalho.objects.filter(autor=self.request.user)
            .select_related("cfp__evento")
            .prefetch_related("pareceres", "certificados")
            .order_by("-created_at")
        )

    def _exigir_rascunho(self, submissao):
        if submissao.status != "rascunho":
            raise ValidationError({"detail": "Trabalho já submetido não pode ser alterado."})

    def perform_create(self, serializer):
        cfp = serializer.validated_data["cfp"]
        if not chamada_aberta(cfp):
            raise ValidationError({"detail": "A chamada de trabalhos não está recebendo submissões."})
        submissao = serializer.save(autor=self.request.user)
        from .services import vincular_membro_por_email

        vincular_membro_por_email(submissao)

    def perform_update(self, serializer):
        self._exigir_rascunho(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._exigir_rascunho(instance)
        if instance.arquivo:
            instance.arquivo.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["post"])
    def submeter(self, request, pk=None):
        try:
            submissao = submeter_pelo_autor(self.get_object())
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(submissao).data)

    @action(detail=True, methods=["get"])
    def arquivo(self, request, pk=None):
        return _baixar_arquivo(self.get_object())


class MeuParecerViewSet(viewsets.ReadOnlyModelViewSet):
    """Pareceres atribuídos ao usuário logado (qualquer papel)."""

    permission_classes = [IsAuthenticated]
    serializer_class = MeuParecerSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Parecer.objects.filter(parecerista=self.request.user)
            .select_related("submissao__cfp__evento", "submissao__autor", "submissao__membro")
            .order_by("concluido", "prazo", "-submissao__submetido_em")
        )

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        parecer = self.get_object()
        serializer = ConcluirMeuParecerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            parecer = concluir_parecer(parecer, **serializer.validated_data)
        except FluxoError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(parecer).data)

    @action(detail=True, methods=["get"])
    def arquivo(self, request, pk=None):
        return _baixar_arquivo(self.get_object().submissao)


class TrabalhoPublicadoViewSet(viewsets.ModelViewSet):
    """Diretoria: DOI, ordem e PDF final de cada trabalho dos anais — `?evento=<id>`."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "eventos"
    serializer_class = TrabalhoPublicadoSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = None
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        qs = TrabalhoPublicado.objects.select_related("anais__evento")
        evento_id = self.request.query_params.get("evento")
        if evento_id:
            qs = qs.filter(anais__evento_id=evento_id)
        return qs

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Trabalhos entram nos anais por \"Gerar anais\"."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_update(self, serializer):
        novo = serializer.validated_data.get("arquivo")
        if novo and serializer.instance.arquivo:
            serializer.instance.arquivo.delete(save=False)
        if novo:
            novo.name = f"{serializer.instance.slug}.pdf"
        serializer.save()

    @action(detail=True, methods=["post"], url_path="remover-arquivo")
    def remover_arquivo(self, request, pk=None):
        trabalho = self.get_object()
        if trabalho.arquivo:
            trabalho.arquivo.delete(save=False)
            trabalho.arquivo = None
            trabalho.save(update_fields=["arquivo"])
        return Response(self.get_serializer(trabalho).data)


def _anais_publicos(slug):
    evento = _eventos_publicos().filter(slug=slug).first()
    anais = getattr(evento, "anais", None) if evento else None
    if not anais or not anais.publicado_em:
        raise NotFound("Anais não encontrados.")
    return anais


def _trabalho_publico(slug, trabalho_slug):
    trabalho = _anais_publicos(slug).trabalhos.filter(slug=trabalho_slug).select_related("anais__evento").first()
    if not trabalho:
        raise NotFound("Trabalho não encontrado nos anais.")
    return trabalho


class PublicAnaisView(APIView):
    """GET /api/eventos/public/<slug>/anais/?schema= — sumário dos anais."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        with schema_context(_schema_publico(request)):
            return Response(PublicAnaisSerializer(_anais_publicos(slug)).data)


class PublicTrabalhoView(APIView):
    """GET /api/eventos/public/<slug>/anais/<trabalho>/?schema= — página citável do trabalho."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, trabalho_slug):
        from .anais import LICENCA_URL, citacoes, url_publica

        tenant = _tenant_publico(request)
        with schema_context(tenant.schema_name):
            trabalho = _trabalho_publico(slug, trabalho_slug)
            anais = trabalho.anais
            url = url_publica(tenant.schema_name, trabalho)
            dados = PublicTrabalhoResumoSerializer(trabalho).data
            dados.update(
                {
                    "resumo": trabalho.resumo,
                    "publicado_em": trabalho.publicado_em,
                    "tem_arquivo_final": bool(trabalho.arquivo),
                    "url": url,
                    "associacao": tenant.name,
                    "citacoes": citacoes(trabalho, tenant.name, url),
                    "anais": {
                        "titulo": anais.titulo,
                        "issn": anais.issn,
                        "isbn": anais.isbn,
                        "licenca": anais.licenca,
                        "licenca_display": anais.get_licenca_display(),
                        "licenca_url": LICENCA_URL.get(anais.licenca),
                        "cidade": anais.cidade,
                    },
                    "evento": {
                        "titulo": anais.evento.titulo,
                        "slug": anais.evento.slug,
                        "data_inicio": anais.evento.data_inicio,
                        "local": anais.evento.local,
                    },
                }
            )
            return Response(dados)


class PublicTrabalhoPdfView(APIView):
    """GET /api/eventos/public/<slug>/anais/<trabalho>/pdf/?schema= — PDF final ou folha com resumo."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, trabalho_slug):
        from .anais import build_trabalho_pdf, url_publica

        tenant = _tenant_publico(request)
        with schema_context(tenant.schema_name):
            trabalho = _trabalho_publico(slug, trabalho_slug)
            nome = f"{trabalho.slug}.pdf"
            if trabalho.arquivo:
                return FileResponse(trabalho.arquivo.open("rb"), filename=nome, content_type="application/pdf")
            pdf = build_trabalho_pdf(trabalho, tenant.name, url_publica(tenant.schema_name, trabalho))
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{nome}"'
        return response
