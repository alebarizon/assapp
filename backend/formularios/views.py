"""
API do módulo Formulários.

Diretoria: /api/formularios/            CRUD, duplicar, convites, respostas, resumo, CSV
Associado: /api/formularios/my/         formulários do portal e convites
Público:   /api/formularios/public/f/<public_token>/?schema=   link aberto
           /api/formularios/public/r/<token>/?schema=          convite individual
"""
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.emails import nome_associacao
from mandatos.permissions import IsBoardOrAdmin
from membros.models import Membro
from membros.services import resolver_membro_do_user
from tenants.resolvers import resolve_tenant_from_request

from .models import Formulario, Resposta
from .serializers import (
    FormularioListSerializer,
    FormularioSerializer,
    RespostaSerializer,
    estrutura_publica,
)
from .services import convidar_membros, duplicar, exportar_csv, registrar, resumo, valores_salvos

UUID_LOOKUP = r"[0-9a-fA-F-]{36}"


class FormularioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "formularios"
    lookup_value_regex = UUID_LOOKUP
    pagination_class = None

    def get_serializer_class(self):
        return FormularioListSerializer if self.action == "list" else FormularioSerializer

    def get_queryset(self):
        qs = Formulario.objects.select_related("evento")
        if self.action == "list":
            qs = qs.annotate(
                respostas_enviadas=Count(
                    "respostas", filter=Q(respostas__status=Resposta.ENVIADA), distinct=True
                ),
                convites_pendentes=Count(
                    "respostas",
                    filter=Q(respostas__origem=Resposta.CONVITE) & ~Q(respostas__status=Resposta.ENVIADA),
                    distinct=True,
                ),
                perguntas_count=Count("secoes__perguntas", distinct=True),
            )
            params = self.request.query_params
            if params.get("status"):
                qs = qs.filter(status=params["status"])
            if params.get("evento"):
                qs = qs.filter(evento_id=params["evento"])
            if params.get("search"):
                qs = qs.filter(titulo__icontains=params["search"])
        else:
            qs = qs.prefetch_related("secoes__perguntas")
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def duplicar(self, request, pk=None):
        copia = duplicar(self.get_object(), request.user)
        return Response(FormularioSerializer(copia).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def convites(self, request, pk=None):
        """
        GET: convites e situação.
        POST {membros: [ids]} | {todos_ativos: true} | {reenviar_pendentes: true}; {notificar: false} não envia e-mail.
        """
        formulario = self.get_object()
        if request.method == "POST":
            reenviar = bool(request.data.get("reenviar_pendentes"))
            if request.data.get("todos_ativos"):
                membros = Membro.objects.filter(ativo=True)
            elif reenviar and not request.data.get("membros"):
                pendentes = formulario.respostas.filter(origem=Resposta.CONVITE).exclude(status=Resposta.ENVIADA)
                membros = Membro.objects.filter(id__in=pendentes.values("membro_id"))
            else:
                ids = request.data.get("membros") or []
                if not isinstance(ids, list) or not ids:
                    raise ValidationError({"membros": "Selecione ao menos um associado."})
                membros = Membro.objects.filter(id__in=ids)
            if reenviar and not formulario.aceitando_respostas:
                raise ValidationError({"detail": "Publique o formulário (ou reabra o prazo) antes de enviar convites."})
            resultado = convidar_membros(
                formulario,
                membros.distinct(),
                schema=connection.schema_name,
                associacao=nome_associacao(request),
                notificar=request.data.get("notificar", True) is not False,
                reenviar_pendentes=reenviar,
            )
            return Response(resultado, status=status.HTTP_201_CREATED)
        convites = formulario.respostas.filter(origem=Resposta.CONVITE).order_by("nome")
        return Response(RespostaSerializer(convites, many=True).data)

    @action(detail=True, methods=["get"])
    def respostas(self, request, pk=None):
        formulario = self.get_object()
        qs = formulario.respostas.filter(status=Resposta.ENVIADA).prefetch_related("itens")
        return Response(RespostaSerializer(qs, many=True, context={"incluir_valores": True}).data)

    @action(
        detail=True,
        methods=["delete"],
        url_path=rf"respostas/(?P<resposta_id>{UUID_LOOKUP})",
    )
    def excluir_resposta(self, request, pk=None, resposta_id=None):
        resposta = get_object_or_404(Resposta, pk=resposta_id, formulario=self.get_object())
        resposta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def resumo(self, request, pk=None):
        return Response(resumo(self.get_object()))

    @action(detail=True, methods=["get"])
    def exportar(self, request, pk=None):
        formulario = self.get_object()
        response = HttpResponse(exportar_csv(formulario), content_type="text/csv; charset=utf-8")
        nome = slugify(formulario.titulo) or "formulario"
        response["Content-Disposition"] = f'attachment; filename="respostas-{nome}.csv"'
        return response


# ---------------------------------------------------------------- Portal do associado


class MeusFormulariosViewSet(viewsets.GenericViewSet):
    """
    GET  my/                 formulários disponíveis no portal + convites
    GET  my/{formulario}/    estrutura + respostas salvas
    POST my/{formulario}/salvar/  |  my/{formulario}/enviar/   {answers}
    """

    permission_classes = [IsAuthenticated]
    lookup_value_regex = UUID_LOOKUP

    def get_membro(self):
        membro = resolver_membro_do_user(self.request.user, auto_link=True)
        if not membro:
            raise NotFound("Perfil de associado não encontrado.")
        return membro

    def _disponiveis(self, membro):
        return (
            Formulario.objects.filter(status__in=[Formulario.PUBLICADO, Formulario.ENCERRADO])
            .filter(Q(disponivel_no_portal=True) | Q(respostas__membro=membro))
            .distinct()
        )

    def _formulario(self, pk, membro):
        formulario = self._disponiveis(membro).filter(pk=pk).first()
        if not formulario:
            raise NotFound("Formulário não encontrado.")
        return formulario

    def list(self, request):
        membro = self.get_membro()
        minhas = {r.formulario_id: r for r in Resposta.objects.filter(membro=membro)}
        itens = []
        for f in self._disponiveis(membro).order_by("-created_at"):
            resposta = minhas.get(f.id)
            if not f.aceitando_respostas and not (resposta and resposta.status == Resposta.ENVIADA):
                continue
            itens.append(
                {
                    "id": str(f.id),
                    "titulo": f.titulo,
                    "descricao": f.descricao,
                    "encerra_em": f.encerra_em,
                    "aceitando_respostas": f.aceitando_respostas,
                    "minha_situacao": resposta.status if resposta else Resposta.PENDENTE,
                    "enviada_em": resposta.enviada_em if resposta else None,
                }
            )
        return Response(itens)

    def retrieve(self, request, pk=None):
        membro = self.get_membro()
        formulario = self._formulario(pk, membro)
        resposta = Resposta.objects.filter(formulario=formulario, membro=membro).prefetch_related("itens").first()
        data = estrutura_publica(formulario)
        data["situacao"] = resposta.status if resposta else Resposta.PENDENTE
        data["valores"] = valores_salvos(resposta)
        return Response(data)

    def _registrar(self, request, pk, enviar):
        membro = self.get_membro()
        formulario = self._formulario(pk, membro)
        resposta = Resposta.objects.filter(formulario=formulario, membro=membro).first() or Resposta(
            formulario=formulario,
            membro=membro,
            origem=Resposta.PORTAL,
            nome=membro.nome_completo,
            email=membro.email or "",
        )
        registrar(resposta, request.data.get("answers") or {}, enviar=enviar)
        return Response({"situacao": resposta.status, "mensagem_confirmacao": formulario.mensagem_confirmacao})

    @action(detail=True, methods=["post"])
    def salvar(self, request, pk=None):
        return self._registrar(request, pk, enviar=False)

    @action(detail=True, methods=["post"])
    def enviar(self, request, pk=None):
        return self._registrar(request, pk, enviar=True)


# ---------------------------------------------------------------- Rotas públicas


def _tenant(request):
    tenant = resolve_tenant_from_request(request)
    if not tenant:
        raise NotFound("Associação não encontrada. Informe ?schema=.")
    return tenant


class PublicBase(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "formularios_public"


class PublicFormularioView(PublicBase):
    """Link aberto: GET estrutura · POST {nome, email, answers} cria uma resposta enviada."""

    def _formulario(self, token):
        formulario = (
            Formulario.objects.select_related("evento")
            .filter(public_token=token, link_publico_ativo=True)
            .exclude(status=Formulario.RASCUNHO)
            .first()
        )
        if not formulario:
            raise NotFound("Formulário não encontrado.")
        return formulario

    def get(self, request, token):
        tenant = _tenant(request)
        with schema_context(tenant.schema_name):
            data = estrutura_publica(self._formulario(token))
            data["associacao"] = tenant.name
            return Response(data)

    def post(self, request, token):
        tenant = _tenant(request)
        with schema_context(tenant.schema_name):
            formulario = self._formulario(token)
            nome = (request.data.get("nome") or "").strip()[:200]
            email = (request.data.get("email") or "").strip()[:254]
            if formulario.pedir_identificacao:
                erros = {}
                if not nome:
                    erros["nome"] = "Informe seu nome."
                if not email or "@" not in email:
                    erros["email"] = "Informe um e-mail válido."
                if erros:
                    raise ValidationError(erros)
            resposta = Resposta(
                formulario=formulario, nome=nome, email=email, origem=Resposta.LINK_PUBLICO
            )
            registrar(resposta, request.data.get("answers") or {}, enviar=True)
            return Response(
                {"situacao": resposta.status, "mensagem_confirmacao": formulario.mensagem_confirmacao},
                status=status.HTTP_201_CREATED,
            )


class PublicConviteView(PublicBase):
    """Convite individual: GET estrutura + respostas salvas · POST {answers, enviar: bool}."""

    def _resposta(self, token):
        resposta = (
            Resposta.objects.select_related("formulario__evento")
            .prefetch_related("itens")
            .filter(token=token)
            .exclude(formulario__status=Formulario.RASCUNHO)
            .first()
        )
        if not resposta:
            raise NotFound("Convite não encontrado.")
        return resposta

    def get(self, request, token):
        tenant = _tenant(request)
        with schema_context(tenant.schema_name):
            resposta = self._resposta(token)
            data = estrutura_publica(resposta.formulario)
            data.update(
                {
                    "associacao": tenant.name,
                    "pedir_identificacao": False,
                    "nome": resposta.nome,
                    "situacao": resposta.status,
                    "valores": valores_salvos(resposta),
                }
            )
            return Response(data)

    def post(self, request, token):
        tenant = _tenant(request)
        with schema_context(tenant.schema_name):
            resposta = self._resposta(token)
            enviar = bool(request.data.get("enviar", True))
            registrar(resposta, request.data.get("answers") or {}, enviar=enviar)
            return Response(
                {
                    "situacao": resposta.status,
                    "mensagem_confirmacao": resposta.formulario.mensagem_confirmacao,
                }
            )
