"""Integrações: catálogo, webhooks de saída (assinatura, retentativas, bloqueio de rede interna) e permissões."""
import hashlib
import hmac
import json
import socket
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from integracoes.models import EntregaWebhook, WebhookSaida
from integracoes.services import ESPERAS_MINUTOS, UrlBloqueada, processar_fila, validar_url
from integracoes.views import CatalogoView, WebhookSaidaViewSet
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus, Membro
from membros.services import registrar_pagamento
from payments.models import ConfiguracaoPagamento

User = get_user_model()
factory = APIRequestFactory()

IP_PUBLICO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
IP_INTERNO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]


@pytest.fixture
def dns_publico():
    with mock.patch("integracoes.services.socket.getaddrinfo", return_value=IP_PUBLICO):
        yield


def _resposta(status=200, texto="ok"):
    r = mock.Mock(status_code=status, text=texto)
    return r


def _webhook(**kw):
    return WebhookSaida.objects.create(
        url=kw.pop("url", "https://hooks.exemplo.org/gesttora"),
        eventos=kw.pop("eventos", ["membro.criado", "anuidade.paga"]),
        **kw,
    )


def _staff(tenant, username, perfis):
    return User.objects.create_user(
        username=username, email=f"{username}@teste.org", password="pass12345",
        role=User.BOARD_MEMBER, perfis=perfis, tenant=tenant,
    )


@pytest.mark.django_db
class TestUrl:
    def test_aceita_https_publico(self, dns_publico):
        validar_url("https://hooks.exemplo.org/x")

    @pytest.mark.parametrize("url", ["http://hooks.exemplo.org/x", "ftp://x.org", "https://"])
    def test_recusa_esquema_ou_host(self, url, dns_publico):
        with pytest.raises(UrlBloqueada):
            validar_url(url)

    def test_recusa_rede_interna(self):
        with mock.patch("integracoes.services.socket.getaddrinfo", return_value=IP_INTERNO):
            with pytest.raises(UrlBloqueada):
                validar_url("https://interno.exemplo.org/")
        loopback = [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 443, 0, 0))]
        with mock.patch("integracoes.services.socket.getaddrinfo", return_value=loopback):
            with pytest.raises(UrlBloqueada):
                validar_url("https://localhost/")


