"""
API do módulo Contatos.

Diretoria: /api/contatos/               CRUD, resumo do funil, notas, converter em associado
           /api/contatos/etiquetas/     CRUD de etiquetas
Público:   /api/contatos/public/?schema=   formulário de contato do site
"""
from django.db.models import Count, Q
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from mandatos.permissions import IsBoardOrAdmin
from membros.models import Filiacao
from tenants.resolvers import resolve_tenant_from_request
from website.models import WebsiteConfig

from .models import Contato, Etiqueta, Nota
from .serializers import ContatoPublicoSerializer, ContatoSerializer, EtiquetaSerializer, NotaSerializer
from .services import converter_em_membro, notificar_associacao, nota_sistema, registrar_contato_publico, resumo_funil

UUID_LOOKUP = r"[0-9a-fA-F-]{36}"


class EtiquetaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "contatos"
    serializer_class = EtiquetaSerializer
    pagination_class = None

    def get_queryset(self):
        return Etiqueta.objects.annotate(contatos_count=Count("contatos"))


class ContatoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "contatos"
    serializer_class = ContatoSerializer
    lookup_value_regex = UUID_LOOKUP
    pagination_class = None

    def get_queryset(self):
        qs = Contato.objects.select_related("membro", "responsavel").prefetch_related("etiquetas")
        if self.action != "list":
            return qs
        qs = qs.annotate(notas_count=Count("notas", filter=Q(notas__tipo=Nota.MANUAL)))
        params = self.request.query_params
        if params.get("etapa"):
            qs = qs.filter(etapa=params["etapa"])
        elif params.get("abertos") == "true":
            qs = qs.filter(etapa__in=Contato.ETAPAS_ABERTAS)
        if params.get("origem"):
            qs = qs.filter(origem=params["origem"])
        if params.get("assunto"):
            qs = qs.filter(assunto=params["assunto"])
        if params.get("etiqueta"):
            qs = qs.filter(etiquetas__id=params["etiqueta"])
        if params.get("search"):
            termo = params["search"]
            qs = qs.filter(
                Q(nome__icontains=termo)
                | Q(email__icontains=termo)
                | Q(instituicao__icontains=termo)
                | Q(mensagem__icontains=termo)
            )
        return qs.distinct()

    def perform_create(self, serializer):
        dados = serializer.validated_data
        origem = dados.get("origem") or Contato.MANUAL
        contato = serializer.save(origem=origem)
        nota_sistema(contato, "Contato cadastrado manualmente.", autor=self.request.user)

    def perform_update(self, serializer):
        anterior = serializer.instance.etapa
        contato = serializer.save()
        if contato.etapa != anterior:
            de = dict(Contato.ETAPA_CHOICES)[anterior]
            para = contato.get_etapa_display()
            nota_sistema(contato, f"Etapa alterada: {de} → {para}.", autor=self.request.user)

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        return Response(resumo_funil())

    @action(detail=True, methods=["get", "post"])
    def notas(self, request, pk=None):
        contato = self.get_object()
        if request.method == "POST":
            serializer = NotaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(contato=contato, autor=request.user, tipo=Nota.MANUAL)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        notas = contato.notas.select_related("autor")
        return Response(NotaSerializer(notas, many=True).data)

    @action(detail=True, methods=["get"])
    def ficha(self, request, pk=None):
        """Ficha 360: resumo e linha do tempo da pessoa em todos os módulos."""
        from .ficha import ficha_contato

        return Response(ficha_contato(self.get_object()))

    @action(detail=True, methods=["post"])
    def converter(self, request, pk=None):
        """POST {tipo_filiacao?} — cria/vincula o associado e move para 'Convertido'."""
        contato = self.get_object()
        tipo = request.data.get("tipo_filiacao") or None
        tipos_validos = {valor for valor, _ in Filiacao._meta.get_field("tipo").choices}
        if tipo and tipo not in tipos_validos:
            raise ValidationError({"tipo_filiacao": "Tipo de filiação inválido."})
        membro, criado = converter_em_membro(contato, request.user, tipo)
        contato.refresh_from_db()
        return Response(
            {"membro_id": str(membro.id), "membro_criado": criado, "contato": ContatoSerializer(contato).data}
        )


class ContatoPublicoView(APIView):
    """POST do formulário de contato do site da associação."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "contatos_public"

    def post(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        serializer = ContatoPublicoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        resposta = {"detail": "Mensagem enviada. A associação entrará em contato em breve."}
        if dados.get("website"):
            return Response(resposta, status=status.HTTP_201_CREATED)
        with schema_context(tenant.schema_name):
            contato, criado = registrar_contato_publico(dados)
            config = WebsiteConfig.objects.first()
            destino = config.contact_email if config else ""
            notificar_associacao(contato, destino, tenant.name, criado)
        return Response(resposta, status=status.HTTP_201_CREATED)
