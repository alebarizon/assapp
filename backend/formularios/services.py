"""Regras do módulo Formulários: validação, gravação, consolidação e exportação."""
import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Formulario, ItemResposta, Pergunta, Resposta, Secao

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_TEXTO = 5000


def perguntas_ordenadas(formulario: Formulario) -> list[Pergunta]:
    return list(
        Pergunta.objects.filter(secao__formulario=formulario)
        .select_related("secao")
        .order_by("secao__ordem", "secao__id", "ordem", "id")
    )


def _limpar_valor(pergunta: Pergunta, valor):
    """Retorna (valor_texto, valor_lista) ou levanta ValueError com mensagem amigável."""
    if pergunta.tipo == Pergunta.MULTIPLA_ESCOLHA:
        if valor in (None, ""):
            return "", None
        if not isinstance(valor, list):
            raise ValueError("Formato inválido.")
        escolhidas = [str(v) for v in valor if str(v).strip()]
        invalidas = [v for v in escolhidas if v not in pergunta.opcoes]
        if invalidas:
            raise ValueError("Opção inválida.")
        return "", list(dict.fromkeys(escolhidas)) or None

    if isinstance(valor, (list, dict)):
        raise ValueError("Formato inválido.")
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        return "", None

    if pergunta.tipo == Pergunta.ESCOLHA_UNICA:
        if texto not in pergunta.opcoes:
            raise ValueError("Opção inválida.")
    elif pergunta.tipo == Pergunta.NUMERO:
        try:
            Decimal(texto.replace(",", "."))
        except InvalidOperation:
            raise ValueError("Informe um número.")
        texto = texto.replace(",", ".")
    elif pergunta.tipo == Pergunta.ESCALA:
        try:
            nota = int(texto)
        except ValueError:
            raise ValueError("Nota inválida.")
        if not pergunta.escala_min <= nota <= pergunta.escala_max:
            raise ValueError(f"Escolha uma nota de {pergunta.escala_min} a {pergunta.escala_max}.")
        texto = str(nota)
    elif pergunta.tipo == Pergunta.EMAIL:
        if not EMAIL_RE.match(texto):
            raise ValueError("E-mail inválido.")
    elif pergunta.tipo == Pergunta.DATA:
        try:
            date.fromisoformat(texto)
        except ValueError:
            raise ValueError("Data inválida.")
    return texto[:MAX_TEXTO], None


def validar_respostas(formulario: Formulario, answers, exigir_obrigatorias: bool) -> dict:
    """
    answers: {pergunta_id: valor}. Perguntas desconhecidas são ignoradas.
    Retorna {pergunta: (valor_texto, valor_lista)}; erros por pergunta em ValidationError.
    """
    if not isinstance(answers, dict):
        raise ValidationError({"answers": "Formato inválido."})
    erros, limpos = {}, {}
    for pergunta in perguntas_ordenadas(formulario):
        chave = str(pergunta.id)
        try:
            texto, lista = _limpar_valor(pergunta, answers.get(chave))
        except ValueError as exc:
            erros[chave] = str(exc)
            continue
        if exigir_obrigatorias and pergunta.obrigatoria and not (texto or lista):
            erros[chave] = "Resposta obrigatória."
            continue
        limpos[pergunta] = (texto, lista)
    if erros:
        raise ValidationError({"detail": "Revise as respostas destacadas.", "erros": erros})
    return limpos


def salvar_itens(resposta: Resposta, limpos: dict) -> None:
    for pergunta, (texto, lista) in limpos.items():
        if not (texto or lista):
            ItemResposta.objects.filter(resposta=resposta, pergunta=pergunta).delete()
            continue
        ItemResposta.objects.update_or_create(
            resposta=resposta,
            pergunta=pergunta,
            defaults={"valor_texto": texto, "valor_lista": lista},
        )


