"""Fluxo científico da chamada de trabalhos: submissão pelo autor, parecer por critérios, decisão e certificados."""
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    CallForPapers,
    CertificadoPapel,
    EventoAcademico,
    Parecer,
    RecomendacaoParecer,
    SubmissaoStatus,
    SubmissaoTrabalho,
)

CRITERIOS_PADRAO = [
    {"nome": "Relevância e originalidade", "peso": 2},
    {"nome": "Rigor metodológico", "peso": 2},
    {"nome": "Clareza e qualidade do texto", "peso": 1},
    {"nome": "Adequação à área temática", "peso": 1},
]

STATUS_CONTA_LIMITE = [
    SubmissaoStatus.SUBMETIDO,
    SubmissaoStatus.EM_PARECER,
    SubmissaoStatus.ACEITO,
    SubmissaoStatus.ACEITO_COM_REVISOES,
    SubmissaoStatus.REJEITADO,
]

DECISOES = {
    RecomendacaoParecer.ACEITAR: SubmissaoStatus.ACEITO,
    RecomendacaoParecer.ACEITAR_COM_REVISOES: SubmissaoStatus.ACEITO_COM_REVISOES,
    RecomendacaoParecer.REJEITAR: SubmissaoStatus.REJEITADO,
}


class FluxoError(ValueError):
    """Regra de negócio violada — mensagem apresentável ao usuário."""


def criterios_da_chamada(cfp: CallForPapers) -> list[dict]:
    return cfp.criterios or CRITERIOS_PADRAO


def chamada_aberta(cfp: CallForPapers, agora=None) -> bool:
    agora = agora or timezone.now()
    return cfp.data_abertura <= agora <= cfp.data_fechamento


def normalizar_coautores(coautores) -> list[dict]:
    if not isinstance(coautores, list):
        raise FluxoError("Coautores em formato inválido.")
    limpos = []
    for c in coautores:
        if not isinstance(c, dict):
            raise FluxoError("Coautores em formato inválido.")
        nome = " ".join(str(c.get("nome") or "").split())
        if not nome:
            continue
        limpos.append(
            {
                "nome": nome,
                "email": str(c.get("email") or "").strip().lower(),
                "instituicao": " ".join(str(c.get("instituicao") or "").split()),
            }
        )
    if len(limpos) > 20:
        raise FluxoError("Máximo de 20 coautores.")
    return limpos


def nome_autor(submissao: SubmissaoTrabalho) -> str:
    if submissao.membro_id:
        return submissao.membro.nome_completo
    autor = submissao.autor
    return autor.get_full_name() or autor.email


def autoria_completa(submissao: SubmissaoTrabalho) -> str:
    return ", ".join([nome_autor(submissao)] + [c["nome"] for c in submissao.coautores or []])


# ------------------------------------------------------------------ Autor


def submeter_pelo_autor(submissao: SubmissaoTrabalho) -> SubmissaoTrabalho:
    from .services import submeter_trabalho

    cfp = submissao.cfp
    if submissao.status != SubmissaoStatus.RASCUNHO:
        raise FluxoError("Só rascunhos podem ser submetidos.")
    if not chamada_aberta(cfp):
        raise FluxoError("A chamada de trabalhos não está recebendo submissões.")
    if not submissao.titulo.strip() or not submissao.resumo.strip():
        raise FluxoError("Informe título e resumo.")
    if cfp.areas_tematicas and submissao.area_tematica not in cfp.areas_tematicas:
        raise FluxoError("Escolha uma das áreas temáticas da chamada.")
    if cfp.exige_arquivo and not submissao.arquivo:
        raise FluxoError("Esta chamada exige o arquivo do trabalho.")
    enviadas = (
        cfp.submissoes.filter(autor=submissao.autor, status__in=STATUS_CONTA_LIMITE).exclude(pk=submissao.pk).count()
    )
    if enviadas >= cfp.max_submissoes_por_autor:
        raise FluxoError(f"Limite de {cfp.max_submissoes_por_autor} trabalho(s) por autor atingido.")
    return submeter_trabalho(submissao)


