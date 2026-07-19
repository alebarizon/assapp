"""H1 — Arquivamento automático de contextos ao encerrar mandato."""
from django.utils import timezone

from .models import ContextoHistorico, TimelineInstitucional


def arquivar_contextos_do_mandato(mandato, motivo_arquivamento: str = "encerramento_mandato"):
    """
    Preserva contextos do mandato encerrado sem deletar.
    Cria evento na timeline documentando o arquivamento.
    """
    contextos = ContextoHistorico.objects.filter(mandato=mandato, arquivado=False)
    count = contextos.count()
    if count == 0:
        return 0

    now = timezone.now()
    contextos.update(arquivado=True, updated_at=now)

    TimelineInstitucional.objects.create(
        mandato=mandato,
        tipo="arquivamento",
        titulo=f"Arquivamento automático — {count} registro(s)",
        descricao=(
            f"Contextos do mandato '{mandato.titulo}' arquivados automaticamente "
            f"ao encerrar gestão. Motivo: {motivo_arquivamento}."
        ),
        data_evento=now,
        metadata={"contextos_arquivados": count, "motivo": motivo_arquivamento},
    )
    return count