@transaction.atomic
def registrar(resposta: Resposta, answers, enviar: bool) -> Resposta:
    """Salva rascunho (enviar=False) ou envia definitivamente."""
    if resposta.status == Resposta.ENVIADA:
        raise ValidationError({"detail": "Esta resposta já foi enviada."})
    if not resposta.formulario.aceitando_respostas:
        raise ValidationError({"detail": "Este formulário não está recebendo respostas."})
    limpos = validar_respostas(resposta.formulario, answers, exigir_obrigatorias=enviar)
    if resposta._state.adding:
        resposta.save()
    salvar_itens(resposta, limpos)
    resposta.status = Resposta.ENVIADA if enviar else Resposta.EM_ANDAMENTO
    resposta.enviada_em = timezone.now() if enviar else None
    resposta.save(update_fields=["status", "enviada_em", "updated_at"])
    return resposta


def valores_salvos(resposta: Resposta | None) -> dict:
    if not resposta or resposta._state.adding:
        return {}
    return {
        str(item.pergunta_id): item.valor_lista if item.valor_lista is not None else item.valor_texto
        for item in resposta.itens.all()
    }


def enviar_convite(resposta: Resposta, schema: str, associacao: str) -> bool:
    from urllib.parse import urlencode

    from core.emails import enviar_email, frontend_url

    formulario = resposta.formulario
    prazo = ""
    if formulario.encerra_em:
        prazo = f"\n\nRespostas aceitas até {timezone.localtime(formulario.encerra_em).strftime('%d/%m/%Y %H:%M')}."
    texto = (
        f"Olá, {resposta.nome or 'associado(a)'}!\n\n"
        f"{associacao} convida você a responder: {formulario.titulo}."
        f"{(chr(10) * 2 + formulario.descricao) if formulario.descricao else ''}"
        f"{prazo}\n\nO link abaixo é pessoal; você pode salvar e continuar depois."
    )
    link = frontend_url(f"/site/formularios/convite/{resposta.token}?{urlencode({'schema': schema})}")
    return enviar_email(resposta.email, f"[{associacao}] {formulario.titulo}", texto, link=link, link_label="Responder")


def convidar_membros(
    formulario: Formulario,
    membros,
    schema: str = "",
    associacao: str = "",
    notificar: bool = True,
    reenviar_pendentes: bool = False,
) -> dict:
    """Cria convites. Com `notificar`, envia e-mail aos novos (e aos pendentes, se `reenviar_pendentes`)."""
    criados = existentes = emails = 0
    pode_enviar = notificar and formulario.aceitando_respostas
    for membro in membros:
        resposta, created = Resposta.objects.get_or_create(
            formulario=formulario,
            membro=membro,
            defaults={"origem": Resposta.CONVITE, "nome": membro.nome_completo, "email": membro.email or ""},
        )
        if created:
            criados += 1
        else:
            existentes += 1
        deve_enviar = created or (reenviar_pendentes and resposta.status != Resposta.ENVIADA)
        if pode_enviar and deve_enviar and resposta.email:
            emails += int(enviar_convite(resposta, schema, associacao))
    return {"criados": criados, "existentes": existentes, "emails_enviados": emails}


@transaction.atomic
def duplicar(formulario: Formulario, user) -> Formulario:
    copia = Formulario.objects.create(
        titulo=f"{formulario.titulo} (cópia)"[:200],
        descricao=formulario.descricao,
        link_publico_ativo=formulario.link_publico_ativo,
        pedir_identificacao=formulario.pedir_identificacao,
        disponivel_no_portal=formulario.disponivel_no_portal,
        evento=formulario.evento,
        mensagem_confirmacao=formulario.mensagem_confirmacao,
        created_by=user,
    )
    for secao in formulario.secoes.prefetch_related("perguntas"):
        nova = Secao.objects.create(
            formulario=copia, titulo=secao.titulo, descricao=secao.descricao, ordem=secao.ordem
        )
        Pergunta.objects.bulk_create(
            [
                Pergunta(
                    secao=nova,
                    texto=p.texto,
                    ajuda=p.ajuda,
                    tipo=p.tipo,
                    opcoes=p.opcoes,
                    escala_min=p.escala_min,
                    escala_max=p.escala_max,
                    obrigatoria=p.obrigatoria,
                    ordem=p.ordem,
                )
                for p in secao.perguntas.all()
            ]
        )
    return copia