# ------------------------------------------------------------------ Pareceristas


def candidatos_parecer():
    """Equipe, pareceristas cadastrados e associados com login."""
    User = get_user_model()
    from django.db.models import Q

    return (
        User.objects.filter(is_active=True)
        .filter(
            Q(role__in=[User.ASSOCIATION_ADMIN, User.BOARD_MEMBER, User.REVIEWER])
            | Q(membro_perfil__isnull=False, membro_perfil__ativo=True)
        )
        .distinct()
        .order_by("first_name", "last_name", "email")
    )


def conflito_interesse(submissao: SubmissaoTrabalho, usuario) -> str | None:
    if usuario.pk == submissao.autor_id:
        return "O parecerista é o autor do trabalho."
    email = (usuario.email or "").lower()
    if email and any(c.get("email") == email for c in submissao.coautores or []):
        return "O parecerista é coautor do trabalho."
    return None


def atribuir_parecerista(submissao: SubmissaoTrabalho, parecerista, prazo=None, notificar=False, associacao="") -> Parecer:
    motivo = conflito_interesse(submissao, parecerista)
    if motivo:
        raise FluxoError(motivo)
    if submissao.status in (SubmissaoStatus.RASCUNHO, SubmissaoStatus.RETIRADO):
        raise FluxoError("O trabalho ainda não foi submetido.")
    if submissao.decidido_em:
        raise FluxoError("O trabalho já tem decisão.")

    parecer, created = Parecer.objects.get_or_create(submissao=submissao, parecerista=parecerista)
    if prazo and parecer.prazo != prazo:
        parecer.prazo = prazo
        parecer.save(update_fields=["prazo"])
    if submissao.status == SubmissaoStatus.SUBMETIDO:
        submissao.status = SubmissaoStatus.EM_PARECER
        submissao.save(update_fields=["status", "updated_at"])

    if created and notificar and parecerista.email:
        from core.emails import enviar_email, frontend_url

        evento = submissao.cfp.evento
        prazo_txt = f" até {prazo.strftime('%d/%m/%Y')}" if prazo else ""
        enviar_email(
            parecerista.email,
            f"Convite para parecer — {evento.titulo}",
            (
                f"Olá, {parecerista.first_name or parecerista.email}!\n\n"
                f"{associacao or 'A comissão científica'} convida você a avaliar um trabalho submetido a "
                f"{evento.titulo}{prazo_txt}. O trabalho e os critérios de avaliação estão na sua área de pareceres."
            ),
            link=frontend_url("/app/pareceres"),
            link_label="Abrir meus pareceres",
        )
    return parecer


# ------------------------------------------------------------------ Parecer


def calcular_nota(criterios: list[dict], notas: dict) -> Decimal:
    soma_pesos = Decimal("0")
    soma = Decimal("0")
    for criterio in criterios:
        peso = Decimal(str(criterio.get("peso") or 1))
        soma += peso * Decimal(str(notas[criterio["nome"]]))
        soma_pesos += peso
    return (soma / soma_pesos).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validar_notas(criterios: list[dict], notas) -> dict:
    if not isinstance(notas, dict):
        raise FluxoError("Envie as notas por critério.")
    limpas = {}
    for criterio in criterios:
        nome = criterio["nome"]
        valor = notas.get(nome)
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise FluxoError(f"Dê uma nota de 1 a 5 para “{nome}”.")
        if not 1 <= valor <= 5:
            raise FluxoError(f"Dê uma nota de 1 a 5 para “{nome}”.")
        limpas[nome] = valor
    return limpas


