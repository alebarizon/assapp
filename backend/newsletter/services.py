"""
Segmentação, fila e envio da newsletter.

O envio nunca acontece na requisição: `enviar` só enfileira, e o comando
`enviar_newsletters` despacha a fila respeitando um limite por minuto.
"""
import logging
from email.utils import formataddr
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import connection, transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.html import escape, linebreaks, urlize
from rest_framework.exceptions import ValidationError

from contatos.models import Contato
from core.emails import frontend_url
from eventos.models import InscricaoEvento
from membros.models import Anuidade, AnuidadeStatus, FiliacaoStatus, Membro

from .models import Campanha, Descadastro, EnvioCampanha, StatusCampanha, StatusEnvio

logger = logging.getLogger(__name__)

SITUACOES = ("em_dia", "pendente", "inativo")
MAX_TENTATIVAS = 3


def situacoes_membros() -> dict:
    """membro_id → em_dia | pendente | inativo, com a mesma regra de `membro_adimplente`."""
    vigentes = set(
        Membro.objects.filter(
            ativo=True,
            filiacoes__status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA, FiliacaoStatus.INADIMPLENTE],
        ).values_list("id", flat=True)
    )
    regulares = set(
        Membro.objects.filter(
            ativo=True, filiacoes__status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA]
        ).values_list("id", flat=True)
    )
    devedores = set(
        Anuidade.objects.filter(
            status__in=[AnuidadeStatus.PENDENTE, AnuidadeStatus.VENCIDA],
            vencimento__lt=timezone.localdate(),
            valor__gt=0,
        ).values_list("filiacao__membro_id", flat=True)
    )
    situacao = {}
    for mid in Membro.objects.values_list("id", flat=True):
        if mid in regulares and mid not in devedores:
            situacao[mid] = "em_dia"
        elif mid in vigentes:
            situacao[mid] = "pendente"
        else:
            situacao[mid] = "inativo"
    return situacao


def _descadastrados() -> set:
    return {e.lower() for e in Descadastro.objects.values_list("email", flat=True)}


def destinatarios(publico: dict) -> list[dict]:
    """Une associados, inscritos em eventos e contatos com etiqueta; um destinatário por e-mail."""
    vistos: dict[str, dict] = {}

    def incluir(email, nome, origem, membro_id=None, contato_id=None):
        chave = (email or "").strip().lower()
        if not chave:
            return
        atual = vistos.get(chave)
        if atual is None:
            vistos[chave] = {
                "email": chave, "nome": nome or "", "origem": origem,
                "membro_id": membro_id, "contato_id": contato_id,
            }
        else:
            atual["membro_id"] = atual["membro_id"] or membro_id
            atual["contato_id"] = atual["contato_id"] or contato_id

    associados = publico.get("associados")
    if associados is not None:
        situacoes = set(associados.get("situacoes") or SITUACOES)
        tipos = associados.get("tipos") or []
        mapa = situacoes_membros()
        qs = Membro.objects.all()
        if tipos:
            qs = qs.filter(filiacoes__tipo__in=tipos).distinct()
        for m in qs.only("id", "email", "nome_completo"):
            if mapa.get(m.id) in situacoes:
                incluir(m.email, m.nome_completo, "associados", membro_id=m.id)

    eventos = publico.get("eventos") or []
    if eventos:
        for i in InscricaoEvento.objects.filter(evento_id__in=eventos).only("email", "nome", "membro_id"):
            incluir(i.email, i.nome, "eventos", membro_id=i.membro_id)

    etiquetas = publico.get("etiquetas") or []
    if etiquetas:
        contatos = Contato.objects.filter(etiquetas__in=etiquetas, consentimento_lgpd=True).distinct()
        for c in contatos.only("id", "email", "nome", "membro_id"):
            incluir(c.email, c.nome, "contatos", membro_id=c.membro_id, contato_id=c.id)

    fora = _descadastrados()
    return [d for email, d in sorted(vistos.items()) if email not in fora]


