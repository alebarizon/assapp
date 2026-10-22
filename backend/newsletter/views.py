"""
API da newsletter.

Painel:  /api/newsletter/campanhas/              CRUD + enviar, teste, cancelar, duplicar, envios
         /api/newsletter/campanhas/publico/      prévia do público (total e amostra)
         /api/newsletter/campanhas/opcoes/       eventos e etiquetas para segmentar
         /api/newsletter/descadastros/           lista e reinscrição (DELETE)
         /api/newsletter/reguas/                 réguas automáticas: lista, PATCH {tipo}, previa, teste,
                                                 restaurar, envios/?tipo=
Público: /api/newsletter/public/descadastrar/?schema=&t=   GET situação, POST descadastra (inclui one-click)
"""
from django.conf import settings
from django_tenants.utils import schema_context
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from contatos.models import Etiqueta
from eventos.models import EventoAcademico
from mandatos.permissions import IsBoardOrAdmin
from tenants.resolvers import resolve_tenant_from_request

from . import reguas, services
from .models import Campanha, Descadastro, EnvioRegua, Regua, StatusCampanha, TipoRegua
from .serializers import (
    CampanhaSerializer,
    DescadastroSerializer,
    EnvioReguaSerializer,
    EnvioSerializer,
    ReguaSerializer,
    validar_publico,
)


class CampanhaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "newsletter"
    serializer_class = CampanhaSerializer
    pagination_class = None
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def get_queryset(self):
        qs = Campanha.objects.select_related("created_by")
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != StatusCampanha.RASCUNHO:
            raise ValidationError("Só é possível excluir campanhas em rascunho.")
        instance.delete()

    def _resposta(self, campanha, **extra):
        campanha.refresh_from_db()
        return Response({**self.get_serializer(campanha).data, **extra})

    @action(detail=False, methods=["post"])
    def publico(self, request):
        publico = validar_publico(request.data.get("publico") or {})
        lista = services.destinatarios(publico)
        resumo = services.resumo_publico(publico)
        resumo["amostra"] = [{"nome": d["nome"], "email": d["email"], "origem": d["origem"]} for d in lista[:8]]
        return Response(resumo)

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        eventos = EventoAcademico.objects.order_by("-data_inicio").values("id", "titulo", "data_inicio")[:50]
        etiquetas = Etiqueta.objects.order_by("nome").values("id", "nome", "cor")
        return Response({"eventos": list(eventos), "etiquetas": list(etiquetas)})

    @action(detail=True, methods=["post"])
    def enviar(self, request, pk=None):
        total = services.enviar(self.get_object())
        return self._resposta(self.get_object(), enfileirados=total)

    @action(detail=True, methods=["post"])
    def teste(self, request, pk=None):
        email = (request.data.get("email") or request.user.email or "").strip()
        if not email:
            raise ValidationError({"email": "Informe um e-mail."})
        ok = services.enviar_teste(self.get_object(), email, request.user.get_full_name())
        if not ok:
            raise ValidationError("Não foi possível enviar o teste. Verifique a configuração de e-mail.")
        return Response({"enviado_para": email})

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        cancelados = services.cancelar(self.get_object())
        return self._resposta(self.get_object(), cancelados=cancelados)

    @action(detail=True, methods=["post"])
    def duplicar(self, request, pk=None):
        origem = self.get_object()
        copia = Campanha.objects.create(
            assunto=f"{origem.assunto} (cópia)"[:200],
            corpo=origem.corpo,
            link=origem.link,
            link_label=origem.link_label,
            publico=origem.publico,
            created_by=request.user,
        )
        return Response(self.get_serializer(copia).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def envios(self, request, pk=None):
        qs = self.get_object().envios.all()
        st = request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        return Response(EnvioSerializer(qs[:500], many=True).data)


class ReguaViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "newsletter"
    serializer_class = ReguaSerializer
    pagination_class = None
    lookup_field = "tipo"
    lookup_value_regex = "|".join(TipoRegua.values)
    http_method_names = ["get", "patch", "post"]

    def get_queryset(self):
        reguas.obter_reguas()
        return Regua.objects.all()

    def list(self, request, *args, **kwargs):
        from core.management.commands.agendador import email_entregue

        return Response({
            "reguas": self.get_serializer(self.get_queryset(), many=True).data,
            "email_entregue": email_entregue(),
            "hora": getattr(settings, "REGUA_HORA", 8),
            "limite_por_dia": reguas.LIMITE_POR_EXECUCAO,
        })

    @action(detail=True, methods=["get"])
    def previa(self, request, tipo=None):
        return Response(reguas.previa(self.get_object()))

    @action(detail=True, methods=["post"])
    def teste(self, request, tipo=None):
        email = (request.data.get("email") or request.user.email or "").strip()
        if not email:
            raise ValidationError({"email": "Informe um e-mail."})
        if not reguas.enviar_teste(self.get_object(), email, request.user.get_full_name()):
            raise ValidationError("Não foi possível enviar o teste. Verifique a configuração de e-mail.")
        return Response({"enviado_para": email})

    @action(detail=True, methods=["post"])
    def restaurar(self, request, tipo=None):
        regua = self.get_object()
        padrao = reguas.PADROES[regua.tipo]
        regua.assunto, regua.corpo, regua.dias = padrao["assunto"], padrao["corpo"], padrao["dias"]
        regua.save(update_fields=["assunto", "corpo", "dias", "updated_at"])
        return Response(self.get_serializer(regua).data)

    @action(detail=False, methods=["get"])
    def envios(self, request):
        qs = EnvioRegua.objects.all()
        tipo = request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo)
        return Response(EnvioReguaSerializer(qs[:200], many=True).data)


class DescadastroViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "newsletter"
    serializer_class = DescadastroSerializer
    pagination_class = None
    queryset = Descadastro.objects.select_related("campanha")


def _mascarar(email: str) -> str:
    usuario, _, dominio = email.partition("@")
    return f"{usuario[:2]}{'*' * max(len(usuario) - 2, 1)}@{dominio}"


class DescadastrarPublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [JSONParser, FormParser]

    def _contexto(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        token = request.query_params.get("t") or request.data.get("t") or ""
        dados = services.ler_token(token, tenant.schema_name)
        if not dados:
            raise ValidationError("Link de descadastro inválido.")
        return tenant, dados

    def get(self, request):
        tenant, dados = self._contexto(request)
        with schema_context(tenant.schema_name):
            descadastrado = Descadastro.objects.filter(email=dados["e"]).exists()
        return Response({"email": _mascarar(dados["e"]), "associacao": tenant.name, "descadastrado": descadastrado})

    def post(self, request):
        tenant, dados = self._contexto(request)
        with schema_context(tenant.schema_name):
            services.descadastrar(dados["e"], dados.get("c"))
        return Response({"email": _mascarar(dados["e"]), "associacao": tenant.name, "descadastrado": True})
