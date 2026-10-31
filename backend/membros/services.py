"""Serviços — geração e renovação de anuidades, régua de cobrança + ponte User↔Membro."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from mandatos.models import Mandato

from .models import (
    Anuidade,
    AnuidadeStatus,
    Filiacao,
    FiliacaoStatus,
    LembreteAnuidade,
    Membro,
)


# Valores padrão por tipo de filiação (configurável futuramente via settings do tenant)
VALORES_ANUIDADE_PADRAO = {
    "efetivo": Decimal("80.00"),
    "estudante": Decimal("40.00"),
    "honorario": Decimal("0.00"),
    "institucional": Decimal("200.00"),
}


def get_valor_anuidade(tipo_filiacao: str) -> Decimal:
    return VALORES_ANUIDADE_PADRAO.get(tipo_filiacao, Decimal("80.00"))


def gerar_anuidades_ano(
    ano: int,
    valor: Decimal | None = None,
    vencimento: date | None = None,
    mandato: Mandato | None = None,
) -> dict:
    """
    Gera anuidades para todas as filiações ativas que ainda não possuem
    cobrança no ano de referência.
    """
    if vencimento is None:
        vencimento = date(ano, 3, 31)  # padrão: 31/mar

    filiacoes = Filiacao.objects.filter(
        status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.INADIMPLENTE],
        data_fim__isnull=True,
    ).select_related("membro")

    criadas = 0
    ignoradas = 0

    for filiacao in filiacoes:
        if Anuidade.objects.filter(filiacao=filiacao, ano_referencia=ano).exists():
            ignoradas += 1
            continue

        valor_cobranca = valor if valor is not None else get_valor_anuidade(filiacao.tipo)
        status = AnuidadeStatus.ISENTA if valor_cobranca == 0 else AnuidadeStatus.PENDENTE

        Anuidade.objects.create(
            filiacao=filiacao,
            ano_referencia=ano,
            valor=valor_cobranca,
            vencimento=vencimento,
            status=status,
        )
        criadas += 1

    return {"ano": ano, "criadas": criadas, "ignoradas": ignoradas}


def atualizar_anuidades_vencidas() -> dict:
    """Marca anuidades pendentes vencidas e filiações como inadimplentes."""
    hoje = timezone.now().date()
    vencidas = Anuidade.objects.filter(
        status=AnuidadeStatus.PENDENTE,
        vencimento__lt=hoje,
    ).select_related("filiacao")

    count_anuidades = 0
    filiacoes_afetadas = set()

    for anuidade in vencidas:
        anuidade.status = AnuidadeStatus.VENCIDA
        anuidade.save(update_fields=["status"])
        count_anuidades += 1
        filiacoes_afetadas.add(anuidade.filiacao_id)

    Filiacao.objects.filter(
        id__in=filiacoes_afetadas,
        status=FiliacaoStatus.ATIVA,
    ).update(status=FiliacaoStatus.INADIMPLENTE)

    return {
        "anuidades_vencidas": count_anuidades,
        "filiacoes_inadimplentes": len(filiacoes_afetadas),
    }


_ETAPAS_ORDEM = [etapa for etapa, _ in LembreteAnuidade.OFFSETS]

# Fora desta janela a anuidade não entra na régua (evita disparar lembretes de
# cobranças antigas na primeira execução).
_JANELA_ANTES = 30
_JANELA_DEPOIS = 45


def etapa_devida(anuidade: Anuidade, hoje: date) -> str | None:
    """Etapa mais recente da régua já alcançada pela anuidade em `hoje`."""
    dias = (hoje - anuidade.vencimento).days
    devida = None
    for etapa, offset in LembreteAnuidade.OFFSETS:
        if dias >= offset:
            devida = etapa
    return devida


def _texto_lembrete(anuidade: Anuidade, etapa: str, associacao: str) -> tuple[str, str]:
    membro = anuidade.filiacao.membro
    venc = anuidade.vencimento.strftime("%d/%m/%Y")
    valor = f"R$ {anuidade.valor:.2f}".replace(".", ",")
    ano = anuidade.ano_referencia
    primeiro_nome = membro.nome_completo.split(" ")[0]

    if etapa in (LembreteAnuidade.ANTES_30, LembreteAnuidade.ANTES_15):
        assunto = f"Sua anuidade {ano} vence em {venc}"
        abertura = f"Sua anuidade {ano} na {associacao} vence em {venc}."
    elif etapa == LembreteAnuidade.NO_DIA:
        assunto = f"Sua anuidade {ano} vence hoje"
        abertura = f"Sua anuidade {ano} na {associacao} vence hoje ({venc})."
    else:
        assunto = f"Anuidade {ano} em aberto"
        abertura = (
            f"Ainda não identificamos o pagamento da sua anuidade {ano} na {associacao}, "
            f"vencida em {venc}. Com a anuidade em aberto, sua filiação fica como inadimplente."
        )

    texto = (
        f"Olá, {primeiro_nome}.\n\n"
        f"{abertura}\n\n"
        f"Valor: {valor}\n\n"
        "Você pode pagar pelo portal do associado. Se já pagou, desconsidere esta mensagem."
    )
    return assunto, texto


def enviar_lembretes_anuidade(hoje: date | None = None, request=None) -> dict:
    """
    Régua de cobrança: envia, para cada anuidade em aberto, o lembrete da etapa
    mais recente ainda não enviada. Idempotente — pode rodar várias vezes ao dia.
    """
    from core import cota_email
    from core.emails import enviar_email, frontend_url, nome_associacao

    hoje = hoje or timezone.now().date()
    associacao = nome_associacao(request)
    link = frontend_url("/app/portal/perfil")

    anuidades = (
        Anuidade.objects.filter(
            status__in=[AnuidadeStatus.PENDENTE, AnuidadeStatus.VENCIDA],
            valor__gt=0,
            vencimento__gte=hoje - timedelta(days=_JANELA_DEPOIS),
            vencimento__lte=hoje + timedelta(days=_JANELA_ANTES),
            filiacao__membro__ativo=True,
        )
        .select_related("filiacao__membro")
        .prefetch_related("lembretes")
    )

    enviados = 0
    falhas = 0
    por_etapa = {etapa: 0 for etapa in _ETAPAS_ORDEM}

    for anuidade in anuidades:
        etapa = etapa_devida(anuidade, hoje)
        if not etapa:
            continue
        indice = _ETAPAS_ORDEM.index(etapa)
        ja_enviadas = {lembrete.etapa for lembrete in anuidade.lembretes.all()}
        if any(_ETAPAS_ORDEM.index(e) >= indice for e in ja_enviadas):
            continue

        if not cota_email.cabe():
            break
        email = anuidade.filiacao.membro.email
        assunto, texto = _texto_lembrete(anuidade, etapa, associacao)
        if enviar_email(email, assunto, texto, link=link, link_label="Pagar anuidade", fila=False):
            LembreteAnuidade.objects.create(anuidade=anuidade, etapa=etapa, email=email)
            enviados += 1
            por_etapa[etapa] += 1
        else:
            falhas += 1

    return {"enviados": enviados, "falhas": falhas, "por_etapa": por_etapa}


def registrar_pagamento(anuidade: Anuidade, nf_numero: str = None, user=None) -> Anuidade:
    """Registra pagamento, reativa filiação e espelha no finance (idempotente)."""
    if anuidade.status == AnuidadeStatus.PAGA:
        return anuidade
    anuidade.status = AnuidadeStatus.PAGA
    anuidade.pago_em = timezone.now()
    if nf_numero:
        anuidade.nf_numero = nf_numero
    anuidade.save()

    filiacao = anuidade.filiacao
    if filiacao.status == FiliacaoStatus.INADIMPLENTE:
        filiacao.status = FiliacaoStatus.ATIVA
        filiacao.save(update_fields=["status"])

    try:
        from finance.services import espelhar_pagamento_anuidade

        espelhar_pagamento_anuidade(anuidade, user=user)
    except Exception:
        pass

    from integracoes.services import disparar

    membro = filiacao.membro
    disparar(
        "anuidade.paga",
        {
            "id": str(anuidade.id),
            "ano_referencia": anuidade.ano_referencia,
            "valor": f"{anuidade.valor:.2f}",
            "pago_em": anuidade.pago_em.isoformat(),
            "membro": {"id": str(membro.id), "nome": membro.nome_completo, "email": membro.email},
        },
    )
    return anuidade


def criar_membro_com_filiacao(
    dados_membro: dict,
    tipo_filiacao: str = "efetivo",
    mandato: Mandato | None = None,
) -> tuple[Membro, Filiacao]:
    """Cria membro e primeira filiação em uma operação."""
    membro = Membro.objects.create(**dados_membro)
    filiacao = Filiacao.objects.create(
        membro=membro,
        mandato=mandato,
        tipo=tipo_filiacao,
        status=FiliacaoStatus.ATIVA,
        data_inicio=timezone.now().date(),
    )
    return membro, filiacao


def resumo_quadro() -> dict:
    """KPIs do quadro de associados para dashboard."""
    total = Membro.objects.filter(ativo=True).count()
    ativos = Filiacao.objects.filter(status=FiliacaoStatus.ATIVA).count()
    inadimplentes = Filiacao.objects.filter(status=FiliacaoStatus.INADIMPLENTE).count()
    anuidades_pendentes = Anuidade.objects.filter(status=AnuidadeStatus.PENDENTE).count()
    anuidades_vencidas = Anuidade.objects.filter(status=AnuidadeStatus.VENCIDA).count()

    return {
        "total_membros": total,
        "filiacoes_ativas": ativos,
        "filiacoes_inadimplentes": inadimplentes,
        "anuidades_pendentes": anuidades_pendentes,
        "anuidades_vencidas": anuidades_vencidas,
    }


def membro_adimplente(membro: Membro | None) -> bool:
    """Sócio em dia: filiação ativa/honorária e nenhuma anuidade em atraso (mesmo antes do cron marcar vencida)."""
    if not membro or not membro.ativo:
        return False
    if not membro.filiacoes.filter(
        status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA]
    ).exists():
        return False
    return not Anuidade.objects.filter(
        filiacao__membro=membro,
        status__in=[AnuidadeStatus.PENDENTE, AnuidadeStatus.VENCIDA],
        vencimento__lt=timezone.localdate(),
        valor__gt=0,
    ).exists()


def vincular_user(membro: Membro, user) -> Membro:
    """
    Liga Membro ↔ User (OneToOne).
    Bloqueia se o User já estiver em outro membro; e-mails devem coincidir se ambos existir.
    """
    if user is None:
        raise ValidationError({"user": "Informe o usuário."})

    outro = Membro.objects.filter(user=user).exclude(pk=membro.pk).first()
    if outro:
        raise ValidationError(
            {"user": f"Usuário já vinculado ao membro {outro.nome_completo}."}
        )

    if membro.email and user.email:
        if membro.email.strip().lower() != user.email.strip().lower():
            raise ValidationError(
                {
                    "user": (
                        "E-mail do usuário difere do membro. "
                        "Alinhe os e-mails antes de vincular."
                    )
                }
            )

    membro.user = user
    membro.save(update_fields=["user", "updated_at"])
    return membro


def desvincular_user(membro: Membro) -> Membro:
    membro.user = None
    membro.save(update_fields=["user", "updated_at"])
    return membro


def resolver_membro_do_user(user, auto_link: bool = True) -> Membro | None:
    """
    Resolve o Membro do User: FK primeiro; fallback e-mail (iexact).
    Se auto_link e match por e-mail sem FK, preenche a FK (evita match fantasma).
    """
    if not user:
        return None

    try:
        return user.membro_perfil
    except Membro.DoesNotExist:
        pass

    email = getattr(user, "email", None)
    if not email:
        return None

    membro = Membro.objects.filter(email__iexact=email).first()
    if membro and auto_link and membro.user_id is None:
        if not Membro.objects.filter(user=user).exists():
            membro.user = user
            membro.save(update_fields=["user", "updated_at"])
    return membro
