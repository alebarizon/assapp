"""Perfis de acesso da equipe, gestão de usuários e links de senha."""
from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail
from django.core.cache import cache
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.access import LEITURA, TOTAL, modulos_do_user, nivel_acesso
from accounts.equipe_views import DefinirSenhaView, EquipeViewSet, EsqueciSenhaView
from accounts.models import User
from accounts.serializers import UserSerializer
from contatos.views import ContatoViewSet
from finance.views import TransactionViewSet
from membros.views import AnuidadeViewSet, MembroViewSet
from memoria.views import ContextoHistoricoViewSet

factory = APIRequestFactory()


def _call(view_cls, actions, user, method="get", data=None, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return view_cls.as_view(actions)(request, **kwargs)


def _staff(tenant, email, perfis):
    with schema_context(tenant.schema_name):
        return User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password="pass12345",
            role=User.BOARD_MEMBER,
            perfis=perfis,
            tenant=tenant,
        )


def _link_params(body):
    url = next(p for p in body.split() if "/definir-senha?" in p)
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


@pytest.fixture(autouse=True)
def _limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestMatriz:
    def test_conta_antiga_sem_perfis_vira_gestor(self, board_user):
        assert board_user.perfis == []
        assert nivel_acesso(board_user, "usuarios") == TOTAL

    def test_administrativo(self, test_tenant):
        user = _staff(test_tenant, "adm@teste.org", ["administrativo"])
        assert nivel_acesso(user, "membros") == TOTAL
        assert nivel_acesso(user, "memoria") == LEITURA
        assert nivel_acesso(user, "financeiro") is None
        assert "usuarios" not in modulos_do_user(user)

    def test_perfis_somam_o_maior_nivel(self, test_tenant):
        user = _staff(test_tenant, "dupla@teste.org", ["diretoria", "financeiro"])
        assert nivel_acesso(user, "financeiro") == TOTAL
        assert nivel_acesso(user, "contatos") == TOTAL

    def test_associado_sem_modulos(self, member):
        user, _ = member
        assert modulos_do_user(user) == {}

    def test_me_expoe_perfis_e_modulos(self, test_tenant):
        user = _staff(test_tenant, "fin@teste.org", ["financeiro"])
        data = UserSerializer(user).data
        assert data["perfis"] == ["financeiro"]
        assert data["modulos"]["membros"] == LEITURA


@pytest.mark.django_db
class TestPermissoesPorModulo:
    def test_financeiro(self, test_tenant):
        user = _staff(test_tenant, "fin@teste.org", ["financeiro"])
        with schema_context("teste"):
            assert _call(TransactionViewSet, {"get": "list"}, user).status_code == 200
            assert _call(MembroViewSet, {"get": "list"}, user).status_code == 200
            assert _call(MembroViewSet, {"post": "create"}, user, "post", {}).status_code == 403
            assert _call(AnuidadeViewSet, {"get": "list"}, user).status_code == 200
            assert _call(ContatoViewSet, {"get": "list"}, user).status_code == 403

    def test_administrativo(self, test_tenant):
        user = _staff(test_tenant, "adm@teste.org", ["administrativo"])
        with schema_context("teste"):
            assert _call(ContatoViewSet, {"get": "list"}, user).status_code == 200
            assert _call(TransactionViewSet, {"get": "list"}, user).status_code == 403
            assert _call(ContextoHistoricoViewSet, {"get": "list"}, user).status_code == 200
            assert (
                _call(ContextoHistoricoViewSet, {"post": "create"}, user, "post", {}).status_code
                == 403
            )

    def test_diretoria_le_financeiro_mas_nao_gerencia_equipe(self, test_tenant):
        user = _staff(test_tenant, "dir@teste.org", ["diretoria"])
        with schema_context("teste"):
            assert _call(TransactionViewSet, {"get": "list"}, user).status_code == 200
            assert _call(TransactionViewSet, {"post": "create"}, user, "post", {}).status_code == 403
            assert _call(EquipeViewSet, {"get": "list"}, user).status_code == 403

    def test_associado_bloqueado(self, member):
        user, _ = member
        with schema_context("teste"):
            assert _call(EquipeViewSet, {"get": "list"}, user).status_code == 403
            assert _call(MembroViewSet, {"get": "list"}, user).status_code == 403


