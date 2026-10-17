"""Testes do Suporte (chamados associação ↔ equipe Gesttora)."""
import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from support.models import Chamado, MensagemChamado
from support.views import ChamadoViewSet
from tenants.models import Tenant

factory = APIRequestFactory()


def _call(actions, user, method, data=None, multipart=False, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="multipart" if multipart else "json")
    force_authenticate(request, user=user)
    return ChamadoViewSet.as_view(actions)(request, **kwargs)


@pytest.fixture
def equipe(test_tenant):
    with schema_context(test_tenant.schema_name):
        return User.objects.create_user(
            username="gesttora", email="equipe@gesttora.com", password="x", role=User.SUPERADMIN, first_name="Lia"
        )


@pytest.fixture
def outra_associacao(db):
    tenant = Tenant.objects.create(name="Outra Associação", slug="outra", schema_name="outra")
    with schema_context("outra"):
        user = User.objects.create_user(
            username="outra", email="dir@outra.org", password="x", role=User.ASSOCIATION_ADMIN, tenant=tenant
        )
    return tenant, user


def _abrir(user, **extra):
    data = {"assunto": "Erro ao gerar anuidades", "categoria": "problema", "mensagem": "Aparece erro 500.", **extra}
    return _call({"post": "create"}, user, "post", data, multipart=True)


@pytest.mark.django_db
class TestChamados:
    def test_fluxo_completo(self, test_tenant, board_user, equipe, settings, tmp_path, django_capture_on_commit_callbacks):
        settings.SUPPORT_EMAIL = "suporte@gesttora.com"
        settings.MEDIA_ROOT = tmp_path
        with schema_context(test_tenant.schema_name):
            anexo = SimpleUploadedFile("print.png", b"\x89PNG fake", content_type="image/png")
            with django_capture_on_commit_callbacks(execute=True):
                resp = _abrir(board_user, anexos=[anexo])
            assert resp.status_code == 201, resp.data
            chamado_id = resp.data["id"]
            assert resp.data["associacao"] == "Associação Teste"
            assert resp.data["mensagens"][0]["anexos"][0]["nome"] == "print.png"
            assert mail.outbox[-1].to == ["suporte@gesttora.com"]

            with django_capture_on_commit_callbacks(execute=True):
                resp = _call({"post": "responder"}, equipe, "post", {"texto": "Pode enviar o CPF?"}, pk=chamado_id)
            assert resp.status_code == 201
            assert resp.data["status"] == Chamado.AGUARDANDO
            assert mail.outbox[-1].to == ["diretoria@teste.org"]

            _call({"post": "responder"}, equipe, "post", {"texto": "Bug no gerador", "interna": True}, pk=chamado_id)

            resp = _call({"get": "list"}, board_user, "get")
            assert resp.data[0]["nao_lido"] is True
            resp = _call({"get": "retrieve"}, board_user, "get", pk=chamado_id)
            textos = [m["texto"] for m in resp.data["mensagens"]]
            assert "Bug no gerador" not in textos
            assert Chamado.objects.get(pk=chamado_id).lido_pela_associacao

            resp = _call({"post": "responder"}, board_user, "post", {"texto": "Segue o CPF."}, pk=chamado_id)
            assert resp.data["status"] == Chamado.EM_ANDAMENTO

            resp = _call({"get": "retrieve"}, equipe, "get", pk=chamado_id)
            assert "Bug no gerador" in [m["texto"] for m in resp.data["mensagens"]]

    def test_isolamento_entre_associacoes(self, test_tenant, board_user, equipe, outra_associacao):
        _, user_outra = outra_associacao
        with schema_context(test_tenant.schema_name):
            chamado_id = _abrir(board_user).data["id"]
        with schema_context("outra"):
            _abrir(user_outra, assunto="Dúvida")
            resp = _call({"get": "list"}, user_outra, "get")
            assert [c["assunto"] for c in resp.data] == ["Dúvida"]
            resp = _call({"get": "retrieve"}, user_outra, "get", pk=chamado_id)
            assert resp.status_code == 404
        with schema_context(test_tenant.schema_name):
            resp = _call({"get": "list"}, equipe, "get")
            assert len(resp.data) == 2
            resp = _call({"get": "list"}, equipe, "get", {"tenant": test_tenant.id})
            assert len(resp.data) == 1

    def test_permissoes_de_status(self, test_tenant, board_user, equipe, member):
        user_membro, _ = member
        with schema_context(test_tenant.schema_name):
            chamado_id = _abrir(board_user).data["id"]
            assert _call({"get": "list"}, user_membro, "get").status_code == 403
            resp = _call({"post": "alterar_status"}, board_user, "post", {"status": "resolvido"}, pk=chamado_id)
            assert resp.status_code == 403
            resp = _call({"post": "alterar_status"}, board_user, "post", {"status": "fechado"}, pk=chamado_id)
            assert resp.data["status"] == "fechado"
            assert MensagemChamado.objects.filter(chamado_id=chamado_id, texto__contains="Fechado").exists()
            resp = _call({"post": "responder"}, board_user, "post", {"texto": "Voltou a acontecer"}, pk=chamado_id)
            assert resp.data["status"] == "aberto"
            resp = _call(
                {"post": "alterar_status"}, equipe, "post", {"status": "em_andamento", "prioridade": "alta"}, pk=chamado_id
            )
            assert resp.data["prioridade"] == "alta" and resp.data["status"] == "em_andamento"
            assert _abrir(equipe).status_code == 403

    def test_anexo_invalido(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            exe = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
            resp = _abrir(board_user, anexos=[exe])
            assert resp.status_code == 400
            assert not Chamado.objects.exists()

    def test_resumo(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            _abrir(board_user)
            resp = _call({"get": "resumo"}, board_user, "get")
            assert resp.data["por_status"]["aberto"] == 1
            assert resp.data["nao_lidos"] == 0
