"""
Suporte — chamados da associação para a equipe Gesttora.

App compartilhado (schema public): a equipe enxerga os chamados de todas as
associações sem trocar de schema. Usuários vivem no schema de cada tenant, por
isso o autor é guardado de forma desnormalizada (id, nome, e-mail).
"""
from django.db import models


class Chamado(models.Model):
    DUVIDA = "duvida"
    PROBLEMA = "problema"
    FINANCEIRO = "financeiro"
    SUGESTAO = "sugestao"
    CANCELAMENTO = "cancelamento"
    CATEGORIA_CHOICES = [
        (DUVIDA, "Dúvida de uso"),
        (PROBLEMA, "Problema técnico"),
        (FINANCEIRO, "Assinatura e pagamento"),
        (SUGESTAO, "Sugestão"),
        (CANCELAMENTO, "Cancelamento"),
    ]

    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"
    PRIORIDADE_CHOICES = [(BAIXA, "Baixa"), (NORMAL, "Normal"), (ALTA, "Alta"), (URGENTE, "Urgente")]

    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO = "aguardando_associacao"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"
    STATUS_CHOICES = [
        (ABERTO, "Aberto"),
        (EM_ANDAMENTO, "Em andamento"),
        (AGUARDANDO, "Aguardando a associação"),
        (RESOLVIDO, "Resolvido"),
        (FECHADO, "Fechado"),
    ]
    STATUS_ENCERRADOS = [RESOLVIDO, FECHADO]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="chamados")
    assunto = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default=DUVIDA)
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default=NORMAL)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=ABERTO, db_index=True)
    autor_id = models.CharField(max_length=64)
    autor_nome = models.CharField(max_length=200)
    autor_email = models.EmailField()
    pagina = models.CharField(max_length=300, blank=True, default="", help_text="Tela onde o problema ocorreu")
    lido_pela_equipe = models.BooleanField(default=False)
    lido_pela_associacao = models.BooleanField(default=True)
    ultima_mensagem_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ultima_mensagem_em", "-created_at"]
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        indexes = [models.Index(fields=["tenant", "status"])]

    def __str__(self):
        return f"#{self.pk} {self.assunto}"


class MensagemChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name="mensagens")
    autor_id = models.CharField(max_length=64)
    autor_nome = models.CharField(max_length=200)
    da_equipe = models.BooleanField(default=False)
    interna = models.BooleanField(default=False, help_text="Nota interna da equipe, invisível à associação")
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Mensagem do chamado"
        verbose_name_plural = "Mensagens do chamado"


class AnexoChamado(models.Model):
    mensagem = models.ForeignKey(MensagemChamado, on_delete=models.CASCADE, related_name="anexos")
    arquivo = models.FileField(upload_to="support/%Y/%m/")
    nome = models.CharField(max_length=255)
    tamanho = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo do chamado"
        verbose_name_plural = "Anexos do chamado"
