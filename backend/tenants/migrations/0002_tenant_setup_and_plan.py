# Generated manually for signup/setup flow (2026-07-14)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="setup_completed",
            field=models.BooleanField(
                default=False,
                help_text="True após wizard de setup (1º mandato + diretoria).",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="plan_slug",
            field=models.CharField(
                blank=True,
                help_text="Plano SaaS escolhido no signup (ex: starter, profissional).",
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="payment_simulated",
            field=models.BooleanField(
                default=True,
                help_text="True quando o signup não passou por Stripe (modo simulado).",
            ),
        ),
    ]