def resumo_publico(publico: dict) -> dict:
    lista = destinatarios(publico)
    por_origem = {"associados": 0, "eventos": 0, "contatos": 0}
    for d in lista:
        por_origem[d["origem"]] += 1
    return {"total": len(lista), "por_origem": por_origem, "descadastrados": Descadastro.objects.count()}


def _token(email: str, schema: str, campanha_id=None) -> str:
    dados = {"e": email.lower(), "c": str(campanha_id) if campanha_id else None}
    return signing.dumps(dados, salt=f"newsletter:{schema}", compress=True)


def ler_token(token: str, schema: str) -> dict | None:
    try:
        dados = signing.loads(token, salt=f"newsletter:{schema}")
    except signing.BadSignature:
        return None
    return dados if isinstance(dados, dict) and dados.get("e") else None


def link_descadastro(email: str, schema: str, campanha_id=None) -> str:
    query = urlencode({"schema": schema, "t": _token(email, schema, campanha_id)})
    return frontend_url(f"/site/descadastrar?{query}")


def _url_one_click(email: str, schema: str, campanha_id=None) -> str:
    query = urlencode({"schema": schema, "t": _token(email, schema, campanha_id)})
    return frontend_url(f"/api/newsletter/public/descadastrar/?{query}")


def _remetente() -> str:
    padrao = settings.DEFAULT_FROM_EMAIL
    if "<" in padrao:
        return padrao
    nome = getattr(getattr(connection, "tenant", None), "name", "") or ""
    return formataddr((nome, padrao)) if nome else padrao


def _personalizar(texto: str, nome: str) -> str:
    primeiro = (nome or "").split(" ")[0] or "associado(a)"
    return texto.replace("{nome}", primeiro)


