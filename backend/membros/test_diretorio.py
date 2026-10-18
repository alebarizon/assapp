"""Diretório público: opt-in no portal, filtro de filiação, busca e chave do site."""
from datetime import date

import pytest
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from membros.models import Filiacao, FiliacaoStatus, Membro
from membros.views import DiretorioPublicoView, MeuMembroView
from website.models import WebsiteConfig

factory = APIRequestFactory()


def _associado(nome, email, instituicao="", status=FiliacaoStatus.ATIVA, publico=True):
    membro = Membro.objects.create(
        nome_completo=nome, email=email, instituicao=instituicao, diretorio_publico=publico
    )
    Filiacao.objects.create(membro=membro, data_inicio=date(2021, 3, 1), status=status)
    return membro


def _diretorio(schema, **params):
    query = "&".join(f"{k}={v}" for k, v in {"schema": schema, **params}.items())
    return DiretorioPublicoView.as_view()(factory.get(f"/?{query}"))


@pytest.mark.django_db
class TestDiretorio:
    def test_opt_in_pelo_portal(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            Filiacao.objects.create(membro=membro, data_inicio=date(2024, 1, 1))
            req = factory.patch("/", {
                "diretorio_publico": True, "mini_bio": "Pesquisa cibercultura.",
                "instituicao": "UFBA", "email": "outro@x.org",
            }, format="json")
            force_authenticate(req, user=user)
            resp = MeuMembroView.as_view()(req)
            assert resp.status_code == 200, resp.data
            membro.refresh_from_db()
            assert membro.diretorio_publico and membro.diretorio_aceito_em
            assert membro.email != "outro@x.org"

            req = factory.patch("/", {"diretorio_publico": False}, format="json")
            force_authenticate(req, user=user)
            MeuMembroView.as_view()(req)
            membro.refresh_from_db()
            assert not membro.diretorio_publico and membro.diretorio_aceito_em is None

    def test_listagem_publica(self, test_tenant):
        schema = test_tenant.schema_name
        with schema_context(schema):
            _associado("Ana Souza", "ana@x.org", "UFBA")
            _associado("Bruno Lima", "bruno@x.org", "USP")
            _associado("Carla Dias", "carla@x.org", "UFBA", publico=False)
            _associado("Davi Ex", "davi@x.org", "UFBA", status=FiliacaoStatus.CANCELADA)

            assert _diretorio(schema).status_code == 404
            WebsiteConfig.objects.create(is_published=True, diretorio_ativo=True)

            r = _diretorio(schema).data
            assert [m["nome"] for m in r["resultados"]] == ["Ana Souza", "Bruno Lima"]
            assert r["instituicoes"][0] == {"nome": "UFBA", "total": 1}
            assert "email" not in r["resultados"][0] and r["resultados"][0]["membro_desde"] == 2021

            assert [m["nome"] for m in _diretorio(schema, q="usp").data["resultados"]] == ["Bruno Lima"]
            assert _diretorio(schema, instituicao="UFBA").data["total"] == 1
