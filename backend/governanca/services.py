"""Regras de assembleias e votações: censo, voto, apuração, quórum, ata e registro na memória."""
from __future__ import annotations

import hashlib
import secrets
from io import BytesIO

from django.db import transaction
from django.utils import timezone

from mandatos.models import Mandato
from membros.models import FiliacaoStatus, Membro
from membros.services import membro_adimplente

from .models import (
    Assembleia,
    AssembleiaStatus,
    Cedula,
    CensoVotacao,
    Eleitor,
    OpcaoVotacao,
    PresencaAssembleia,
    TipoVotacao,
    Votacao,
    VotacaoStatus,
)

OPCOES_DELIBERACAO = ["Aprovo", "Rejeito", "Abstenção"]


class GovernancaError(Exception):
    pass


def membros_ativos():
    return (
        Membro.objects.filter(ativo=True, filiacoes__status__in=[FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA])
        .distinct()
        .order_by("nome_completo")
    )


def censo(regra: str = CensoVotacao.ADIMPLENTES) -> list[Membro]:
    ativos = list(membros_ativos())
    if regra == CensoVotacao.ATIVOS:
        return ativos
    return [m for m in ativos if membro_adimplente(m)]


def _mandato_da(obj) -> Mandato | None:
    return obj.mandato or Mandato.get_ativo()


def _registrar_memoria(*, mandato, autor, tipo, titulo, conteudo, decisao, entidade_tipo, entidade_id, tags):
    from memoria.models import ContextoHistorico

    return ContextoHistorico.objects.create(
        mandato=mandato,
        autor=autor,
        tipo=tipo,
        titulo=titulo[:255],
        conteudo=conteudo,
        decisao=decisao[:500],
        entidade_tipo=entidade_tipo,
        entidade_id=entidade_id,
        tags=["governanca", *tags],
    )


# ---------------------------------------------------------------- votações


@transaction.atomic
def abrir_votacao(votacao: Votacao) -> int:
    if votacao.status != VotacaoStatus.RASCUNHO:
        raise GovernancaError("Só votações em rascunho podem ser abertas.")
    existentes = OpcaoVotacao.objects.filter(votacao=votacao)
    if votacao.tipo == TipoVotacao.DELIBERACAO and not existentes.exists():
        OpcaoVotacao.objects.bulk_create(
            OpcaoVotacao(votacao=votacao, titulo=t, ordem=i) for i, t in enumerate(OPCOES_DELIBERACAO)
        )
    opcoes = existentes.count()
    if opcoes < 2:
        raise GovernancaError("Cadastre ao menos duas opções (ou chapas).")
    if votacao.max_escolhas < 1 or votacao.max_escolhas > opcoes:
        raise GovernancaError("Número máximo de escolhas inválido.")
    eleitores = censo(votacao.censo)
    if not eleitores:
        raise GovernancaError("Nenhum associado apto a votar pelo critério escolhido.")
    Eleitor.objects.bulk_create(Eleitor(votacao=votacao, membro=m) for m in eleitores)
    votacao.status = VotacaoStatus.ABERTA
    votacao.aberta_em = timezone.now()
    votacao.mandato = _mandato_da(votacao)
    votacao.save(update_fields=["status", "aberta_em", "mandato", "updated_at"])
    return len(eleitores)


def recebendo_votos(votacao: Votacao) -> bool:
    return votacao.status == VotacaoStatus.ABERTA and not (votacao.fecha_em and timezone.now() > votacao.fecha_em)