def montar_email(campanha: Campanha, email: str, nome: str, schema: str, conexao=None, assunto=None):
    corpo = _personalizar(campanha.corpo, nome)
    sair = link_descadastro(email, schema, campanha.pk)
    associacao = getattr(getattr(connection, "tenant", None), "name", "") or "a associação"
    texto = corpo
    if campanha.link:
        texto += f"\n\n{campanha.link_label or 'Saiba mais'}: {campanha.link}"
    texto += f"\n\n--\nVocê recebe este e-mail por seu vínculo com {associacao}.\nPara não receber mais: {sair}"

    botao = ""
    if campanha.link:
        botao = (
            f'<p style="margin-top:24px"><a href="{escape(campanha.link)}" '
            'style="background:#1a5f4a;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none">'
            f"{escape(campanha.link_label or 'Saiba mais')}</a></p>"
        )
    html = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;color:#0f172a;max-width:640px">'
        f"{linebreaks(urlize(corpo, autoescape=True))}{botao}"
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:32px 0 12px">'
        f'<p style="color:#64748b;font-size:12px">Você recebe este e-mail por seu vínculo com {escape(associacao)}. '
        f'<a href="{escape(sair)}" style="color:#64748b">Não quero mais receber</a>.</p></div>'
    )
    msg = EmailMultiAlternatives(
        subject=assunto or campanha.assunto,
        body=texto,
        from_email=_remetente(),
        to=[email],
        connection=conexao,
        headers={
            "List-Unsubscribe": f"<{_url_one_click(email, schema, campanha.pk)}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )
    msg.attach_alternative(html, "text/html")
    return msg


def enviar_teste(campanha: Campanha, email: str, nome: str = "") -> bool:
    try:
        montar_email(campanha, email, nome, connection.schema_name, assunto=f"[Teste] {campanha.assunto}").send()
        return True
    except Exception:
        logger.exception("Falha no envio de teste da campanha %s", campanha.pk)
        return False


@transaction.atomic
def enviar(campanha: Campanha) -> int:
    campanha = Campanha.objects.select_for_update().get(pk=campanha.pk)
    if campanha.status != StatusCampanha.RASCUNHO:
        raise ValidationError("Esta campanha já foi enviada ou cancelada.")
    lista = destinatarios(campanha.publico)
    if not lista:
        raise ValidationError("Nenhum destinatário no público escolhido.")
    EnvioCampanha.objects.bulk_create(
        EnvioCampanha(
            campanha=campanha, email=d["email"], nome=d["nome"][:255],
            membro_id=d["membro_id"], contato_id=d["contato_id"],
        )
        for d in lista
    )
    campanha.status = StatusCampanha.ENVIANDO
    campanha.enviada_em = timezone.now()
    campanha.save(update_fields=["status", "enviada_em", "updated_at"])
    return len(lista)


@transaction.atomic
def cancelar(campanha: Campanha) -> int:
    if campanha.status not in (StatusCampanha.RASCUNHO, StatusCampanha.ENVIANDO):
        raise ValidationError("Esta campanha já terminou.")
    cancelados = campanha.envios.filter(status=StatusEnvio.PENDENTE).update(status=StatusEnvio.CANCELADO)
    campanha.status = StatusCampanha.CANCELADA
    campanha.concluida_em = timezone.now()
    campanha.save(update_fields=["status", "concluida_em", "updated_at"])
    return cancelados


def _concluir_terminadas():
    for campanha in Campanha.objects.filter(status=StatusCampanha.ENVIANDO):
        if not campanha.envios.filter(status=StatusEnvio.PENDENTE).exists():
            campanha.status = StatusCampanha.ENVIADA
            campanha.concluida_em = timezone.now()
            campanha.save(update_fields=["status", "concluida_em", "updated_at"])


def processar_fila(limite: int) -> dict:
    """Despacha até `limite` e-mails pendentes da associação atual."""
    schema = connection.schema_name
    with transaction.atomic():
        lote = list(
            EnvioCampanha.objects.select_for_update(skip_locked=True)
            .filter(status=StatusEnvio.PENDENTE, campanha__status=StatusCampanha.ENVIANDO)
            .select_related("campanha")
            .order_by("id")[:limite]
        )
        fora = _descadastrados()
        enviados = falhas = 0
        conexao = get_connection() if lote else None
        try:
            if conexao:
                conexao.open()
            for envio in lote:
                if envio.email.lower() in fora:
                    envio.status = StatusEnvio.CANCELADO
                    envio.erro = "Descadastrado"
                    envio.save(update_fields=["status", "erro"])
                    continue
                envio.tentativas += 1
                try:
                    montar_email(envio.campanha, envio.email, envio.nome, schema, conexao).send()
                    envio.status = StatusEnvio.ENVIADO
                    envio.enviado_em = timezone.now()
                    envio.erro = ""
                    enviados += 1
                except Exception as exc:
                    logger.warning("Newsletter: falha para %s: %s", envio.email, exc)
                    envio.erro = str(exc)[:255]
                    if envio.tentativas >= MAX_TENTATIVAS:
                        envio.status = StatusEnvio.FALHA
                    falhas += 1
                envio.save(update_fields=["status", "tentativas", "erro", "enviado_em"])
        finally:
            if conexao:
                conexao.close()
    _concluir_terminadas()
    return {"enviados": enviados, "falhas": falhas, "processados": len(lote)}


def estatisticas(campanha: Campanha) -> dict:
    contagem = {s: 0 for s, _ in StatusEnvio.choices}
    for row in campanha.envios.values("status").annotate(n=Count("id")):
        contagem[row["status"]] = row["n"]
    return {
        "total": sum(contagem.values()),
        **contagem,
        "descadastros": campanha.descadastros.count(),
    }


def descadastrar(email: str, campanha_id=None) -> Descadastro:
    email = email.strip().lower()
    campanha = Campanha.objects.filter(pk=campanha_id).first() if campanha_id else None
    obj, _ = Descadastro.objects.get_or_create(email=email, defaults={"campanha": campanha})
    return obj
