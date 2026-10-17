"""Testes do módulo Contatos."""
import pytest
from django.core import mail
from django.core.cache import cache
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from contatos.models import Contato, Etiqueta, Nota
from contatos.views import ContatoPublicoView, ContatoViewSet, EtiquetaViewSet
from membros.models import Filiacao, Membro
from website.models import WebsiteConfig

factory = APIRequestFactory()


def _call(viewset_cls, actions, user, method, data=None, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return viewset_cls.as_view(actions)(request, **kwargs)


def _public(data):
    request = factory.post("/?schema=teste", data, format="json")
    return ContatoPublicoView.as_view()(request)


PAYLOAD = {
    "nome": "Carlos Souza",
    "email": "Carlos@Exemplo.org",
    "telefone": "11 99999-0000",
    "assunto": "filiacao",
    "mensagem": "Gostaria de saber como me associar.",
    "consentimento_lgpd": True,
}


@pytest.fixture(autouse=True)
def _limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestPublico:
    def test_cria_contato_e_notifica(self, test_tenant, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        with schema_context(test_tenant.schema_name):
            WebsiteConfig.objects.create(contact_email="diretoria@assoc.org")
        resp = _public(PAYLOAD)
        assert resp.status_code == 201, resp.data
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.get()
            assert contato.email == "carlos@exemplo.org"
            assert contato.etapa == Contato.NOVO
            assert contato.origem == Contato.SITE_CONTATO
            assert contato.consentimento_lgpd
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["diretoria@assoc.org"]
        assert mail.outbox[0].reply_to == ["carlos@exemplo.org"]

    def test_exige_consentimento(self, test_tenant):
        resp = _public({**PAYLOAD, "consentimento_lgpd": False})
        assert resp.status_code == 400
        assert "consentimento_lgpd" in resp.data

    def test_honeypot_descarta_sem_erro(self, test_tenant):
        resp = _public({**PAYLOAD, "website": "http://spam"})
        assert resp.status_code == 201
        with schema_context(test_tenant.schema_name):
            assert not Contato.objects.exists()

    def test_reenvio_vira_nota_no_contato_aberto(self, test_tenant):
        _public(PAYLOAD)
        _public({**PAYLOAD, "mensagem": "Ainda aguardo retorno.", "instituicao": "USP"})
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.get()
            assert contato.instituicao == "USP"
            nota = contato.notas.get(tipo=Nota.MENSAGEM)
            assert "Ainda aguardo retorno." in nota.texto

    def test_reenvio_apos_arquivado_cria_novo(self, test_tenant):
        _public(PAYLOAD)
        with schema_context(test_tenant.schema_name):
            Contato.objects.update(etapa=Contato.ARQUIVADO)
        _public(PAYLOAD)
        with schema_context(test_tenant.schema_name):
            assert Contato.objects.count() == 2

    def test_email_de_associado_e_vinculado(self, test_tenant, member):
        _, membro = member
        resp = _public({**PAYLOAD, "email": membro.email})
        assert resp.status_code == 201
        with schema_context(test_tenant.schema_name):
            assert Contato.objects.get().membro_id == membro.id


@pytest.mark.django_db
class TestDiretoria:
    def test_associado_nao_acessa(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _call(ContatoViewSet, {"get": "list"}, user, "get")
            assert resp.status_code == 403

    def test_cadastro_manual_filtros_e_resumo(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            tag = Etiqueta.objects.create(nome="Congresso 2026")
            resp = _call(
                ContatoViewSet,
                {"post": "create"},
                board_user,
                "post",
                {"nome": "Beatriz", "email": "bia@x.org", "etiqueta_ids": [tag.id]},
            )
            assert resp.status_code == 201, resp.data
            assert resp.data["origem"] == Contato.MANUAL
            Contato.objects.create(nome="Outro", email="o@x.org", etapa=Contato.ARQUIVADO)

            resp = _call(ContatoViewSet, {"get": "list"}, board_user, "get", {"etiqueta": tag.id})
            assert [c["nome"] for c in resp.data] == ["Beatriz"]
            resp = _call(ContatoViewSet, {"get": "list"}, board_user, "get", {"abertos": "true"})
            assert len(resp.data) == 1
            resp = _call(ContatoViewSet, {"get": "list"}, board_user, "get", {"search": "outro"})
            assert len(resp.data) == 1

            resp = _call(ContatoViewSet, {"get": "resumo"}, board_user, "get")
            assert resp.data["novo"] == 1 and resp.data["arquivado"] == 1

    def test_mudar_etapa_registra_historico_e_notas(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="Davi", email="davi@x.org")
            resp = _call(
                ContatoViewSet,
                {"patch": "partial_update"},
                board_user,
                "patch",
                {"etapa": Contato.EM_ATENDIMENTO},
                pk=str(contato.pk),
            )
            assert resp.status_code == 200, resp.data
            assert contato.notas.filter(tipo=Nota.SISTEMA, texto__contains="Em atendimento").exists()

            resp = _call(
                ContatoViewSet,
                {"post": "notas"},
                board_user,
                "post",
                {"texto": "Liguei, pediu proposta."},
                pk=str(contato.pk),
            )
            assert resp.status_code == 201
            resp = _call(ContatoViewSet, {"get": "notas"}, board_user, "get", pk=str(contato.pk))
            assert resp.data[0]["texto"] == "Liguei, pediu proposta."

    def test_converter_cria_membro_com_filiacao(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="Elisa Prado", email="elisa@x.org", consentimento_lgpd=True)
            resp = _call(
                ContatoViewSet,
                {"post": "converter"},
                board_user,
                "post",
                {"tipo_filiacao": "estudante"},
                pk=str(contato.pk),
            )
            assert resp.status_code == 200, resp.data
            assert resp.data["membro_criado"] is True
            membro = Membro.objects.get(email="elisa@x.org")
            assert membro.consentimento_lgpd
            assert Filiacao.objects.filter(membro=membro, tipo="estudante").exists()
            contato.refresh_from_db()
            assert contato.etapa == Contato.CONVERTIDO and contato.membro_id == membro.id

    def test_converter_vincula_membro_existente(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="Ana", email=membro.email.upper())
            resp = _call(ContatoViewSet, {"post": "converter"}, board_user, "post", {}, pk=str(contato.pk))
            assert resp.data["membro_criado"] is False
            assert resp.data["membro_id"] == str(membro.id)
            assert Membro.objects.count() == 1

    def test_converter_tipo_invalido(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            contato = Contato.objects.create(nome="F", email="f@x.org")
            resp = _call(
                ContatoViewSet, {"post": "converter"}, board_user, "post", {"tipo_filiacao": "vip"}, pk=str(contato.pk)
            )
            assert resp.status_code == 400

    def test_etiqueta_nome_duplicado(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            Etiqueta.objects.create(nome="Imprensa")
            resp = _call(EtiquetaViewSet, {"post": "create"}, board_user, "post", {"nome": "imprensa"})
            assert resp.status_code == 400
