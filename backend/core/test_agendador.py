from datetime import datetime
from unittest import mock

from django.test import SimpleTestCase, override_settings

from core.management.commands.agendador import Command

CONSOLE = "django.core.mail.backends.console.EmailBackend"
SMTP = "django.core.mail.backends.smtp.EmailBackend"


def _comando():
    cmd = Command()
    cmd.ultima_regua = None
    return cmd


def _chamadas(chamar):
    return [c.args for c in chamar.call_args_list]


@override_settings(REGUA_HORA=8, EMAIL_BACKEND=SMTP)
class AgendadorTests(SimpleTestCase):
    @mock.patch("core.management.commands.agendador.call_command")
    def test_regua_roda_uma_vez_por_dia_depois_da_hora(self, chamar):
        cmd = _comando()
        cmd.ciclo(datetime(2026, 10, 18, 7, 59))
        self.assertEqual(_chamadas(chamar), [("enviar_newsletters",)])

        chamar.reset_mock()
        cmd.ciclo(datetime(2026, 10, 18, 8, 0))
        cmd.ciclo(datetime(2026, 10, 18, 9, 0))
        self.assertEqual(
            _chamadas(chamar),
            [("enviar_newsletters",), ("regua_anuidades",), ("enviar_newsletters",)],
        )

        chamar.reset_mock()
        cmd.ciclo(datetime(2026, 10, 19, 8, 1))
        self.assertIn(("regua_anuidades",), _chamadas(chamar))

    @mock.patch("core.management.commands.agendador.call_command")
    def test_falha_na_regua_tenta_de_novo_no_proximo_ciclo(self, chamar):
        def efeito(nome, *args, **kwargs):
            if nome == "regua_anuidades" and chamar.call_count < 3:
                raise RuntimeError("banco indisponível")

        chamar.side_effect = efeito
        cmd = _comando()
        cmd.ciclo(datetime(2026, 10, 18, 8, 0))
        self.assertIsNone(cmd.ultima_regua)
        cmd.ciclo(datetime(2026, 10, 18, 8, 1))
        self.assertEqual(cmd.ultima_regua, datetime(2026, 10, 18).date())

    @override_settings(EMAIL_BACKEND=CONSOLE)
    @mock.patch("core.management.commands.agendador.call_command")
    def test_sem_provedor_real_so_marca_vencidas(self, chamar):
        _comando().ciclo(datetime(2026, 10, 18, 8, 0))
        self.assertIn(("regua_anuidades", "--sem-email"), _chamadas(chamar))
