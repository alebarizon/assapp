from django.db import models


class EmailEnviado(models.Model):
    """Destinatários entregues ao provedor de e-mail; base da cota horária (schema public)."""

    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    destinatarios = models.PositiveIntegerField()

    class Meta:
        ordering = ["-criado_em"]
