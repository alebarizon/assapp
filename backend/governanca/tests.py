"""Assembleias e votações: censo, voto secreto, apuração, quórum, ata e memória."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from governanca.models import Assembleia, Cedula, Votacao
from governanca.views import AssembleiaViewSet, MinhaGovernancaView, MinhaPresencaView, VotacaoViewSet, VotarView
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus, Membro
from memoria.models import ContextoHistorico

factory = APIRequestFactory()


def _req(method, user, data=None, path="/"):
    request = getattr(factory, method)(path, data or {}, format="json")
    force_authenticate(request, user=user)
    return request


def _staff(viewset, actions, user, method="post", data=None, **kwargs):
    return viewset.as_view(actions)(_req(method, user, data), **kwargs)


def _filiar(membro, status=FiliacaoStatus.ATIVA):
    return Filiacao.objects.create(membro=membro, data_inicio=date(2025, 1, 1), status=status)


def _associado(nome, email, em_dia=True):
    membro = Membro.objects.create(nome_completo=nome, email=email)
    filiacao = _filiar(membro)
    if not em_dia:
        Anuidade.objects.create(
            filiacao=filiacao, ano_referencia=2026, valor=Decimal("100"),
            vencimento=date.today() - timedelta(days=10), status=AnuidadeStatus.PENDENTE,
        )
    return membro


def _criar_votacao(user, **dados):
    payload = {"titulo": "Eleição da diretoria", "tipo": "eleicao", **dados}
    resp = _staff(VotacaoViewSet, {"post": "create"}, user, data=payload)
    assert resp.status_code == 201, resp.data
    return Votacao.objects.get(pk=resp.data["id"])


@pytest.mark.django_db
class TestVotacao:
    def test_fluxo_eleicao_secreta(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            outro = _associado("Bruno Lima", "bruno@teste.org")
            _associado("Carla Dias", "carla@teste.org", em_dia=False)

            v = _criar_votacao(
                board_user,
                opcoes=[
                    {"titulo": "Chapa Ciência Aberta", "integrantes": [{"nome": "Ana", "cargo": "Presidente"}]},
                    {"titulo": "Chapa Renovação"},
                ],
            )
            aberta = _staff(VotacaoViewSet, {"post": "abrir"}, board_user, pk=str(v.pk))
            assert aberta.status_code == 200, aberta.data
            assert aberta.data["eleitores"] == 2  # inadimplente fica fora do censo
            chapa_a, chapa_b = v.opcoes.all()

            portal = MinhaGovernancaView.as_view()(_req("get", user)).data
            assert portal["votacoes"][0]["pode_votar"] is True

            voto = VotarView.as_view()(_req("post", user, {"opcoes": [chapa_a.id]}), pk=v.pk)
            assert voto.status_code == 201 and len(voto.data["comprovante"]) == 12
            again = VotarView.as_view()(_req("post", user, {"opcoes": [chapa_b.id]}), pk=v.pk)
            assert again.status_code == 400

            from governanca.services import votar
            v.refresh_from_db()
            votar(v, outro, [chapa_a.id])
            assert all(c.eleitor_id is None for c in Cedula.objects.filter(votacao=v))

            parcial = _staff(VotacaoViewSet, {"get": "retrieve"}, board_user, method="get", pk=str(v.pk))
            assert parcial.data["resultado"] is None

            fim = _staff(VotacaoViewSet, {"post": "encerrar"}, board_user, pk=str(v.pk))
            r = fim.data["resultado"]
            assert r["votantes"] == 2 and r["vencedora"] == chapa_a.id and r["participacao_pct"] == 100.0
            memoria = ContextoHistorico.objects.get(entidade_tipo="votacao", entidade_id=v.id)
            assert memoria.tipo == "decisao" and "Chapa Ciência Aberta" in memoria.decisao

            fechada = VotarView.as_view()(_req("post", user, {"opcoes": []}), pk=v.pk)
            assert fechada.status_code == 400

    def test_deliberacao_cria_opcoes_e_aceita_branco(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            v = _criar_votacao(board_user, titulo="Reforma do estatuto", tipo="deliberacao", censo="ativos")
            aberta = _staff(VotacaoViewSet, {"post": "abrir"}, board_user, pk=str(v.pk))
            assert aberta.status_code == 200, aberta.data
            assert list(v.opcoes.values_list("titulo", flat=True)) == ["Aprovo", "Rejeito", "Abstenção"]
            VotarView.as_view()(_req("post", user, {"opcoes": []}), pk=v.pk)
            r = _staff(VotacaoViewSet, {"post": "encerrar"}, board_user, pk=str(v.pk)).data["resultado"]
            assert r["brancos"] == 1 and r["vencedora"] is None

    def test_limite_de_escolhas_e_censo_vazio(self, test_tenant, board_user, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            vazia = _criar_votacao(board_user, opcoes=[{"titulo": "A"}, {"titulo": "B"}])
            assert _staff(VotacaoViewSet, {"post": "abrir"}, board_user, pk=str(vazia.pk)).status_code == 400

            _filiar(membro)
            v = _criar_votacao(board_user, opcoes=[{"titulo": "A"}, {"titulo": "B"}], permite_branco=False)
            _staff(VotacaoViewSet, {"post": "abrir"}, board_user, pk=str(v.pk))
            ids = list(v.opcoes.values_list("id", flat=True))
            assert VotarView.as_view()(_req("post", user, {"opcoes": ids}), pk=v.pk).status_code == 400
            assert VotarView.as_view()(_req("post", user, {"opcoes": []}), pk=v.pk).status_code == 400

    def test_associado_nao_administra(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _staff(VotacaoViewSet, {"post": "create"}, user, data={"titulo": "X"})
            assert resp.status_code == 403


@pytest.mark.django_db
class TestAssembleia:
    def test_convocacao_presenca_quorum_e_ata(self, test_tenant, board_user, member, mailoutbox):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            _filiar(membro)
            _associado("Bruno Lima", "bruno@teste.org")
            devedor = _associado("Carla Dias", "carla@teste.org", em_dia=False)
            criada = _staff(
                AssembleiaViewSet, {"post": "create"}, board_user,
                data={
                    "titulo": "AGO 2026", "data_hora": (timezone.now() + timedelta(days=15)).isoformat(),
                    "modalidade": "hibrida", "local": "Auditório", "pauta": ["Prestação de contas", "Eleição"],
                    "quorum_minimo": 50,
                },
            )
            assert criada.status_code == 201, criada.data
            a = Assembleia.objects.get()

            conv = _staff(AssembleiaViewSet, {"post": "convocar"}, board_user, pk=str(a.pk))
            assert conv.data["emails_enviados"] == 3 and len(mailoutbox) == 3
            assert all(len(m.to) == 1 for m in mailoutbox)

            presenca_cedo = MinhaPresencaView.as_view()(_req("post", user), pk=a.pk)
            assert presenca_cedo.status_code == 400
            _staff(AssembleiaViewSet, {"post": "iniciar"}, board_user, pk=str(a.pk))
            assert MinhaPresencaView.as_view()(_req("post", user), pk=a.pk).status_code == 200

            _staff(AssembleiaViewSet, {"post": "presencas"}, board_user, data={"membro": str(devedor.id)}, pk=str(a.pk))
            lista = _staff(AssembleiaViewSet, {"get": "presencas"}, board_user, method="get", pk=str(a.pk)).data
            assert lista["quorum"] == {
                "aptos": 2, "presentes": 2, "presentes_aptos": 1, "pct": 50.0, "minimo": 50, "atingido": True,
            }

            sem_encerrar = _staff(AssembleiaViewSet, {"post": "publicar_ata"}, board_user, pk=str(a.pk))
            assert sem_encerrar.status_code == 400
            _staff(AssembleiaViewSet, {"post": "encerrar"}, board_user, pk=str(a.pk))
            ata = _staff(AssembleiaViewSet, {"post": "gerar_ata"}, board_user, pk=str(a.pk)).data["ata"]
            assert "sendo 1 de 2 aptos" in ata and "1. Prestação de contas" in ata

            pub = _staff(AssembleiaViewSet, {"post": "publicar_ata"}, board_user, pk=str(a.pk))
            assert pub.status_code == 200 and len(pub.data["ata_hash"]) == 64
            assert ContextoHistorico.objects.filter(entidade_tipo="assembleia", entidade_id=a.id).exists()
            edit = _staff(AssembleiaViewSet, {"patch": "partial_update"}, board_user, method="patch",
                          data={"ata": "outra"}, pk=str(a.pk))
            assert edit.status_code == 400

            pdf = _staff(AssembleiaViewSet, {"get": "ata_pdf"}, board_user, method="get", pk=str(a.pk))
            assert pdf["Content-Type"] == "application/pdf"
            portal = MinhaGovernancaView.as_view()(_req("get", user)).data["assembleias"][0]
            assert portal["presente"] is True and portal["ata"].startswith("ATA DA ASSEMBLEIA")
