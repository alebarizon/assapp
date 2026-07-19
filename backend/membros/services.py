"""Serviços — geração e renovação de anuidades + ponte User↔Membro."""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from mandatos.models import Mandato

from .models import Anuidade, AnuidadeStatus, Filiacao, FiliacaoStatus, Membro


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


def registrar_pagamento(anuidade: Anuidade, nf_numero: str = None, user=None) -> Anuidade:
    """Registra pagamento, reativa filiação e espelha no finance (idempotente)."""
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
