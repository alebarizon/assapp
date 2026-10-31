"""E-mails individuais que falham: fila de reenvio, desistência e endpoint de saúde para monitor externo."""
import smtplib
from datetime import timedelta
from unittest import mock

import pytest
from django.core.mail import EmailMultiAlternatives
from django.test import RequestFactory
from django.utils import timezone

from core.emails import ESPERAS_MINUTOS, enviar_email, reenviar_pendentes
from core.models import EmailPendente
from core.views import health_email


def _falhar_envio():
    return mock.patch.object(EmailMultiAlternatives, "send", side_effect=smtplib.SMTPServerDisconnected("caiu"))


def _vencer(pendente):
    EmailPendente.objects.filter(pk=pendente.pk).update(proxima_tentativa=timezone.now() - timedelta(seconds=1))


@pytest.mark.django_db
class TestFilaDeReenvio:
    def test_falha_vai_para_a_fila_e_sai_no_reenvio(self, mailoutbox):
        with _falhar_envio():
            assert not enviar_email("ana@teste.org", "Convite", "Olá", link="https://x/y", reply_to="sec@x.org")
        pendente = EmailPendente.objects.get()
        assert pendente.destinatarios == ["ana@teste.org"]
        assert pendente.reply_to == ["sec@x.org"]
        assert "caiu" in pendente.ultimo_erro
        assert pendente.proxima_tentativa > timezone.now()

        assert reenviar_pendentes() == {"enviados": 0, "falhas": 0, "desistencias": 0}
        _vencer(pendente)
        assert reenviar_pendentes()["enviados"] == 1
        pendente.refresh_from_db()
        assert pendente.status == EmailPendente.ENVIADO
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Convite"
        assert "https://x/y" in mailoutbox[0].body
        assert mailoutbox[0].alternatives

    def test_fila_false_nao_enfileira(self):
        with _falhar_envio():
            assert not enviar_email("ana@teste.org", "Lembrete", "Olá", fila=False)
        assert not EmailPendente.objects.exists()

    def test_falhas_seguidas_espaçam_e_depois_desistem(self):
        with _falhar_envio():
            enviar_email("ana@teste.org", "Convite", "Olá")
        pendente = EmailPendente.objects.get()
        conexao = mock.Mock()
        conexao.send_messages.side_effect = smtplib.SMTPRecipientsRefused({})
        with mock.patch("core.emails.get_connection", return_value=conexao):
            for _ in range(len(ESPERAS_MINUTOS) - 1):
                _vencer(pendente)
                assert reenviar_pendentes()["falhas"] == 1
            pendente.refresh_from_db()
            assert pendente.status == EmailPendente.PENDENTE
            assert pendente.proxima_tentativa > timezone.now() + timedelta(minutes=ESPERAS_MINUTOS[-1] - 1)

            _vencer(pendente)
            assert reenviar_pendentes()["desistencias"] == 1
        pendente.refresh_from_db()
        assert pendente.status == EmailPendente.DESISTIU

    def test_smtp_fora_nao_gasta_tentativas(self):
        with _falhar_envio():
            enviar_email("ana@teste.org", "Convite", "Olá")
        pendente = EmailPendente.objects.get()
        _vencer(pendente)
        conexao = mock.Mock()
        conexao.open.side_effect = OSError("sem rota")
        with mock.patch("core.emails.get_connection", return_value=conexao):
            assert reenviar_pendentes() == {"enviados": 0, "falhas": 0, "desistencias": 0}
        pendente.refresh_from_db()
        assert pendente.tentativas == 1
        assert pendente.status == EmailPendente.PENDENTE


@pytest.mark.django_db
class TestHealthEmail:
    def _get(self):
        return health_email(RequestFactory().get("/health/email/"))

    def test_sem_smtp_configurado_fica_ok(self):
        resposta = self._get()
        assert resposta.status_code == 200
        assert b'"smtp": "desligado"' in resposta.content

    def test_smtp_fora_retorna_503(self):
        with mock.patch("core.emails.smtp_disponivel", return_value=False):
            resposta = self._get()
        assert resposta.status_code == 503
        assert b'"smtp": "indisponivel"' in resposta.content

    def test_email_parado_na_fila_retorna_503(self):
        with _falhar_envio():
            enviar_email("ana@teste.org", "Convite", "Olá")
        assert self._get().status_code == 200
        EmailPendente.objects.update(criado_em=timezone.now() - timedelta(minutes=31))
        resposta = self._get()
        assert resposta.status_code == 503
        assert b'"pendentes_ha_mais_de_30min": 1' in resposta.content