@pytest.mark.django_db
class TestEntregas:
    def test_evento_gera_entrega_assinada(self, test_tenant, dns_publico):
        with schema_context(test_tenant.schema_name):
            webhook = _webhook()
            _webhook(eventos=["inscricao.criada"])
            Membro.objects.create(nome_completo="Ana Souza", email="ana@teste.org")
            assert EntregaWebhook.objects.count() == 1

            with mock.patch("integracoes.services.requests.post", return_value=_resposta()) as post:
                assert processar_fila()["entregues"] == 1
            corpo = post.call_args.kwargs["data"]
            headers = post.call_args.kwargs["headers"]
            assert post.call_args.kwargs["allow_redirects"] is False
            esperado = hmac.new(
                webhook.segredo.encode(), headers["X-Gesttora-Timestamp"].encode() + b"." + corpo, hashlib.sha256
            ).hexdigest()
            assert headers["X-Gesttora-Assinatura"] == f"sha256={esperado}"
            payload = json.loads(corpo)
            assert payload["evento"] == "membro.criado"
            assert payload["associacao"] == test_tenant.schema_name
            assert payload["dados"]["email"] == "ana@teste.org"
            assert EntregaWebhook.objects.get().status == EntregaWebhook.ENTREGUE

    def test_anuidade_paga_dispara(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            _webhook(eventos=["anuidade.paga"])
            membro = Membro.objects.create(nome_completo="Ana Souza", email="ana@teste.org")
            filiacao = Filiacao.objects.create(membro=membro, data_inicio=date(2026, 1, 1), status=FiliacaoStatus.ATIVA)
            anuidade = Anuidade.objects.create(
                filiacao=filiacao, ano_referencia=2026, valor=Decimal("150"),
                vencimento=date(2026, 3, 31), status=AnuidadeStatus.PENDENTE,
            )
            registrar_pagamento(anuidade)
            registrar_pagamento(anuidade)
            entrega = EntregaWebhook.objects.get()
            assert entrega.evento == "anuidade.paga"
            assert entrega.dados["valor"] == "150.00"
            assert entrega.dados["membro"]["email"] == "ana@teste.org"

    def test_falha_reagenda_e_depois_desiste(self, test_tenant, dns_publico):
        with schema_context(test_tenant.schema_name):
            webhook = _webhook()
            Membro.objects.create(nome_completo="Ana Souza", email="ana@teste.org")
            entrega = EntregaWebhook.objects.get()
            with mock.patch("integracoes.services.requests.post", return_value=_resposta(500, "erro")):
                for _ in ESPERAS_MINUTOS:
                    EntregaWebhook.objects.filter(pk=entrega.pk).update(proxima_tentativa=timezone.now())
                    assert processar_fila()["falhas"] == 1
                entrega.refresh_from_db()
                assert entrega.status == EntregaWebhook.PENDENTE
                assert entrega.resposta_status == 500

                EntregaWebhook.objects.filter(pk=entrega.pk).update(proxima_tentativa=timezone.now())
                processar_fila()
            entrega.refresh_from_db()
            webhook.refresh_from_db()
            assert entrega.status == EntregaWebhook.DESISTIU
            assert webhook.falhas_seguidas == len(ESPERAS_MINUTOS) + 1

    def test_erro_de_rede_e_webhook_inativo(self, test_tenant, dns_publico):
        with schema_context(test_tenant.schema_name):
            webhook = _webhook()
            Membro.objects.create(nome_completo="Ana Souza", email="ana@teste.org")
            with mock.patch("integracoes.services.requests.post", side_effect=requests.Timeout("lento")):
                processar_fila()
            entrega = EntregaWebhook.objects.get()
            assert "Timeout" in entrega.ultimo_erro
            assert entrega.proxima_tentativa > timezone.now()

            webhook.ativo = False
            webhook.save()
            EntregaWebhook.objects.update(proxima_tentativa=timezone.now() - timedelta(seconds=1))
            assert processar_fila()["processados"] == 0

    def test_dns_que_muda_para_rede_interna_e_bloqueado_na_entrega(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            _webhook()
            Membro.objects.create(nome_completo="Ana Souza", email="ana@teste.org")
            with mock.patch("integracoes.services.socket.getaddrinfo", return_value=IP_INTERNO), mock.patch(
                "integracoes.services.requests.post"
            ) as post:
                processar_fila()
            post.assert_not_called()
            assert "interna" in EntregaWebhook.objects.get().ultimo_erro


@pytest.mark.django_db
class TestApi:
    def _req(self, user, method="get", data=None):
        request = getattr(factory, method)("/", data or {}, format="json")
        force_authenticate(request, user=user)
        return request

    def test_gestor_cria_testa_e_ve_entregas(self, test_tenant, board_user, dns_publico):
        with schema_context(test_tenant.schema_name):
            criar = WebhookSaidaViewSet.as_view({"post": "create"})
            r = criar(self._req(board_user, "post", {"url": "https://hooks.exemplo.org/a", "eventos": ["membro.criado"]}))
            assert r.status_code == 201, r.data
            assert r.data["segredo"].startswith("whsec_")
            pk = r.data["id"]

            r = criar(self._req(board_user, "post", {"url": "https://hooks.exemplo.org/a", "eventos": ["x.y"]}))
            assert r.status_code == 400

            with mock.patch("integracoes.services.requests.post", return_value=_resposta(404, "nada")):
                r = WebhookSaidaViewSet.as_view({"post": "testar"})(self._req(board_user, "post"), pk=pk)
            assert r.data["status"] == EntregaWebhook.DESISTIU
            assert r.data["resposta_status"] == 404

            r = WebhookSaidaViewSet.as_view({"get": "entregas"})(self._req(board_user), pk=pk)
            assert [e["evento"] for e in r.data] == ["ping"]

            antigo = WebhookSaida.objects.get(pk=pk).segredo
            r = WebhookSaidaViewSet.as_view({"post": "regenerar_segredo"})(self._req(board_user, "post"), pk=pk)
            assert r.data["segredo"] != antigo

    def test_url_interna_recusada_na_criacao(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            with mock.patch("integracoes.services.socket.getaddrinfo", return_value=IP_INTERNO):
                r = WebhookSaidaViewSet.as_view({"post": "create"})(
                    self._req(board_user, "post", {"url": "https://interno.exemplo.org/", "eventos": ["membro.criado"]})
                )
            assert r.status_code == 400
            assert "url" in r.data

    def test_catalogo_mostra_situacao_do_gateway(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            config = ConfiguracaoPagamento.atual()
            config.provedor = ConfiguracaoPagamento.PAGBANK
            config.ativo = True
            config.save()
            r = CatalogoView.as_view()(self._req(board_user))
            situacao = {c["slug"]: c["situacao"] for c in r.data["conectores"]}
            assert situacao["pagbank"] == "ativo"
            assert situacao["asaas"] == "disponivel"
            assert situacao["webhooks"] == "disponivel"
            assert situacao["orcid"] == "em_breve"
            assert r.data["pode_configurar_pagamento"] is True

    def test_so_gestor_acessa(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            diretoria = _staff(test_tenant, "dir", ["diretoria"])
            financeiro = _staff(test_tenant, "fin", ["financeiro"])
            for user in (diretoria, financeiro):
                assert CatalogoView.as_view()(self._req(user)).status_code == 403
                assert WebhookSaidaViewSet.as_view({"get": "list"})(self._req(user)).status_code == 403
