"""Testes de Mensagens (diretoria ↔ associado)."""
import pytest
from django.core import mail
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from membros.models import Membro
from mensagens.models import Conversa
from mensagens.views import ConversaViewSet, MinhasConversasViewSet

factory = APIRequestFactory()


def _call(viewset_cls, actions, user, method, data=None, **kwargs):
    request = factory.get("/", data or {}) if method == "get" else getattr(factory, method)("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return viewset_cls.as_view(actions)(request, **kwargs)


@pytest.mark.django_db
class TestMensagens:
    def test_diretoria_inicia_associado_responde(self, test_tenant, board_user, member, django_capture_on_commit_callbacks):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            with django_capture_on_commit_callbacks(execute=True):
                resp = _call(
                    ConversaViewSet,
                    {"post": "create"},
                    board_user,
                    "post",
                    {"membros": [str(membro.id)], "assunto": "Anuidade 2027", "texto": "Sua anuidade vence dia 10."},
                )
            assert resp.status_code == 201, resp.data
            conversa_id = resp.data["id"]
            assert mail.outbox[-1].to == ["ana@teste.org"]
            assert f"/app/portal/mensagens/{conversa_id}" in mail.outbox[-1].body

            resp = _call(MinhasConversasViewSet, {"get": "resumo"}, user, "get")
            assert resp.data["nao_lidas"] == 1
            resp = _call(MinhasConversasViewSet, {"get": "retrieve"}, user, "get", pk=conversa_id)
            assert resp.data["mensagens"][0]["da_diretoria"] is True
            assert _call(MinhasConversasViewSet, {"get": "resumo"}, user, "get").data["nao_lidas"] == 0

            resp = _call(MinhasConversasViewSet, {"post": "responder_conversa"}, user, "post", {"texto": "Obrigada!"}, pk=conversa_id)
            assert resp.status_code == 201
            assert _call(ConversaViewSet, {"get": "resumo"}, board_user, "get").data["nao_lidas"] == 1
            resp = _call(ConversaViewSet, {"get": "list"}, board_user, "get")
            assert resp.data[0]["nao_lida"] is True and resp.data[0]["previa"] == "Obrigada!"

    def test_associado_inicia_com_a_secretaria(self, test_tenant, board_user, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _call(MinhasConversasViewSet, {"post": "create"}, user, "post", {"assunto": "Declaração", "texto": "Preciso de declaração."})
            assert resp.status_code == 201
            resp = _call(ConversaViewSet, {"get": "list"}, board_user, "get", {"nao_lidas": "true"})
            assert [c["assunto"] for c in resp.data] == ["Declaração"]

    def test_envio_para_todos_os_ativos(self, test_tenant, board_user, member):
        with schema_context(test_tenant.schema_name):
            Membro.objects.create(nome_completo="Bruno", email="bruno@x.org")
            Membro.objects.create(nome_completo="Inativo", email="inativo@x.org", ativo=False)
            resp = _call(
                ConversaViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"todos_ativos": True, "assunto": "Assembleia", "texto": "Convocação", "notificar": False},
            )
            assert resp.data == {"criadas": 2}
            assert Conversa.objects.count() == 2
            assert not mail.outbox

    def test_isolamento_entre_associados(self, test_tenant, board_user, member):
        with schema_context(test_tenant.schema_name):
            outro_user = User.objects.create_user(username="beto", email="beto@x.org", password="x", role=User.MEMBER, tenant=test_tenant)
            outro = Membro.objects.create(user=outro_user, nome_completo="Beto", email="beto@x.org")
            _, membro = member
            resp = _call(
                ConversaViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"membros": [str(membro.id)], "assunto": "Privado", "texto": "Só para Ana", "notificar": False},
            )
            conversa_id = resp.data["id"]
            assert _call(MinhasConversasViewSet, {"get": "retrieve"}, outro_user, "get", pk=conversa_id).status_code == 404
            assert _call(MinhasConversasViewSet, {"get": "list"}, outro_user, "get").data == []
            assert _call(ConversaViewSet, {"get": "list"}, outro_user, "get").status_code == 403
            assert outro.conversas.count() == 0

    def test_arquivar_e_resposta_reabre(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            resp = _call(
                ConversaViewSet, {"post": "create"}, board_user, "post",
                {"membros": [str(membro.id)], "assunto": "X", "texto": "Y", "notificar": False},
            )
            conversa_id = resp.data["id"]
            _call(ConversaViewSet, {"post": "arquivar"}, board_user, "post", {}, pk=conversa_id)
            assert _call(ConversaViewSet, {"get": "list"}, board_user, "get").data == []
            _call(MinhasConversasViewSet, {"post": "responder_conversa"}, user, "post", {"texto": "Oi"}, pk=conversa_id)
            assert Conversa.objects.get(pk=conversa_id).status == Conversa.ABERTA
