"""User model — roles adaptados para associações científicas (H2: perfil_tecnico)."""
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    SUPERADMIN = "superadmin"
    ASSOCIATION_ADMIN = "association_admin"
    BOARD_MEMBER = "board_member"
    MEMBER = "member"
    REVIEWER = "reviewer"

    ROLE_CHOICES = [
        (SUPERADMIN, "Super Admin"),
        (ASSOCIATION_ADMIN, "Administrador da Associação"),
        (BOARD_MEMBER, "Membro da Diretoria"),
        (MEMBER, "Associado"),
        (REVIEWER, "Parecerista"),
    ]

    PERFIL_INICIANTE = "iniciante"
    PERFIL_INTERMEDIARIO = "intermediario"
    PERFIL_AVANCADO = "avancado"

    PERFIL_TECNICO_CHOICES = [
        (PERFIL_INICIANTE, "Iniciante"),
        (PERFIL_INTERMEDIARIO, "Intermediário"),
        (PERFIL_AVANCADO, "Avançado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    role = models.CharField(
        max_length=32, choices=ROLE_CHOICES, default=ASSOCIATION_ADMIN, db_index=True
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    phone_number = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Telefone inválido.",
            )
        ],
    )
    locale = models.CharField(max_length=10, default="pt-BR")
    # H2 — perfil para interface adaptativa
    perfil_tecnico = models.CharField(
        max_length=20,
        choices=PERFIL_TECNICO_CHOICES,
        default=PERFIL_INICIANTE,
        help_text="H2: determina complexidade da interface",
    )
    consentimento_lgpd = models.BooleanField(default=False)
    consentimento_em = models.DateTimeField(blank=True, null=True)
    terms_accepted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            base = self.email.split("@")[0]
            self.username = base
            counter = 1
            while User.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                self.username = f"{base}{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def is_board_or_admin(self):
        return self.role in (
            self.ASSOCIATION_ADMIN,
            self.BOARD_MEMBER,
            self.SUPERADMIN,
        )