@pytest.mark.django_db
class TestEquipe:
    def test_convite_e_definicao_de_senha(self, board_user, settings):
        settings.FRONTEND_URL = "https://app.exemplo.org"
        with schema_context("teste"):
            resp = _call(
                EquipeViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"email": "Nova@Teste.org", "first_name": "Nova", "perfis": ["administrativo", "financeiro"]},
            )
            assert resp.status_code == 201, resp.data
            assert resp.data["email_enviado"] is True
            assert resp.data["convite_pendente"] is True
            novo = User.objects.get(email="nova@teste.org")
            assert novo.role == User.BOARD_MEMBER
            assert novo.perfis == ["administrativo", "financeiro"]
            assert not novo.has_usable_password()

        assert len(mail.outbox) == 1
        params = _link_params(mail.outbox[0].body)
        assert params["schema"] == "teste"

        check = DefinirSenhaView.as_view()(factory.get("/", params))
        assert check.status_code == 200
        assert check.data["email"] == "nova@teste.org"

        resp = DefinirSenhaView.as_view()(
            factory.post("/", {**params, "password": "senha-nova-1"}, format="json")
        )
        assert resp.status_code == 200, resp.data
        assert resp.data["access"]
        assert resp.data["user"]["perfis"] == ["administrativo", "financeiro"]

        with schema_context("teste"):
            assert User.objects.get(email="nova@teste.org").check_password("senha-nova-1")

        reuso = DefinirSenhaView.as_view()(
            factory.post("/", {**params, "password": "outra-senha-2"}, format="json")
        )
        assert reuso.status_code == 400

    def test_convite_promove_associado(self, board_user, member):
        user, _ = member
        with schema_context("teste"):
            resp = _call(
                EquipeViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"email": "ana@teste.org", "perfis": ["administrativo"]},
            )
            assert resp.status_code == 201
            user.refresh_from_db()
            assert user.role == User.BOARD_MEMBER
            assert user.check_password("pass12345")

    def test_convite_duplicado_e_perfil_invalido(self, board_user):
        with schema_context("teste"):
            dup = _call(
                EquipeViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"email": "diretoria@teste.org", "perfis": ["diretoria"]},
            )
            assert dup.status_code == 400
            invalido = _call(
                EquipeViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"email": "x@teste.org", "perfis": ["presidente"]},
            )
            assert invalido.status_code == 400
            vazio = _call(
                EquipeViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"email": "x@teste.org", "perfis": []},
            )
            assert vazio.status_code == 400

    def test_nao_remove_ultimo_gestor(self, board_user, test_tenant):
        pk = str(board_user.pk)
        with schema_context("teste"):
            resp = _call(
                EquipeViewSet,
                {"patch": "partial_update"},
                board_user,
                "patch",
                {"perfis": ["diretoria"]},
                pk=pk,
            )
            assert resp.status_code == 400
            proprio = _call(
                EquipeViewSet,
                {"patch": "partial_update"},
                board_user,
                "patch",
                {"is_active": False},
                pk=pk,
            )
            assert proprio.status_code == 400

        _staff(test_tenant, "gestor2@teste.org", ["gestor"])
        with schema_context("teste"):
            resp = _call(
                EquipeViewSet,
                {"patch": "partial_update"},
                board_user,
                "patch",
                {"perfis": ["diretoria"]},
                pk=pk,
            )
            assert resp.status_code == 200
            assert resp.data["perfis"] == ["diretoria"]

    def test_desativar_e_listar(self, board_user, test_tenant):
        outro = _staff(test_tenant, "fin@teste.org", ["financeiro"])
        with schema_context("teste"):
            resp = _call(
                EquipeViewSet,
                {"patch": "partial_update"},
                board_user,
                "patch",
                {"is_active": False},
                pk=str(outro.pk),
            )
            assert resp.status_code == 200
            assert resp.data["is_active"] is False
            lista = _call(EquipeViewSet, {"get": "list"}, board_user)
            emails = [u["email"] for u in lista.data]
            assert emails == ["diretoria@teste.org", "fin@teste.org"]


@pytest.mark.django_db
class TestEsqueciSenha:
    def test_envia_link_para_conta_existente(self, board_user):
        resp = EsqueciSenhaView.as_view()(
            factory.post("/", {"email": "DIRETORIA@teste.org"}, format="json")
        )
        assert resp.status_code == 200
        assert len(mail.outbox) == 1
        params = _link_params(mail.outbox[0].body)
        assert params["schema"] == "teste"

    def test_email_desconhecido_responde_igual(self, test_tenant):
        resp = EsqueciSenhaView.as_view()(
            factory.post("/", {"email": "ninguem@teste.org"}, format="json")
        )
        assert resp.status_code == 200
        assert mail.outbox == []
