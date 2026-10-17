"""Serviços — fluxo integrado de eventos científicos (H3)."""
from django.utils import timezone
from django.utils.text import slugify

from mandatos.models import Mandato
from membros.models import Membro

from .models import (
    AnaisPublicacao,
    CallForPapers,
    EventoAcademico,
    EventoAcademicoStatus,
    InscricaoEvento,
    Parecer,
    RecomendacaoParecer,
    SubmissaoStatus,
    SubmissaoTrabalho,
)


def vincular_membro_por_email(submissao: SubmissaoTrabalho) -> SubmissaoTrabalho:
    """H3 — vincula submissão ao membro: FK do autor, senão e-mail (com auto-link)."""
    if submissao.membro_id:
        return submissao

    autor = submissao.autor
    if autor:
        from membros.services import resolver_membro_do_user

        membro = resolver_membro_do_user(autor, auto_link=True)
        if membro and membro.ativo:
            submissao.membro = membro
            submissao.save(update_fields=["membro"])
            return submissao

    email = getattr(autor, "email", None) if autor else None
    if email:
        membro = Membro.objects.filter(email__iexact=email, ativo=True).first()
        if membro:
            submissao.membro = membro
            submissao.save(update_fields=["membro"])
    return submissao


def submeter_trabalho(submissao: SubmissaoTrabalho) -> SubmissaoTrabalho:
    """Marca submissão como submetida e vincula membro."""
    submissao.status = SubmissaoStatus.SUBMETIDO
    submissao.submetido_em = timezone.now()
    submissao.save()
    vincular_membro_por_email(submissao)

    cfp = submissao.cfp
    if cfp.evento.status == EventoAcademicoStatus.CFP_ABERTO:
        total_submetidas = cfp.submissoes.filter(
            status__in=[
                SubmissaoStatus.SUBMETIDO,
                SubmissaoStatus.EM_PARECER,
                SubmissaoStatus.ACEITO,
                SubmissaoStatus.ACEITO_COM_REVISOES,
                SubmissaoStatus.REJEITADO,
            ]
        ).count()
        if total_submetidas >= 1:
            cfp.evento.status = EventoAcademicoStatus.EM_AVALIACAO
            cfp.evento.save(update_fields=["status", "updated_at"])

    return submissao


def atribuir_parecerista(submissao: SubmissaoTrabalho, parecerista) -> Parecer:
    """Atribui parecerista à submissão (H3)."""
    parecer, created = Parecer.objects.get_or_create(
        submissao=submissao,
        parecerista=parecerista,
    )
    if submissao.status == SubmissaoStatus.SUBMETIDO:
        submissao.status = SubmissaoStatus.EM_PARECER
        submissao.save(update_fields=["status", "updated_at"])
    return parecer


def concluir_parecer(
    parecer: Parecer,
    recomendacao: str,
    nota: int = None,
    comentarios_autor: str = None,
    comentarios_internos: str = None,
) -> Parecer:
    """Registra parecer e atualiza status da submissão."""
    parecer.recomendacao = recomendacao
    parecer.nota = nota
    parecer.comentarios_autor = comentarios_autor
    parecer.comentarios_internos = comentarios_internos
    parecer.concluido = True
    parecer.concluido_em = timezone.now()
    parecer.save()

    submissao = parecer.submissao
    mapa = {
        RecomendacaoParecer.ACEITAR: SubmissaoStatus.ACEITO,
        RecomendacaoParecer.ACEITAR_COM_REVISOES: SubmissaoStatus.ACEITO_COM_REVISOES,
        RecomendacaoParecer.REJEITAR: SubmissaoStatus.REJEITADO,
    }
    submissao.status = mapa.get(recomendacao, submissao.status)
    submissao.save(update_fields=["status", "updated_at"])
    return parecer


def gerar_anais(evento: EventoAcademico, titulo: str = None, issn: str = None) -> AnaisPublicacao:
    """
    H3 — Gera publicação de anais a partir de submissões aceitas.
    """
    cfp = getattr(evento, "call_for_papers", None)
    if not cfp:
        raise ValueError("Evento não possui Call for Papers.")

    aceitas = cfp.submissoes.filter(
        status__in=[SubmissaoStatus.ACEITO, SubmissaoStatus.ACEITO_COM_REVISOES]
    ).select_related("autor", "membro")

    trabalhos = [
        {
            "id": str(s.id),
            "titulo": s.titulo,
            "autor": s.autor.get_full_name() or s.autor.email,
            "membro_id": str(s.membro_id) if s.membro_id else None,
            "area_tematica": s.area_tematica,
            "palavras_chave": s.palavras_chave,
        }
        for s in aceitas
    ]

    anais, _ = AnaisPublicacao.objects.update_or_create(
        evento=evento,
        defaults={
            "titulo": titulo or f"Anais — {evento.titulo}",
            "issn": issn,
            "publicado_em": timezone.now(),
            "metadata": {
                "total_trabalhos": len(trabalhos),
                "trabalhos": trabalhos,
                "gerado_automaticamente": True,
            },
        },
    )

    evento.status = EventoAcademicoStatus.ANAIS_PUBLICADOS
    evento.save(update_fields=["status", "updated_at"])
    return anais


