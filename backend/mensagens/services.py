from django.db import transaction
from django.utils import timezone

from core.emails import enviar_email, frontend_url, nome_associacao

from .models import Conversa, Mensagem


def _nome(user) -> str:
    return user.get_full_name() or user.email


def _avisar_associado(conversa: Conversa, texto: str):
    email = conversa.membro.email
    if not email:
        return
    associacao = nome_associacao()
    corpo = f"Olá, {conversa.membro.nome_completo}!\n\n{associacao} enviou uma mensagem: “{conversa.assunto}”.\n\n{texto}"
    link = frontend_url(f"/app/portal/mensagens/{conversa.id}")
    transaction.on_commit(
        lambda: enviar_email(email, f"[{associacao}] {conversa.assunto}", corpo, link=link, link_label="Responder no portal")
    )


@transaction.atomic
def iniciar_pela_diretoria(user, membros, assunto: str, texto: str, notificar: bool = True) -> list[Conversa]:
    agora = timezone.now()
    conversas = []
    for membro in membros:
        conversa = Conversa.objects.create(
            membro=membro,
            assunto=assunto,
            iniciada_pela_diretoria=True,
            lida_pela_diretoria=True,
            lida_pelo_associado=False,
            ultima_mensagem_em=agora,
        )
        Mensagem.objects.create(conversa=conversa, autor=user, autor_nome=_nome(user), da_diretoria=True, texto=texto)
        if notificar:
            _avisar_associado(conversa, texto)
        conversas.append(conversa)
    return conversas


@transaction.atomic
def iniciar_pelo_associado(user, membro, assunto: str, texto: str) -> Conversa:
    conversa = Conversa.objects.create(
        membro=membro,
        assunto=assunto,
        iniciada_pela_diretoria=False,
        lida_pela_diretoria=False,
        lida_pelo_associado=True,
        ultima_mensagem_em=timezone.now(),
    )
    Mensagem.objects.create(conversa=conversa, autor=user, autor_nome=membro.nome_completo, texto=texto)
    return conversa


@transaction.atomic
def responder(conversa: Conversa, user, texto: str, da_diretoria: bool, notificar: bool = True) -> Mensagem:
    nome = _nome(user) if da_diretoria else conversa.membro.nome_completo
    mensagem = Mensagem.objects.create(
        conversa=conversa, autor=user, autor_nome=nome, da_diretoria=da_diretoria, texto=texto
    )
    conversa.ultima_mensagem_em = mensagem.created_at
    conversa.status = Conversa.ABERTA
    if da_diretoria:
        conversa.lida_pelo_associado = False
        conversa.lida_pela_diretoria = True
        if notificar:
            _avisar_associado(conversa, texto)
    else:
        conversa.lida_pela_diretoria = False
        conversa.lida_pelo_associado = True
    conversa.save(update_fields=["ultima_mensagem_em", "status", "lida_pelo_associado", "lida_pela_diretoria"])
    return mensagem
