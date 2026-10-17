"""Usuários e perfis da associação + definição/redefinição de senha."""
from django.db import connection
from django_tenants.utils import get_tenant_model, schema_context
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.emails import nome_associacao
from mandatos.permissions import IsBoardOrAdmin

from .access import MATRIZ, MODULOS, PERFIL_CHOICES, SUGESTAO_POR_CARGO
from .equipe import (
    convidar,
    convite_pendente,
    enviar_convite,
    enviar_redefinicao,
    garantir_gestor_restante,
    normalizar_perfis,
    usuario_do_link,
)
from .models import User
from .serializers import EquipeUsuarioSerializer


class EquipeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Equipe com acesso ao painel. Exclusivo do perfil gestor."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "usuarios"
    serializer_class = EquipeUsuarioSerializer
    pagination_class = None

    def get_queryset(self):
        qs = User.objects.filter(role__in=(User.ASSOCIATION_ADMIN, User.BOARD_MEMBER))
        ativos = self.request.query_params.get("ativos")
        if ativos in ("true", "false"):
            qs = qs.filter(is_active=ativos == "true")
        return qs.order_by("-is_active", "first_name", "email")

    def create(self, request):
        data = request.data
        user, enviado = convidar(
            email=data.get("email"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            perfis=data.get("perfis"),
            tenant_id=request.user.tenant_id,
            schema=connection.schema_name,
            associacao=nome_associacao(request),
            convidado_por=request.user,
        )
        payload = self.get_serializer(user).data
        payload["email_enviado"] = enviado
        return Response(payload, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        user = self.get_object()
        data = request.data
        campos = []
        if "perfis" in data:
            perfis = normalizar_perfis(data.get("perfis"))
            garantir_gestor_restante(user, novos_perfis=perfis)
            user.perfis = perfis
            campos.append("perfis")
        if "is_active" in data:
            ativo = bool(data.get("is_active"))
            if not ativo:
                if user.pk == request.user.pk:
                    raise ValidationError({"detail": "Você não pode desativar o próprio acesso."})
                garantir_gestor_restante(user, desativar=True)
            user.is_active = ativo
            campos.append("is_active")
        for campo in ("first_name", "last_name"):
            if campo in data:
                setattr(user, campo, (data.get(campo) or "").strip())
                campos.append(campo)
        if campos:
            user.save(update_fields=campos)
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["post"], url_path="reenviar-convite")
    def reenviar_convite(self, request, pk=None):
        user = self.get_object()
        if not user.is_active:
            raise ValidationError({"detail": "Reative o usuário antes de reenviar o convite."})
        enviado = enviar_convite(user, connection.schema_name, nome_associacao(request), request.user)
        return Response({"email_enviado": enviado, "convite_pendente": convite_pendente(user)})

    @action(detail=False, methods=["get"])
    def perfis(self, request):
        return Response(
            {
                "perfis": [{"value": v, "label": l} for v, l in PERFIL_CHOICES],
                "modulos": [{"value": v, "label": l} for v, l in MODULOS],
                "matriz": MATRIZ,
                "sugestao_por_cargo": SUGESTAO_POR_CARGO,
            }
        )


def _schemas_para_busca(schema=None):
    Tenant = get_tenant_model()
    with schema_context("public"):
        qs = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
        if schema:
            qs = qs.filter(schema_name=schema)
        return list(qs.values_list("schema_name", "name"))


class EsqueciSenhaView(APIView):
    """POST {email, schema?} — sempre responde 200 para não revelar contas."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "senha_public"

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        schema = (request.data.get("schema") or "").strip() or None
        if email:
            for schema_name, nome in _schemas_para_busca(schema):
                with schema_context(schema_name):
                    user = User.objects.filter(email=email, is_active=True).first()
                    if user:
                        enviar_redefinicao(user, schema_name, nome or "Gesttora")
                        break
        return Response(
            {"detail": "Se o e-mail estiver cadastrado, você receberá um link para definir a senha."}
        )


class DefinirSenhaView(APIView):
    """GET valida o link; POST {schema, uid, token, password} define a senha e autentica."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "senha_public"

    def _resolver(self, schema, uid, token):
        if not schema or not uid or not token or not _schemas_para_busca(schema):
            return None
        with schema_context(schema):
            user = usuario_do_link(uid, token)
        return user if user and user.is_active else None

    def get(self, request):
        p = request.query_params
        schema = p.get("schema")
        user = self._resolver(schema, p.get("uid"), p.get("token"))
        if not user:
            return Response(
                {"detail": "Link inválido ou expirado. Peça um novo em “Esqueci a senha”."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"email": user.email, "first_name": user.first_name})

    def post(self, request):
        from .views import _issue_auth_response

        d = request.data
        schema = d.get("schema")
        user = self._resolver(schema, d.get("uid"), d.get("token"))
        if not user:
            return Response(
                {"detail": "Link inválido ou expirado. Peça um novo em “Esqueci a senha”."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password = d.get("password") or ""
        if len(password) < 8:
            return Response(
                {"detail": "A senha deve ter pelo menos 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with schema_context(schema):
            from django.utils import timezone

            user.set_password(password)
            user.last_login = timezone.now()
            user.save(update_fields=["password", "last_login"])
            payload = _issue_auth_response(user, schema)
        return Response(payload)
