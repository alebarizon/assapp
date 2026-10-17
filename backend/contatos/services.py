from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from core.emails import enviar_email, frontend_url
from membros.models import Membro
from membros.services import criar_membro_com_filiacao

from .models import Contato, Nota


def nota_sistema(contato: Contato, texto: str, autor=None, tipo: str = Nota.SISTEMA) -> Nota:
    return Nota.objects.create(contato=contato, tipo=tipo, texto=texto, autor=autor)


def registrar_contato_publico(dados: dict) -> tuple[Contato, bool]:
    """
    Cria o contato vindo do site. Se já existe um contato em aberto com o mesmo
    e-mail, a nova mensagem vira nota nele (evita duplicar o funil).
    Retorna (contato, criado).
    """
    email = dados["email"].strip().lower()
    existente = (
        Contato.objects.filter(email__iexact=email, etapa__in=Contato.ETAPAS_ABERTAS)
        .order_by("-created_at")
        .first()
    )
    agora = timezone.now()
    if existente:
        assunto = dict(Contato.ASSUNTO_CHOICES).get(dados.get("assunto"), "")
        texto = dados.get("mensagem") or "(sem mensagem)"
        nota_sistema(existente, f"{assunto}: {texto}" if assunto else texto, tipo=Nota.MENSAGEM)
        campos = ["ultima_interacao_em", "updated_at"]
        for campo in ("telefone", "instituicao"):
            if dados.get(campo) and not getattr(existente, campo):
                setattr(existente, campo, dados[campo])
                campos.append(campo)
        existente.ultima_interacao_em = agora
        existente.save(update_fields=campos)
        return existente, False

    contato = Contato.objects.create(
        nome=dados["nome"],
        email=email,
        telefone=dados.get("telefone", ""),
        instituicao=dados.get("instituicao", ""),
        assunto=dados.get("assunto") or "outro",
        mensagem=dados.get("mensagem", ""),
        origem=dados.get("origem") or Contato.SITE_CONTATO,
        consentimento_lgpd=True,
        ultima_interacao_em=agora,
    )
    membro = Membro.objects.filter(email__iexact=email).first()
    if membro:
        contato.membro = membro
        contato.save(update_fields=["membro"])
        nota_sistema(contato, "Este e-mail já pertence a um associado cadastrado.")
    return contato, True


def notificar_associacao(contato: Contato, destinatario: str, associacao: str, criado: bool) -> bool:
    if not destinatario:
        return False
    assunto_label = contato.get_assunto_display()
    prefixo = "Novo contato" if criado else "Nova mensagem"
    texto = (
        f"{prefixo} recebido pelo site de {associacao}.\n\n"
        f"Nome: {contato.nome}\nE-mail: {contato.email}\n"
        f"Telefone: {contato.telefone or '—'}\nAssunto: {assunto_label}\n\n"
        f"{contato.mensagem if criado else contato.notas.first().texto}"
    )
    return enviar_email(
        destinatario,
        f"[{associacao}] {prefixo}: {contato.nome}",
        texto,
        link=frontend_url(f"/app/contatos/{contato.id}"),
        link_label="Abrir no Gesttora",
        reply_to=contato.email,
    )


@transaction.atomic
def converter_em_membro(contato: Contato, user, tipo_filiacao: str | None = None) -> tuple[Membro, bool]:
    """Vincula a um associado existente (mesmo e-mail) ou cria um novo. Retorna (membro, criado)."""
    membro = contato.membro or Membro.objects.filter(email__iexact=contato.email).first()
    criado = False
    if not membro:
        dados = {
            "nome_completo": contato.nome,
            "email": contato.email,
            "telefone": contato.telefone[:20] or None,
            "instituicao": contato.instituicao or None,
            "consentimento_lgpd": contato.consentimento_lgpd,
            "consentimento_em": contato.created_at if contato.consentimento_lgpd else None,
        }
        if tipo_filiacao:
            membro, _ = criar_membro_com_filiacao(dados, tipo_filiacao=tipo_filiacao)
        else:
            membro = Membro.objects.create(**dados)
        criado = True
    contato.membro = membro
    contato.etapa = Contato.CONVERTIDO
    contato.save(update_fields=["membro", "etapa", "updated_at"])
    nota_sistema(
        contato,
        "Convertido em associado (novo cadastro)." if criado else "Vinculado a associado já cadastrado.",
        autor=user,
    )
    return membro, criado


def resumo_funil() -> dict:
    contagem = {etapa: 0 for etapa, _ in Contato.ETAPA_CHOICES}
    for row in Contato.objects.values("etapa").annotate(total=Count("id")):
        contagem[row["etapa"]] = row["total"]
    return contagem
