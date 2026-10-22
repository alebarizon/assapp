from datetime import date, datetime
from unittest import mock

from django.test import SimpleTestCase, override_settings

from core.management.commands.agendador import Command

CONSOLE = "django.core.mail.backends.console.EmailBackend"
SMTP = "django.core.mail.backends.smtp.EmailBackend"


def _comando():
    cmd = Command()
    cmd.ultimas = {}
    return cmd


def _chamadas(chamar):
    return [c.args for c in chamar.call_args_list]


@override_settings(REGUA_HORA=8, EMAIL_BACKEND=SMTP)
class AgendadorTests(SimpleTestCase):
    @mock.patch("core.management.commands.agendador.call_command")
    def test_diarias_rodam_uma_vez_por_dia_depois_da_hora(self, chamar):
        cmd = _comando()
        cmd.ciclo(datetime(2026, 10, 18, 7, 59))
        self.assertEqual(_chamadas(chamar), [("enviar_newsletters",), ("sincronizar_cobrancas",)])

        chamar.reset_mock()
        cmd.ciclo(datetime(2026, 10, 18, 8, 0))
        cmd.ciclo(datetime(2026, 10, 18, 8, 10))
        self.assertEqual(
            _chamadas(chamar),
            [
                ("enviar_newsletters",),
                ("regua_anuidades",),
                ("reguas_relacionamento",),
                ("enviar_newsletters",),
            ],
        )

        chamar.reset_mock()
        cmd.ciclo(datetime(2026, 10, 19, 8, 1))
        self.assertIn(("regua_anuidades",), _chamadas(chamar))
        self.assertIn(("reguas_relacionamento",), _chamadas(chamar))

    @mock.patch("core.management.commands.agendador.call_command")
    def test_falha_numa_tarefa_tenta_de_novo_sem_repetir_a_outra(self, chamar):
        falhas = [RuntimeError("banco indisponível")]

        def efeito(nome, *args, **kwargs):
            if nome == "regua_anuidades" and falhas:
                raise falhas.pop()

        chamar.side_effect = efeito
        cmd = _comando()
        cmd.ciclo(datetime(2026, 10, 18, 8, 0))
        self.assertNotIn("regua_anuidades", cmd.ultimas)
        self.assertEqual(cmd.ultimas["reguas_relacionamento"], date(2026, 10, 18))

        chamar.reset_mock()
        cmd.ciclo(datetime(2026, 10, 18, 8, 1))
        self.assertEqual(_chamadas(chamar), [("enviar_newsletters",), ("regua_anuidades",)])
        self.assertEqual(cmd.ultimas["regua_anuidades"], date(2026, 10, 18))

    @mock.patch("core.management.commands.agendador.call_command")
    def test_cobrancas_sincronizam_a_cada_30_minutos(self, chamar):
        cmd = _comando()
        for minuto in (0, 10, 29, 30, 45, 59):
            cmd.ciclo(datetime(2026, 10, 18, 3, minuto))
        sincronizacoes = [c for c in _chamadas(chamar) if c == ("sincronizar_cobrancas",)]
        self.assertEqual(len(sincronizacoes), 2)

    @override_settings(EMAIL_BACKEND=CONSOLE)
    @mock.patch("core.management.commands.agendador.call_command")
    def test_sem_provedor_real_so_marca_vencidas(self, chamar):
        _comando().ciclo(datetime(2026, 10, 18, 8, 0))
        chamadas = _chamadas(chamar)
        self.assertIn(("regua_anuidades", "--sem-email"), chamadas)
        self.assertNotIn(("reguas_relacionamento",), chamadas)
