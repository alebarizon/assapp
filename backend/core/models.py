from django.db import models


class EmailEnviado(models.Model):
    """Destinatários entregues ao provedor de e-mail; base da cota horária (schema public)."""

    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    destinatarios = models.PositiveIntegerField()

    class Meta:
        ordering = ["-criado_em"]


class EmailPendente(models.Model):
    """E-mail individual que falhou no envio; o agendador tenta de novo (schema public, todas as associações)."""

    PENDENTE = "pendente"
    ENVIADO = "enviado"
    DESISTIU = "desistiu"
    STATUS_CHOICES = [(PENDENTE, "Pendente"), (ENVIADO, "Enviado"), (DESISTIU, "Desistiu")]

    criado_em = models.DateTimeField(auto_now_add=True)
    schema = models.CharField(max_length=63, blank=True, default="")
    remetente = models.CharField(max_length=255)
    destinatarios = models.JSONField()
    reply_to = models.JSONField(blank=True, default=list)
    assunto = models.CharField(max_length=255)
    texto = models.TextField()
    html = models.TextField(blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDENTE, db_index=True)
    tentativas = models.PositiveSmallIntegerField(default=1)
    proxima_tentativa = models.DateTimeField(db_index=True)
    ultimo_erro = models.CharField(max_length=500, blank=True, default="")
    enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["proxima_tentativa"]

    def __str__(self):
        return f"{self.assunto} → {', '.join(self.destinatarios)} ({self.status})"
