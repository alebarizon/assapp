"""Cota horária de e-mail: contagem, backend SMTP e pausa dos envios em massa."""
import smtplib
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.core.mail import EmailMessage
from django.utils import timezone
from django_tenants.utils import schema_context

from core import cota_email
from core.email_backend import CotaSMTPBackend
from core.models import EmailEnviado
from membros.models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus, Membro
from membros.services import enviar_lembretes_anuidade
from newsletter.models import Campanha, EnvioCampanha, StatusCampanha, StatusEnvio, TipoRegua
from newsletter.reguas import executar
from newsletter.services import processar_fila


def _associado(nome, email, inicio):
    membro = Membro.objects.create(nome_completo=nome, email=email)
    filiacao = Filiacao.objects.create(membro=membro, data_inicio=inicio, status=FiliacaoStatus.ATIVA)
    return membro, filiacao


@pytest.mark.django_db
class TestCota:
    def test_conta_so_a_ultima_hora(self, settings):
        settings.EMAIL_LIMITE_POR_HORA = 3
        antigo = EmailEnviado.objects.create(destinatarios=50)
        EmailEnviado.objects.filter(pk=antigo.pk).update(criado_em=timezone.now() - timedelta(minutes=61))
        cota_email.registrar(2)
        assert cota_email.usados_na_ultima_hora() == 2
        assert cota_email.cabe(1) and not cota_email.cabe(2)

    def test_sem_limite(self, settings):
        settings.EMAIL_LIMITE_POR_HORA = 0
        cota_email.registrar(500)
        assert cota_email.cabe(100)

    def test_backend_registra_destinatarios_entregues(self):
        backend = CotaSMTPBackend()
        backend.connection = mock.Mock()
        msg = EmailMessage("Oi", "corpo", "noreply@gesttora.com.br", ["a@x.org"], cc=["b@x.org"])
        assert backend._send(msg)
        assert cota_email.usados_na_ultima_hora() == 2

        backend.connection.sendmail.side_effect = smtplib.SMTPException("recusado")
        backend.fail_silently = True
        assert not backend._send(msg)
        assert cota_email.usados_na_ultima_hora() == 2


@pytest.mark.django_db
class TestEnviosEmMassaRespeitamCota:
    def test_newsletter_fica_na_fila(self, test_tenant, mailoutbox, settings):
        settings.EMAIL_LIMITE_POR_HORA = 5
        cota_email.registrar(5)
        with schema_context(test_tenant.schema_name):
            campanha = Campanha.objects.create(assunto="Boletim", corpo="Olá", status=StatusCampanha.ENVIANDO)
            for i in range(3):
                EnvioCampanha.objects.create(campanha=campanha, email=f"p{i}@teste.org")

            assert processar_fila(10)["enviados"] == 0
            assert campanha.envios.filter(status=StatusEnvio.PENDENTE, tentativas=0).count() == 3

            EmailEnviado.objects.all().delete()
            assert processar_fila(10)["enviados"] == 3
        assert len(mailoutbox) == 3

    def test_reguas_e_lembretes_param(self, test_tenant, mailoutbox, settings):
        settings.EMAIL_LIMITE_POR_HORA = 5
        cota_email.registrar(5)
        with schema_context(test_tenant.schema_name):
            hoje = timezone.localdate()
            _, filiacao = _associado("Ana Souza", "ana@teste.org", hoje - timedelta(days=2))
            Anuidade.objects.create(
                filiacao=filiacao, ano_referencia=hoje.year, valor=Decimal("100"),
                vencimento=hoje - timedelta(days=1), status=AnuidadeStatus.VENCIDA,
            )

            assert executar()[TipoRegua.BOAS_VINDAS]["enviados"] == 0
            assert enviar_lembretes_anuidade()["enviados"] == 0
            assert mailoutbox == []

            EmailEnviado.objects.all().delete()
            assert executar()[TipoRegua.BOAS_VINDAS]["enviados"] == 1
            assert enviar_lembretes_anuidade()["enviados"] == 1