def concluir_parecer(
    parecer: Parecer,
    recomendacao: str,
    notas: dict | None = None,
    nota: int | None = None,
    comentarios_autor: str = "",
    comentarios_internos: str = "",
) -> Parecer:
    """Registra o parecer. A decisão sobre o trabalho é da comissão (`decidir_submissao`)."""
    if parecer.submissao.decidido_em:
        raise FluxoError("O trabalho já tem decisão; o parecer não pode mais ser alterado.")
    if recomendacao not in DECISOES:
        raise FluxoError("Recomendação inválida.")
    criterios = criterios_da_chamada(parecer.submissao.cfp)
    if notas is not None:
        parecer.notas = validar_notas(criterios, notas)
        parecer.nota_ponderada = calcular_nota(criterios, parecer.notas)
        parecer.nota = int(parecer.nota_ponderada.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    elif nota is not None:
        parecer.nota = nota
        parecer.nota_ponderada = Decimal(nota)
    parecer.recomendacao = recomendacao
    parecer.comentarios_autor = comentarios_autor or ""
    parecer.comentarios_internos = comentarios_internos or ""
    parecer.concluido = True
    parecer.concluido_em = timezone.now()
    parecer.save()
    return parecer


def nota_media(submissao: SubmissaoTrabalho) -> Decimal | None:
    notas = [p.nota_ponderada for p in submissao.pareceres.all() if p.concluido and p.nota_ponderada is not None]
    if not notas:
        return None
    return (sum(notas) / len(notas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ------------------------------------------------------------------ Decisão


def _carta(submissao: SubmissaoTrabalho, associacao: str) -> tuple[str, str]:
    evento = submissao.cfp.evento
    status = submissao.status
    if status == SubmissaoStatus.ACEITO:
        assunto = f"Trabalho aceito — {evento.titulo}"
        abertura = f"Temos o prazer de comunicar que o trabalho “{submissao.titulo}” foi ACEITO para {evento.titulo}."
    elif status == SubmissaoStatus.ACEITO_COM_REVISOES:
        assunto = f"Trabalho aceito com revisões — {evento.titulo}"
        abertura = (
            f"O trabalho “{submissao.titulo}” foi ACEITO COM REVISÕES para {evento.titulo}. "
            "Considere os comentários abaixo na versão final."
        )
    else:
        assunto = f"Resultado da avaliação — {evento.titulo}"
        abertura = (
            f"Agradecemos a submissão do trabalho “{submissao.titulo}” a {evento.titulo}. "
            "Após avaliação, ele não foi selecionado nesta edição."
        )

    partes = [f"Olá, {nome_autor(submissao)}!", abertura]
    if submissao.decisao_comentario:
        partes.append(f"Comentário da comissão científica:\n{submissao.decisao_comentario}")
    comentarios = [p.comentarios_autor for p in submissao.pareceres.all() if p.concluido and p.comentarios_autor]
    for i, texto in enumerate(comentarios, start=1):
        partes.append(f"Parecer {i}:\n{texto}")
    partes.append(f"Atenciosamente,\nComissão científica — {associacao}")
    return assunto, "\n\n".join(partes)


@transaction.atomic
def decidir_submissao(
    submissao: SubmissaoTrabalho, decisao: str, comentario: str = "", notificar: bool = True, associacao: str = ""
) -> SubmissaoTrabalho:
    if decisao not in DECISOES:
        raise FluxoError("Decisão inválida.")
    if submissao.status in (SubmissaoStatus.RASCUNHO, SubmissaoStatus.RETIRADO):
        raise FluxoError("O trabalho não foi submetido.")
    submissao.status = DECISOES[decisao]
    submissao.decisao_comentario = comentario or ""
    submissao.decidido_em = timezone.now()
    submissao.save(update_fields=["status", "decisao_comentario", "decidido_em", "updated_at"])

    if notificar:
        from core.emails import enviar_email, frontend_url

        assunto, texto = _carta(submissao, associacao or "a associação")
        destinatarios = [submissao.autor.email] + [c["email"] for c in submissao.coautores or [] if c.get("email")]
        enviar_email(
            list(dict.fromkeys(d for d in destinatarios if d)),
            assunto,
            texto,
            link=frontend_url("/app/portal/trabalhos"),
            link_label="Ver meus trabalhos",
        )
    return submissao


# ------------------------------------------------------------------ Certificados de autor e parecerista


def emitir_certificados_cientificos(evento: EventoAcademico, schema: str, associacao: str, notificar: bool = True) -> dict:
    from core.certificates import certificate_verify_url
    from core.emails import enviar_email

    from .services import gerar_codigo_certificado

    cfp = getattr(evento, "call_for_papers", None)
    if not cfp:
        raise FluxoError("O evento não tem chamada de trabalhos.")

    novos: list[CertificadoPapel] = []
    aceitas = cfp.submissoes.filter(
        status__in=[SubmissaoStatus.ACEITO, SubmissaoStatus.ACEITO_COM_REVISOES]
    ).select_related("autor", "membro")
    for sub in aceitas:
        if CertificadoPapel.objects.filter(evento=evento, papel=CertificadoPapel.AUTOR, submissao=sub).exists():
            continue
        coautores = [c["nome"] for c in sub.coautores or []]
        detalhe = f"Trabalho “{sub.titulo}”"
        if coautores:
            detalhe += f" · Coautoria: {', '.join(coautores)}"
        novos.append(
            CertificadoPapel.objects.create(
                evento=evento,
                papel=CertificadoPapel.AUTOR,
                usuario=sub.autor,
                submissao=sub,
                nome=nome_autor(sub),
                email=sub.autor.email,
                detalhe=detalhe[:500],
                codigo=gerar_codigo_certificado(),
            )
        )

    pareceristas = {}
    for parecer in Parecer.objects.filter(submissao__cfp=cfp, concluido=True).select_related("parecerista"):
        pareceristas.setdefault(parecer.parecerista, 0)
        pareceristas[parecer.parecerista] += 1
    for usuario, total in pareceristas.items():
        if CertificadoPapel.objects.filter(
            evento=evento, papel=CertificadoPapel.PARECERISTA, usuario=usuario
        ).exists():
            continue
        novos.append(
            CertificadoPapel.objects.create(
                evento=evento,
                papel=CertificadoPapel.PARECERISTA,
                usuario=usuario,
                nome=usuario.get_full_name() or usuario.email,
                email=usuario.email,
                detalhe=f"{total} parecer(es) emitido(s)",
                codigo=gerar_codigo_certificado(),
            )
        )

    emails = 0
    if notificar:
        for cert in novos:
            if not cert.email:
                continue
            emails += int(
                enviar_email(
                    cert.email,
                    f"Seu certificado de {cert.get_papel_display().lower()} — {evento.titulo}",
                    (
                        f"Olá, {cert.nome}!\n\nSeu certificado de {cert.get_papel_display().lower()} em "
                        f"{evento.titulo}, emitido por {associacao}, está disponível. Código: {cert.codigo}."
                    ),
                    link=certificate_verify_url(schema, cert.codigo),
                    link_label="Baixar certificado",
                )
            )
    return {
        "autores": sum(1 for c in novos if c.papel == CertificadoPapel.AUTOR),
        "pareceristas": sum(1 for c in novos if c.papel == CertificadoPapel.PARECERISTA),
        "emails_enviados": emails,
    }


ACAO_CERTIFICADO = {
    CertificadoPapel.AUTOR: "apresentou trabalho no evento",
    CertificadoPapel.PARECERISTA: "atuou como parecerista do evento",
}


def build_certificado_papel_pdf(cert: CertificadoPapel, schema: str, associacao: str) -> bytes:
    from core.certificates import build_certificate_pdf, certificate_verify_url

    from .services import _periodo

    detalhes = [cert.detalhe, _periodo(cert.evento).capitalize()] if cert.detalhe else [_periodo(cert.evento).capitalize()]
    return build_certificate_pdf(
        participant_name=cert.nome,
        title=cert.evento.titulo,
        action=ACAO_CERTIFICADO[cert.papel],
        details=" · ".join(detalhes),
        issued_at=timezone.localtime(cert.emitido_em),
        code=cert.codigo,
        issuer=associacao,
        verify_url=certificate_verify_url(schema, cert.codigo),
    )
