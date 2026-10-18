"""Newsletter: segmentação, fila com limite, rodapé de descadastro e descadastro público."""
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.management import call_command
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from contatos.models import Contato, Etiqueta
from eventos.models import EventoAcademico, InscricaoEvento
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus, Membro
from newsletter.models import Campanha, Descadastro, StatusCampanha, StatusEnvio
from newsletter.services import destinatarios, processar_fila
from newsletter.views import CampanhaViewSet, DescadastrarPublicView

factory = APIRequestFactory()


def _staff(actions, user, method="post", data=None, **kwargs):
    request = getattr(factory, method)("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return CampanhaViewSet.as_view(actions)(request, **kwargs)


def _associado(nome, email, em_dia=True, tipo="efetivo", status=FiliacaoStatus.ATIVA):
    membro = Membro.objects.create(nome_completo=nome, email=email)
    filiacao = Filiacao.objects.create(membro=membro, data_inicio=date(2025, 1, 1), status=status, tipo=tipo)
    if not em_dia:
        Anuidade.objects.create(
            filiacao=filiacao, ano_referencia=2026, valor=Decimal("100"),
            vencimento=date.today() - timedelta(days=10), status=AnuidadeStatus.PENDENTE,
        )
    return membro


def _token_do_email(corpo: str) -> str:
    url = next(p for p in corpo.split() if "/site/descadastrar?" in p)
    return parse_qs(urlparse(url).query)["t"][0]


@pytest.mark.django_db
class TestSegmentacao:
    def test_publico_combina_fontes_sem_duplicar(self, test_tenant):
        with schema_context(test_tenant.schema_name):
            _associado("Ana Souza", "ana@teste.org")
            _associado("Bruno Lima", "bruno@teste.org", em_dia=False)
            _associado("Carla Dias", "carla@teste.org", tipo="estudante")
            _associado("Davi Ex", "davi@teste.org", status=FiliacaoStatus.CANCELADA)

            evento = EventoAcademico.objects.create(
                titulo="Congresso", slug="congresso",
                data_inicio=timezone.now(), data_fim=timezone.now() + timedelta(days=2),
            )
            InscricaoEvento.objects.create(evento=evento, nome="Ana Souza", email="ANA@teste.org")
            InscricaoEvento.objects.create(evento=evento, nome="Eva Externa", email="eva@fora.org")

            etiqueta = Etiqueta.objects.create(nome="Patrocínio")
            com = Contato.objects.create(nome="Fábio Lead", email="fabio@empresa.com", consentimento_lgpd=True)
            sem = Contato.objects.create(nome="Gil Sem", email="gil@empresa.com", consentimento_lgpd=False)
            com.etiquetas.add(etiqueta)
            sem.etiquetas.add(etiqueta)

            em_dia = destinatarios({"associados": {"situacoes": ["em_dia"], "tipos": []}})
            assert [d["email"] for d in em_dia] == ["ana@teste.org", "carla@teste.org"]

            estudantes = destinatarios({"associados": {"situacoes": [], "tipos": ["estudante"]}})
            assert [d["email"] for d in estudantes] == ["carla@teste.org"]

            pendentes = destinatarios({"associados": {"situacoes": ["pendente"]}})
            inativos = destinatarios({"associados": {"situacoes": ["inativo"]}})
            assert [d["email"] for d in pendentes] == ["bruno@teste.org"]
            assert [d["email"] for d in inativos] == ["davi@teste.org"]

            Descadastro.objects.create(email="carla@teste.org")
            todos = destinatarios({
                "associados": {"situacoes": ["em_dia"]},
                "eventos": [str(evento.id)],
                "etiquetas": [etiqueta.id],
            })
            assert [d["email"] for d in todos] == ["ana@teste.org", "eva@fora.org", "fabio@empresa.com"]


@pytest.mark.django_db
class TestEnvio:
    def test_fila_limite_rodape_e_descadastro(self, test_tenant, board_user, mailoutbox, settings):
        with schema_context(test_tenant.schema_name):
            for i in range(5):
                _associado(f"Pessoa {i} Silva", f"p{i}@teste.org")

            criada = _staff({"post": "create"}, board_user, data={
                "assunto": "Boletim de outubro",
                "corpo": "Olá, {nome}!\nNovidades em https://exemplo.org",
                "link": "https://exemplo.org/boletim",
                "publico": {"associados": {"situacoes": ["em_dia"]}},
            })
            assert criada.status_code == 201, criada.data
            pk = criada.data["id"]
            assert criada.data["link_label"] == "Saiba mais"

            previa = _staff({"post": "publico"}, board_user, data={"publico": criada.data["publico"]})
            assert previa.data["total"] == 5 and len(previa.data["amostra"]) == 5

            teste = _staff({"post": "teste"}, board_user, data={"email": "eu@teste.org"}, pk=pk)
            assert teste.status_code == 200 and mailoutbox[-1].subject == "[Teste] Boletim de outubro"
            mailoutbox.clear()

            enviada = _staff({"post": "enviar"}, board_user, pk=pk)
            assert enviada.status_code == 200 and enviada.data["enfileirados"] == 5
            assert enviada.data["status"] == "enviando" and len(mailoutbox) == 0

            editar = _staff({"patch": "partial_update"}, board_user, method="patch", data={"assunto": "x"}, pk=pk)
            assert editar.status_code == 400

            assert processar_fila(2)["enviados"] == 2
            msg = mailoutbox[0]
            assert msg.body.startswith("Olá, Pessoa!")
            assert "List-Unsubscribe" in msg.extra_headers and "/site/descadastrar?" in msg.body

            token = _token_do_email(msg.body)
            req = factory.get(f"/?schema={test_tenant.schema_name}&t={token}")
            info = DescadastrarPublicView.as_view()(req)
            assert info.status_code == 200 and info.data["descadastrado"] is False
            assert info.data["email"].startswith("p0") and "*" in info.data["email"]

            Descadastro.objects.create(email="p3@teste.org")
            req = factory.post(f"/?schema={test_tenant.schema_name}", {"t": token}, format="json")
            assert DescadastrarPublicView.as_view()(req).data["descadastrado"] is True

            call_command("enviar_newsletters", schema=test_tenant.schema_name, por_minuto=10)
            campanha = Campanha.objects.get(pk=pk)
            assert campanha.status == StatusCampanha.ENVIADA
            assert campanha.envios.filter(status=StatusEnvio.ENVIADO).count() == 4
            assert campanha.envios.get(email="p3@teste.org").status == StatusEnvio.CANCELADO
            assert len(mailoutbox) == 4
            assert Descadastro.objects.get(email="p0@teste.org").campanha_id == campanha.pk

            ruim = factory.get(f"/?schema={test_tenant.schema_name}&t=invalido")
            assert DescadastrarPublicView.as_view()(ruim).status_code == 400

    def test_cancelar_e_sem_destinatarios(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            vazia = _staff({"post": "create"}, board_user, data={
                "assunto": "Ninguém", "corpo": "x", "publico": {"associados": {"situacoes": ["pendente"]}},
            })
            assert _staff({"post": "enviar"}, board_user, pk=vazia.data["id"]).status_code == 400

            _associado("Ana Souza", "ana@teste.org")
            _associado("Bruno Lima", "bruno@teste.org")
            c = _staff({"post": "create"}, board_user, data={
                "assunto": "Aviso", "corpo": "x", "publico": {"associados": {}},
            })
            _staff({"post": "enviar"}, board_user, pk=c.data["id"])
            cancelada = _staff({"post": "cancelar"}, board_user, pk=c.data["id"])
            assert cancelada.data["cancelados"] == 2 and cancelada.data["status"] == "cancelada"
            assert cancelada.data["estatisticas"]["cancelado"] == 2

            copia = _staff({"post": "duplicar"}, board_user, pk=c.data["id"])
            assert copia.status_code == 201 and copia.data["status"] == "rascunho"