@transaction.atomic
def votar(votacao: Votacao, membro: Membro, opcao_ids: list) -> str:
    if not recebendo_votos(votacao):
        raise GovernancaError("Esta votação não está recebendo votos.")
    eleitor = Eleitor.objects.select_for_update().filter(votacao=votacao, membro=membro).first()
    if not eleitor:
        raise GovernancaError("Você não está no censo desta votação.")
    if eleitor.votou_em:
        raise GovernancaError("Seu voto já foi registrado.")
    ids = {str(i) for i in opcao_ids}
    opcoes = list(votacao.opcoes.filter(id__in=ids))
    if len(opcoes) != len(ids):
        raise GovernancaError("Opção inválida.")
    if not opcoes and not votacao.permite_branco:
        raise GovernancaError("Escolha ao menos uma opção.")
    if len(opcoes) > votacao.max_escolhas:
        raise GovernancaError(f"Escolha no máximo {votacao.max_escolhas} opção(ões).")
    cedula = Cedula.objects.create(
        votacao=votacao,
        eleitor=None if votacao.secreta else eleitor,
        comprovante=secrets.token_hex(6).upper(),
    )
    cedula.opcoes.set(opcoes)
    eleitor.votou_em = timezone.now()
    eleitor.save(update_fields=["votou_em"])
    return cedula.comprovante


def participacao(votacao: Votacao) -> dict:
    total = votacao.eleitores.count()
    votantes = votacao.eleitores.filter(votou_em__isnull=False).count()
    return {
        "eleitores": total,
        "votantes": votantes,
        "participacao_pct": round(100 * votantes / total, 1) if total else 0,
    }


def apurar(votacao: Votacao) -> dict:
    resultado = participacao(votacao)
    cedulas = votacao.cedulas.count()
    brancos = votacao.cedulas.filter(opcoes__isnull=True).count()
    validos = cedulas - brancos
    opcoes = []
    for opcao in votacao.opcoes.all():
        votos = opcao.cedulas.count()
        opcoes.append(
            {
                "id": opcao.id,
                "titulo": opcao.titulo,
                "votos": votos,
                "pct_validos": round(100 * votos / validos, 1) if validos else 0,
            }
        )
    maior = max((o["votos"] for o in opcoes), default=0)
    lideres = [o for o in opcoes if o["votos"] == maior and maior > 0]
    resultado.update(
        {
            "cedulas": cedulas,
            "brancos": brancos,
            "opcoes": sorted(opcoes, key=lambda o: -o["votos"]),
            "vencedora": lideres[0]["id"] if len(lideres) == 1 else None,
            "empate": len(lideres) > 1,
        }
    )
    return resultado


def _texto_resultado(votacao: Votacao, r: dict) -> tuple[str, str]:
    linhas = [f"{o['titulo']}: {o['votos']} voto(s) ({o['pct_validos']}% dos válidos)" for o in r["opcoes"]]
    linhas.append(f"Brancos: {r['brancos']}")
    linhas.append(f"Participação: {r['votantes']} de {r['eleitores']} aptos ({r['participacao_pct']}%)")
    if r["empate"]:
        decisao = "Empate entre as opções mais votadas."
    elif r["vencedora"]:
        vencedora = next(o["titulo"] for o in r["opcoes"] if o["id"] == r["vencedora"])
        decisao = f"{'Eleita' if votacao.tipo == TipoVotacao.ELEICAO else 'Resultado'}: {vencedora}"
    else:
        decisao = "Sem votos válidos."
    return "\n".join(linhas), decisao


@transaction.atomic
def encerrar_votacao(votacao: Votacao, user=None) -> dict:
    from memoria.models import TipoContextoHistorico

    if votacao.status != VotacaoStatus.ABERTA:
        raise GovernancaError("Só votações abertas podem ser encerradas.")
    resultado = apurar(votacao)
    votacao.status = VotacaoStatus.ENCERRADA
    votacao.encerrada_em = timezone.now()
    votacao.resultado = resultado
    votacao.save(update_fields=["status", "encerrada_em", "resultado", "updated_at"])
    conteudo, decisao = _texto_resultado(votacao, resultado)
    _registrar_memoria(
        mandato=votacao.mandato,
        autor=user,
        tipo=TipoContextoHistorico.DECISAO,
        titulo=f"Resultado — {votacao.titulo}",
        conteudo=conteudo,
        decisao=decisao,
        entidade_tipo="votacao",
        entidade_id=votacao.id,
        tags=[votacao.tipo],
    )
    return resultado


