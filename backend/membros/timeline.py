"""Linha do tempo do associado: o que aconteceu com ele em todos os módulos."""
from datetime import date, datetime, time

from django.utils import timezone

from .models import AnuidadeStatus, LembreteAnuidade, Membro


def _quando(valor) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor if timezone.is_aware(valor) else timezone.make_aware(valor)
    if isinstance(valor, date):
        return timezone.make_aware(datetime.combine(valor, time.min))
    return None


def _brl(valor) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


def timeline_membro(membro: Membro, limite: int = 200) -> list[dict]:
    itens: list[dict] = []

    def add(quando, categoria: str, titulo: str, detalhe: str = "", link: str = ""):
        momento = _quando(quando)
        if momento:
            itens.append(
                {
                    "quando": momento,
                    "categoria": categoria,
                    "titulo": titulo,
                    "detalhe": detalhe,
                    "link": link,
                }
            )

    for filiacao in membro.filiacoes.all():
        add(filiacao.data_inicio, "filiacao", f"Filiação {filiacao.get_tipo_display().lower()} iniciada")
        if filiacao.data_fim:
            add(filiacao.data_fim, "filiacao", "Filiação encerrada", filiacao.get_status_display())

        for anuidade in filiacao.anuidades.all():
            if anuidade.pago_em:
                add(
                    anuidade.pago_em,
                    "anuidade",
                    f"Anuidade {anuidade.ano_referencia} paga",
                    _brl(anuidade.valor),
                )
            elif anuidade.status == AnuidadeStatus.VENCIDA:
                add(
                    anuidade.vencimento,
                    "anuidade",
                    f"Anuidade {anuidade.ano_referencia} vencida",
                    _brl(anuidade.valor),
                )

    for lembrete in LembreteAnuidade.objects.filter(anuidade__filiacao__membro=membro).select_related(
        "anuidade"
    ):
        add(
            lembrete.created_at,
            "lembrete",
            f"Lembrete da anuidade {lembrete.anuidade.ano_referencia} enviado",
            lembrete.get_etapa_display(),
        )

    for envio in membro.envios_regua.all():
        add(envio.enviado_em, "lembrete", f"E-mail automático: {envio.get_tipo_display().lower()}", envio.detalhe)

    try:
        from payments.models import Cobranca

        for cobranca in Cobranca.objects.filter(membro=membro):
            add(
                cobranca.created_at,
                "pagamento",
                f"Cobrança {cobranca.get_metodo_display()} gerada",
                f"{cobranca.descricao} · {_brl(cobranca.valor)} · {cobranca.get_status_display()}",
            )
    except (ImportError, LookupError):
        pass

    for pedido in membro.orders.all():
        add(
            pedido.created_at,
            "pedido",
            f"Pedido {pedido.order_number}",
            f"{_brl(pedido.total_amount)} · {pedido.get_status_display()}",
        )

    for inscricao in membro.inscricoes_evento.select_related("evento"):
        add(inscricao.created_at, "evento", f"Inscrição em {inscricao.evento.titulo}")
        if inscricao.certificado_emitido_em:
            add(
                inscricao.certificado_emitido_em,
                "evento",
                f"Certificado emitido — {inscricao.evento.titulo}",
            )

    for submissao in membro.submissoes.exclude(submetido_em__isnull=True):
        add(submissao.submetido_em, "evento", "Trabalho submetido", submissao.titulo)

    for matricula in membro.course_enrollments.select_related("course"):
        add(matricula.enrolled_at, "curso", f"Matrícula em {matricula.course.title}")
        if matricula.completed_at:
            add(matricula.completed_at, "curso", f"Curso concluído — {matricula.course.title}")

    for conversa in membro.conversas.all():
        add(
            conversa.created_at,
            "mensagem",
            "Conversa iniciada" + (" pela diretoria" if conversa.iniciada_pela_diretoria else " pelo associado"),
            conversa.assunto,
            f"/app/mensagens/{conversa.id}",
        )

    for resposta in membro.respostas_formularios.exclude(enviada_em__isnull=True).select_related(
        "formulario"
    ):
        add(resposta.enviada_em, "formulario", "Formulário respondido", resposta.formulario.titulo)

    for contato in membro.contatos.all():
        add(
            contato.created_at,
            "contato",
            "Contato pelo site",
            contato.get_assunto_display(),
            f"/app/contatos/{contato.id}",
        )

    itens.sort(key=lambda item: item["quando"], reverse=True)
    return itens[:limite]
