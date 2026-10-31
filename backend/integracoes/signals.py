from django.db.models.signals import post_save
from django.dispatch import receiver

from eventos.models import InscricaoEvento
from membros.models import Membro

from .services import disparar


@receiver(post_save, sender=Membro, dispatch_uid="integracoes_membro_criado")
def membro_criado(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        disparar(
            "membro.criado",
            {
                "id": str(instance.id),
                "nome": instance.nome_completo,
                "email": instance.email,
                "instituicao": instance.instituicao or "",
                "orcid": instance.orcid or "",
            },
        )


@receiver(post_save, sender=InscricaoEvento, dispatch_uid="integracoes_inscricao_criada")
def inscricao_criada(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        disparar(
            "inscricao.criada",
            {
                "id": str(instance.id),
                "evento": {"id": str(instance.evento_id), "titulo": instance.evento.titulo},
                "nome": instance.nome,
                "email": instance.email,
                "membro_id": str(instance.membro_id) if instance.membro_id else None,
                "confirmada": instance.confirmada,
            },
        )