# ---------------------------------------------------------------- assembleias


def convocar(assembleia: Assembleia, notificar: bool = True) -> int:
    from core.emails import enviar_email, frontend_url, nome_associacao

    if assembleia.status not in (AssembleiaStatus.RASCUNHO, AssembleiaStatus.CONVOCADA):
        raise GovernancaError("Esta assembleia não pode mais ser convocada.")
    assembleia.status = AssembleiaStatus.CONVOCADA
    assembleia.convocada_em = timezone.now()
    assembleia.mandato = _mandato_da(assembleia)
    assembleia.save(update_fields=["status", "convocada_em", "mandato", "updated_at"])
    if not notificar:
        return 0
    quando = timezone.localtime(assembleia.data_hora).strftime("%d/%m/%Y às %H:%M")
    onde = " · ".join(filter(None, [assembleia.local, assembleia.link_online]))
    pauta = "\n".join(f"{i}. {item}" for i, item in enumerate(assembleia.pauta, 1))
    texto = (
        f"{nome_associacao()} convoca seus associados para a assembleia {assembleia.get_tipo_display().lower()} "
        f"\"{assembleia.titulo}\", em {quando}" + (f" ({onde})" if onde else "") + ".\n\n"
        + (f"{assembleia.convocacao}\n\n" if assembleia.convocacao else "")
        + (f"Ordem do dia:\n{pauta}" if pauta else "")
    )
    enviados = 0
    for email in membros_ativos().exclude(email="").values_list("email", flat=True):
        enviados += enviar_email(
            email,
            f"Convocação: {assembleia.titulo}",
            texto,
            link=frontend_url("/app/portal/governanca"),
            link_label="Ver no portal",
        )
    return enviados


def mudar_status(assembleia: Assembleia, novo: str) -> None:
    permitidos = {
        AssembleiaStatus.EM_ANDAMENTO: [AssembleiaStatus.CONVOCADA],
        AssembleiaStatus.ENCERRADA: [AssembleiaStatus.EM_ANDAMENTO],
        AssembleiaStatus.CANCELADA: [AssembleiaStatus.RASCUNHO, AssembleiaStatus.CONVOCADA],
    }
    if assembleia.status not in permitidos[novo]:
        raise GovernancaError("Mudança de situação não permitida.")
    assembleia.status = novo
    campos = ["status", "updated_at"]
    if novo == AssembleiaStatus.ENCERRADA:
        assembleia.encerrada_em = timezone.now()
        campos.append("encerrada_em")
    assembleia.save(update_fields=campos)


def registrar_presenca(assembleia: Assembleia, membro: Membro, forma: str, user=None) -> PresencaAssembleia:
    if assembleia.status not in (AssembleiaStatus.CONVOCADA, AssembleiaStatus.EM_ANDAMENTO):
        raise GovernancaError("Presença só pode ser registrada em assembleia convocada ou em andamento.")
    presenca, _ = PresencaAssembleia.objects.get_or_create(
        assembleia=assembleia, membro=membro, defaults={"forma": forma, "registrada_por": user}
    )
    return presenca


def quorum(assembleia: Assembleia) -> dict:
    aptos = {m.id for m in censo(CensoVotacao.ADIMPLENTES)}
    presencas = set(assembleia.presencas.values_list("membro_id", flat=True))
    presentes_aptos = len(presencas & aptos)
    pct = round(100 * presentes_aptos / len(aptos), 1) if aptos else 0
    minimo = assembleia.quorum_minimo
    return {
        "aptos": len(aptos),
        "presentes": len(presencas),
        "presentes_aptos": presentes_aptos,
        "pct": pct,
        "minimo": minimo,
        "atingido": None if minimo is None else pct >= minimo,
    }