def abrir_cfp(evento: EventoAcademico, dados_cfp: dict) -> CallForPapers:
    """Cria ou atualiza CFP e abre submissões."""
    cfp, _ = CallForPapers.objects.update_or_create(
        evento=evento,
        defaults=dados_cfp,
    )
    evento.status = EventoAcademicoStatus.CFP_ABERTO
    evento.save(update_fields=["status", "updated_at"])
    return cfp


def resumo_eventos() -> dict:
    """KPIs de eventos para dashboard."""
    return {
        "total": EventoAcademico.objects.count(),
        "cfp_abertos": EventoAcademico.objects.filter(
            status=EventoAcademicoStatus.CFP_ABERTO
        ).count(),
        "em_avaliacao": EventoAcademico.objects.filter(
            status=EventoAcademicoStatus.EM_AVALIACAO
        ).count(),
        "submissoes_pendentes": SubmissaoTrabalho.objects.filter(
            status=SubmissaoStatus.SUBMETIDO
        ).count(),
        "pareceres_pendentes": Parecer.objects.filter(concluido=False).count(),
    }


def criar_evento_com_mandato(dados: dict, mandato: Mandato = None) -> EventoAcademico:
    if not mandato:
        mandato = Mandato.get_ativo()
    if not dados.get("slug"):
        dados["slug"] = slugify(dados["titulo"])
    return EventoAcademico.objects.create(mandato=mandato, **dados)


# ---------------------------------------------------------------- Certificados de participação


def _periodo(evento: EventoAcademico) -> str:
    inicio = timezone.localtime(evento.data_inicio).date()
    fim = timezone.localtime(evento.data_fim).date()
    if inicio == fim:
        return f"em {inicio.strftime('%d/%m/%Y')}"
    return f"de {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"


def gerar_codigo_certificado() -> str:
    import secrets

    from courses.models import CourseEnrollment

    while True:
        code = secrets.token_hex(5).upper()
        if (
            not InscricaoEvento.objects.filter(certificado_codigo=code).exists()
            and not CourseEnrollment.objects.filter(certificate_code=code).exists()
        ):
            return code


def emitir_certificados(evento: EventoAcademico, schema: str, associacao: str, notificar: bool = True) -> dict:
    """Gera código para inscritos presentes sem certificado e avisa por e-mail."""
    from core.certificates import certificate_verify_url
    from core.emails import enviar_email

    if not evento.certificado_habilitado:
        raise ValueError("Certificados estão desativados para este evento.")
    pendentes = evento.inscricoes.filter(presente=True, certificado_codigo__isnull=True)
    emitidos, emails = 0, 0
    agora = timezone.now()
    for inscricao in pendentes:
        inscricao.certificado_codigo = gerar_codigo_certificado()
        inscricao.certificado_emitido_em = agora
        inscricao.save(update_fields=["certificado_codigo", "certificado_emitido_em"])
        emitidos += 1
        if notificar and inscricao.email:
            ok = enviar_email(
                inscricao.email,
                f"Seu certificado — {evento.titulo}",
                (
                    f"Olá, {inscricao.nome}!\n\n"
                    f"Seu certificado de participação em {evento.titulo}, emitido por {associacao}, "
                    f"já está disponível. Use o código {inscricao.certificado_codigo} para baixar "
                    "ou verificar a autenticidade."
                ),
                link=certificate_verify_url(schema, inscricao.certificado_codigo),
                link_label="Baixar certificado",
            )
            emails += int(ok)
    sem_presenca = evento.inscricoes.filter(presente=False).count()
    return {"emitidos": emitidos, "emails_enviados": emails, "inscritos_sem_presenca": sem_presenca}


def build_inscricao_certificate(inscricao: InscricaoEvento, schema: str, associacao: str) -> bytes:
    from core.certificates import build_certificate_pdf, certificate_verify_url

    evento = inscricao.evento
    detalhes = [_periodo(evento).capitalize()]
    if evento.carga_horaria:
        detalhes.append(f"Carga horária: {evento.carga_horaria} h")
    if evento.local:
        detalhes.append(evento.local)
    return build_certificate_pdf(
        participant_name=inscricao.nome,
        title=evento.titulo,
        action="participou do evento",
        details=" · ".join(detalhes),
        issued_at=timezone.localtime(inscricao.certificado_emitido_em or timezone.now()),
        code=inscricao.certificado_codigo,
        issuer=associacao,
        verify_url=certificate_verify_url(schema, inscricao.certificado_codigo),
    )
