from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.emails import enviar_email, frontend_url

from .models import AnexoChamado, Chamado, MensagemChamado

MAX_ANEXO_BYTES = 10 * 1024 * 1024
MAX_ANEXOS = 5
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "csv", "xlsx", "xls", "docx", "doc"}


def is_equipe(user) -> bool:
    return getattr(user, "role", None) == "superadmin"


def tenant_do_user(user):
    return getattr(user, "_tenant", None) or getattr(user, "tenant", None)


def nome_do_user(user) -> str:
    return user.get_full_name() or user.email


def validar_anexos(arquivos) -> list:
    arquivos = list(arquivos or [])
    if len(arquivos) > MAX_ANEXOS:
        raise ValidationError({"anexos": f"Envie no máximo {MAX_ANEXOS} arquivos por mensagem."})
    for arquivo in arquivos:
        nome = getattr(arquivo, "name", "") or ""
        extensao = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
        if extensao not in EXTENSOES_PERMITIDAS:
            raise ValidationError({"anexos": f"Tipo de arquivo não permitido: {nome}."})
        if getattr(arquivo, "size", 0) > MAX_ANEXO_BYTES:
            raise ValidationError({"anexos": f"{nome} passa de 10 MB."})
    return arquivos


def _salvar_anexos(mensagem: MensagemChamado, arquivos):
    for arquivo in arquivos:
        AnexoChamado.objects.create(
            mensagem=mensagem,
            arquivo=arquivo,
            nome=(getattr(arquivo, "name", "") or "arquivo")[:255],
            tamanho=getattr(arquivo, "size", 0) or 0,
        )


def _link(chamado: Chamado) -> str:
    return frontend_url(f"/app/suporte/{chamado.pk}")


def _avisar_equipe(chamado: Chamado, texto: str, novo: bool):
    destino = getattr(settings, "SUPPORT_EMAIL", "")
    if not destino:
        return
    prefixo = "Novo chamado" if novo else "Nova resposta"
    corpo = (
        f"{prefixo} de {chamado.tenant.name} — {chamado.get_categoria_display()}\n"
        f"Por: {chamado.autor_nome} <{chamado.autor_email}>\n\n{texto}"
    )
    transaction.on_commit(
        lambda: enviar_email(
            destino,
            f"[Suporte #{chamado.pk}] {prefixo}: {chamado.assunto}",
            corpo,
            link=_link(chamado),
            link_label="Abrir chamado",
            reply_to=chamado.autor_email,
        )
    )


def _avisar_associacao(chamado: Chamado, texto: str):
    corpo = f"A equipe Gesttora respondeu ao seu chamado “{chamado.assunto}”:\n\n{texto}"
    transaction.on_commit(
        lambda: enviar_email(
            chamado.autor_email,
            f"[Suporte #{chamado.pk}] Resposta da equipe Gesttora",
            corpo,
            link=_link(chamado),
            link_label="Ver chamado",
        )
    )


@transaction.atomic
def abrir_chamado(user, dados: dict, arquivos) -> Chamado:
    tenant = tenant_do_user(user)
    if not tenant:
        raise ValidationError({"detail": "Usuário sem associação vinculada."})
    agora = timezone.now()
    chamado = Chamado.objects.create(
        tenant=tenant,
        assunto=dados["assunto"],
        categoria=dados.get("categoria") or Chamado.DUVIDA,
        prioridade=dados.get("prioridade") or Chamado.NORMAL,
        pagina=dados.get("pagina", ""),
        autor_id=str(user.pk),
        autor_nome=nome_do_user(user),
        autor_email=user.email,
        ultima_mensagem_em=agora,
    )
    mensagem = MensagemChamado.objects.create(
        chamado=chamado, autor_id=str(user.pk), autor_nome=nome_do_user(user), texto=dados["mensagem"]
    )
    _salvar_anexos(mensagem, arquivos)
    _avisar_equipe(chamado, dados["mensagem"], novo=True)
    return chamado


@transaction.atomic
def responder(chamado: Chamado, user, texto: str, arquivos, interna: bool = False) -> MensagemChamado:
    equipe = is_equipe(user)
    interna = interna and equipe
    mensagem = MensagemChamado.objects.create(
        chamado=chamado,
        autor_id=str(user.pk),
        autor_nome="Equipe Gesttora" if equipe and not user.get_full_name() else nome_do_user(user),
        da_equipe=equipe,
        interna=interna,
        texto=texto,
    )
    _salvar_anexos(mensagem, arquivos)
    if interna:
        return mensagem

    campos = ["ultima_mensagem_em", "updated_at"]
    chamado.ultima_mensagem_em = timezone.now()
    if equipe:
        if chamado.status in (Chamado.ABERTO, Chamado.EM_ANDAMENTO):
            chamado.status = Chamado.AGUARDANDO
        chamado.lido_pela_associacao = False
        chamado.lido_pela_equipe = True
        campos += ["status", "lido_pela_associacao", "lido_pela_equipe"]
        _avisar_associacao(chamado, texto)
    else:
        if chamado.status in Chamado.STATUS_ENCERRADOS:
            chamado.status = Chamado.ABERTO
        elif chamado.status == Chamado.AGUARDANDO:
            chamado.status = Chamado.EM_ANDAMENTO
        chamado.lido_pela_equipe = False
        chamado.lido_pela_associacao = True
        campos += ["status", "lido_pela_equipe", "lido_pela_associacao"]
        _avisar_equipe(chamado, texto, novo=False)
    chamado.save(update_fields=campos)
    return mensagem


def registrar_mudanca_status(chamado: Chamado, user, novo_status: str):
    if chamado.status == novo_status:
        return
    anterior = chamado.get_status_display()
    chamado.status = novo_status
    chamado.save(update_fields=["status", "updated_at"])
    MensagemChamado.objects.create(
        chamado=chamado,
        autor_id=str(user.pk),
        autor_nome=nome_do_user(user),
        da_equipe=is_equipe(user),
        interna=False,
        texto=f"Status alterado: {anterior} → {chamado.get_status_display()}.",
    )