def _numero(texto: str):
    try:
        return float(Decimal(texto))
    except (InvalidOperation, ValueError):
        return None


def resumo(formulario: Formulario) -> dict:
    """Consolidação por pergunta, considerando só respostas enviadas."""
    enviadas = formulario.respostas.filter(status=Resposta.ENVIADA)
    total = enviadas.count()
    itens_por_pergunta: dict = {}
    for item in ItemResposta.objects.filter(resposta__in=enviadas).only(
        "pergunta_id", "valor_texto", "valor_lista"
    ):
        itens_por_pergunta.setdefault(item.pergunta_id, []).append(item)

    perguntas = []
    for pergunta in perguntas_ordenadas(formulario):
        itens = itens_por_pergunta.get(pergunta.id, [])
        dados = {
            "id": str(pergunta.id),
            "texto": pergunta.texto,
            "tipo": pergunta.tipo,
            "secao": pergunta.secao.titulo,
            "respondidas": len(itens),
        }
        if pergunta.tipo in Pergunta.TIPOS_COM_OPCOES:
            contagem = {opcao: 0 for opcao in pergunta.opcoes}
            for item in itens:
                valores = item.valor_lista if item.valor_lista is not None else [item.valor_texto]
                for valor in valores:
                    contagem[valor] = contagem.get(valor, 0) + 1
            dados["opcoes"] = [{"opcao": k, "total": v} for k, v in contagem.items()]
        elif pergunta.tipo in (Pergunta.ESCALA, Pergunta.NUMERO):
            numeros = [n for n in (_numero(i.valor_texto) for i in itens) if n is not None]
            dados["media"] = round(sum(numeros) / len(numeros), 2) if numeros else None
            if pergunta.tipo == Pergunta.ESCALA:
                distribuicao = {str(n): 0 for n in range(pergunta.escala_min, pergunta.escala_max + 1)}
                for item in itens:
                    if item.valor_texto in distribuicao:
                        distribuicao[item.valor_texto] += 1
                dados["opcoes"] = [{"opcao": k, "total": v} for k, v in distribuicao.items()]
        else:
            ultimos = sorted(itens, key=lambda i: i.id)[-50:]
            dados["textos"] = [i.valor_texto for i in ultimos if i.valor_texto]
        perguntas.append(dados)
    return {"total_respostas": total, "perguntas": perguntas}


def exportar_csv(formulario: Formulario) -> str:
    perguntas = perguntas_ordenadas(formulario)
    saida = io.StringIO()
    saida.write("\ufeff")  # BOM para o Excel reconhecer UTF-8
    writer = csv.writer(saida, delimiter=";")
    writer.writerow(["Enviada em", "Nome", "E-mail", "Origem"] + [p.texto for p in perguntas])
    respostas = (
        formulario.respostas.filter(status=Resposta.ENVIADA)
        .prefetch_related("itens")
        .order_by("enviada_em")
    )
    for resposta in respostas:
        valores = {
            item.pergunta_id: ", ".join(item.valor_lista) if item.valor_lista else item.valor_texto
            for item in resposta.itens.all()
        }
        enviada = timezone.localtime(resposta.enviada_em).strftime("%d/%m/%Y %H:%M") if resposta.enviada_em else ""
        writer.writerow(
            [enviada, resposta.nome, resposta.email, resposta.get_origem_display()]
            + [valores.get(p.id, "") for p in perguntas]
        )
    return saida.getvalue()