def gerar_ata(assembleia: Assembleia) -> str:
    from core.emails import nome_associacao

    q = quorum(assembleia)
    quando = timezone.localtime(assembleia.data_hora)
    linhas = [
        f"ATA DA ASSEMBLEIA {assembleia.get_tipo_display().upper()} — {assembleia.titulo.upper()}",
        "",
        f"Aos {quando.strftime('%d/%m/%Y')}, às {quando.strftime('%H:%M')}, "
        f"{'em ' + assembleia.local if assembleia.local else 'em ambiente virtual'}, "
        f"reuniram-se os associados de {nome_associacao()}, em assembleia "
        f"{assembleia.get_tipo_display().lower()} ({assembleia.get_modalidade_display().lower()}).",
        f"Presentes: {q['presentes']} associado(s), sendo {q['presentes_aptos']} de {q['aptos']} "
        f"aptos a votar ({q['pct']}%)."
        + (
            f" Quórum mínimo de {q['minimo']}% {'atingido' if q['atingido'] else 'não atingido'}."
            if q["minimo"] is not None
            else ""
        ),
    ]
    if assembleia.pauta:
        linhas += ["", "ORDEM DO DIA"] + [f"{i}. {item}" for i, item in enumerate(assembleia.pauta, 1)]
    votacoes = assembleia.votacoes.filter(status=VotacaoStatus.ENCERRADA)
    if votacoes:
        linhas += ["", "DELIBERAÇÕES"]
        for v in votacoes:
            conteudo, decisao = _texto_resultado(v, v.resultado or apurar(v))
            linhas += [f"{v.titulo}", conteudo, decisao, ""]
    linhas += ["", "Nada mais havendo a tratar, a assembleia foi encerrada e lavrada a presente ata."]
    return "\n".join(linhas)


@transaction.atomic
def publicar_ata(assembleia: Assembleia, user=None) -> Assembleia:
    from memoria.models import TipoContextoHistorico

    if assembleia.status != AssembleiaStatus.ENCERRADA:
        raise GovernancaError("Encerre a assembleia antes de publicar a ata.")
    if assembleia.ata_publicada_em:
        raise GovernancaError("A ata já foi publicada.")
    if not assembleia.ata.strip():
        raise GovernancaError("Escreva a ata antes de publicar.")
    assembleia.ata_hash = hashlib.sha256(assembleia.ata.encode()).hexdigest()
    assembleia.ata_publicada_em = timezone.now()
    assembleia.save(update_fields=["ata_hash", "ata_publicada_em", "updated_at"])
    q = quorum(assembleia)
    _registrar_memoria(
        mandato=assembleia.mandato,
        autor=user,
        tipo=TipoContextoHistorico.PROCESSO,
        titulo=f"Ata — {assembleia.titulo}",
        conteudo=assembleia.ata,
        decisao=f"Ata publicada · {q['presentes']} presentes · SHA-256 {assembleia.ata_hash[:16]}…",
        entidade_tipo="assembleia",
        entidade_id=assembleia.id,
        tags=["assembleia", assembleia.tipo],
    )
    return assembleia


def build_ata_pdf(assembleia: Assembleia, associacao: str) -> bytes:
    from xml.sax.saxutils import escape

    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title=f"Ata — {assembleia.titulo}", author=associacao,
    )
    base = getSampleStyleSheet()
    cinza = HexColor("#4b5563")
    cab = ParagraphStyle("cab", parent=base["Normal"], fontSize=9, textColor=cinza)
    texto = ParagraphStyle("texto", parent=base["Normal"], fontSize=11, leading=16, alignment=4)
    pe = ParagraphStyle("pe", parent=base["Normal"], fontSize=8, leading=11, textColor=cinza)
    elementos = [Paragraph(escape(associacao), cab), Spacer(1, 14)]
    for paragrafo in assembleia.ata.split("\n"):
        elementos.append(Paragraph(escape(paragrafo) or "&nbsp;", texto))
    if assembleia.ata_publicada_em:
        publicada = timezone.localtime(assembleia.ata_publicada_em).strftime("%d/%m/%Y %H:%M")
        elementos += [
            Spacer(1, 24),
            Paragraph(f"Publicada em {publicada} · SHA-256 {assembleia.ata_hash}", pe),
        ]
    doc.build(elementos)
    return buffer.getvalue()
