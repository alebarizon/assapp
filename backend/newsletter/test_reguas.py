"""Réguas automáticas: boas-vindas, inativos e autor aprovado que não é sócio."""
from datetime import date, timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from eventos.models import CallForPapers, EventoAcademico, InscricaoEvento, SubmissaoTrabalho
from membros.models import Filiacao, FiliacaoStatus, Membro
from membros.timeline import timeline_membro
from newsletter.models import Descadastro, EnvioRegua, Regua, TipoRegua
from newsletter.reguas import candidatos, executar, obter_reguas
from newsletter.views import ReguaViewSet

factory = APIRequestFactory()


def _associado(nome, email, inicio, status=FiliacaoStatus.ATIVA):
    membro = Membro.objects.create(nome_completo=nome, email=email)
    Filiacao.objects.create(membro=membro, data_inicio=inicio, status=status)
    return membro


def _staff(actions, user, method="get", data=None, **kwargs):
    request = getattr(factory, method)("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return ReguaViewSet.as_view(actions)(request, **kwargs)


def _evento(titulo="Congresso Anual", dias=30, publicado=True):
    agora = timezone.now()
    return EventoAcademico.objects.create(
        titulo=titulo, slug=f"ev-{EventoAcademico.objects.count()}", publicado_site=publicado,
        data_inicio=agora + timedelta(days=dias), data_fim=agora + timedelta(days=dias + 2),
    )


@pytest.mark.django_db
class TestReguas:
    def test_boas_vindas_uma_vez_com_proximo_evento(self, test_tenant, mailoutbox):
        with schema_context(test_tenant.schema_name):
            hoje = timezone.localdate()
            _evento()
            _associado("Ana Souza", "ana@teste.org", hoje - timedelta(days=2))
            _associado("Bruno Antigo", "bruno@teste.org", hoje - timedelta(days=400))
            _associado("Carla Cancelada", "carla@teste.org", hoje, status=FiliacaoStatus.CANCELADA)

            resultado = executar()
            assert resultado[TipoRegua.BOAS_VINDAS] == {"enviados": 1, "falhas": 0}
            assert TipoRegua.INATIVOS not in resultado
            msg = mailoutbox[0]
            assert msg.to == ["ana@teste.org"] and msg.subject == "Bem-vindo(a) à Associação Teste"
            assert msg.body.startswith("Olá, Ana!") and "Próximo evento: Congresso Anual" in msg.body
            assert "/app/portal" in msg.body and "List-Unsubscribe" not in msg.extra_headers

            assert executar()[TipoRegua.BOAS_VINDAS]["enviados"] == 0
            membro = Membro.objects.get(email="ana@teste.org")
            assert any("boas-vindas" in i["titulo"] for i in timeline_membro(membro))

    def test_inativos_respeita_atividade_descadastro_e_intervalo(self, test_tenant, mailoutbox):
        with schema_context(test_tenant.schema_name):
            antigo = timezone.localdate() - timedelta(days=500)
            parado = _associado("Paulo Parado", "paulo@teste.org", antigo)
            ativo = _associado("Lia Ativa", "lia@teste.org", antigo)
            _associado("Sara Sem", "sara@teste.org", antigo)
            _associado("Nina Nova", "nina@teste.org", timezone.localdate() - timedelta(days=20))
            InscricaoEvento.objects.create(evento=_evento(), membro=ativo, nome="Lia", email="lia@teste.org")
            Descadastro.objects.create(email="sara@teste.org")

            regua = obter_reguas()[TipoRegua.INATIVOS]
            assert regua.ativa is False and regua.dias == 6
            assert [c["email"] for c in candidatos(regua)] == ["paulo@teste.org"]

            Regua.objects.filter(tipo=TipoRegua.INATIVOS).update(ativa=True)
            Regua.objects.filter(tipo=TipoRegua.BOAS_VINDAS).update(ativa=False)
            assert executar()[TipoRegua.INATIVOS]["enviados"] == 1
            assert mailoutbox[0].to == ["paulo@teste.org"]
            assert "List-Unsubscribe" in mailoutbox[0].extra_headers

            amanha = timezone.localdate() + timedelta(days=1)
            assert executar(hoje=amanha)[TipoRegua.INATIVOS]["enviados"] == 0
            assert EnvioRegua.objects.get(tipo=TipoRegua.INATIVOS).membro == parado

    def test_autor_aprovado_nao_socio(self, test_tenant, mailoutbox):
        with schema_context(test_tenant.schema_name):
            agora = timezone.now()
            evento = _evento("Encontro Nacional")
            cfp = CallForPapers.objects.create(
                evento=evento, titulo="Chamada", instrucoes="x",
                data_abertura=agora - timedelta(days=30), data_fechamento=agora - timedelta(days=5),
            )
            autor = User.objects.create_user(
                username="autor", email="autor@fora.org", password="x", first_name="Rui", last_name="Autor"
            )
            _associado("Sócia Coautora", "socia@teste.org", date(2024, 1, 1))
            SubmissaoTrabalho.objects.create(
                cfp=cfp, autor=autor, titulo="Redes e cultura", resumo="r", status="aceito", decidido_em=agora,
                coautores=[{"nome": "Sócia Coautora", "email": "SOCIA@teste.org"},
                           {"nome": "Teo Externo", "email": "teo@fora.org"}],
            )
            SubmissaoTrabalho.objects.create(
                cfp=cfp, autor=autor, titulo="Outro aceito", resumo="r", status="aceito", decidido_em=agora,
            )
            SubmissaoTrabalho.objects.create(
                cfp=cfp, autor=User.objects.create_user(username="rej", email="rej@fora.org", password="x"),
                titulo="Recusado", resumo="r", status="rejeitado", decidido_em=agora,
            )

            call_command("reguas_relacionamento", schema=test_tenant.schema_name)
            destinos = sorted(m.to[0] for m in mailoutbox)
            assert destinos == ["autor@fora.org", "teo@fora.org"]
            msg = next(m for m in mailoutbox if m.to == ["autor@fora.org"])
            assert msg.body.startswith("Olá, Rui!") and '"Redes e cultura" em Encontro Nacional' in msg.body
            assert "#associe-se" in msg.body and "schema=teste" in msg.body

            mailoutbox.clear()
            call_command("reguas_relacionamento", schema=test_tenant.schema_name)
            assert mailoutbox == []

    def test_api_configura_previa_teste_e_restaura(self, test_tenant, board_user, mailoutbox):
        with schema_context(test_tenant.schema_name):
            _associado("Ana Souza", "ana@teste.org", timezone.localdate())
            lista = _staff({"get": "list"}, board_user)
            assert lista.status_code == 200
            assert [r["tipo"] for r in lista.data["reguas"]] == ["autor_nao_socio", "boas_vindas", "inativos"]
            assert lista.data["email_entregue"] is False

            alterada = _staff(
                {"patch": "partial_update"}, board_user, method="patch",
                data={"assunto": "Oi {nome}", "dias": 3, "ativa": False}, tipo="boas_vindas",
            )
            assert alterada.status_code == 200 and alterada.data["assunto"] == "Oi {nome}"
            ruim = _staff({"patch": "partial_update"}, board_user, method="patch", data={"dias": 40}, tipo="inativos")
            assert ruim.status_code == 400

            previa = _staff({"get": "previa"}, board_user, tipo="boas_vindas")
            assert previa.data["total"] == 1 and previa.data["amostra"][0]["email"] == "ana@teste.org"

            teste = _staff({"post": "teste"}, board_user, method="post", tipo="boas_vindas")
            assert teste.status_code == 200 and mailoutbox[-1].subject == "[Teste] Oi Diretoria"

            restaurada = _staff({"post": "restaurar"}, board_user, method="post", tipo="boas_vindas")
            assert restaurada.data["assunto"] == "Bem-vindo(a) à {associacao}" and restaurada.data["dias"] == 7
            assert restaurada.data["ativa"] is False
