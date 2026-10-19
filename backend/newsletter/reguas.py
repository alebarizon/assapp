"""
Réguas automáticas de relacionamento: boas-vindas, reengajamento de inativos e
convite ao autor aprovado que ainda não é sócio.

Rodam uma vez por dia (comando `reguas_relacionamento`, chamado pelo agendador).
Cada envio é registrado em `EnvioRegua` com uma chave única por gatilho, então
rodar de novo no mesmo dia não repete mensagens.
"""
import logging
import re
from datetime import timedelta
from urllib.parse import urlencode

from django.core.mail import get_connection
from django.db import IntegrityError, connection
from django.db.models import Max, Min
from django.utils import timezone

from core.emails import frontend_url
from eventos.models import EventoAcademico, InscricaoEvento, SubmissaoStatus, SubmissaoTrabalho
from membros.models import FiliacaoStatus, Membro

from .models import EnvioRegua, Regua, TipoRegua
from .services import _descadastrados, montar_mensagem

logger = logging.getLogger(__name__)

LIMITE_POR_EXECUCAO = 200
VIGENTES = [FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA]
SOCIOS = [FiliacaoStatus.ATIVA, FiliacaoStatus.HONORARIA, FiliacaoStatus.INADIMPLENTE]
VARIAVEIS = ("nome", "associacao", "evento", "trabalho", "proximo_evento")

PADROES = {
    TipoRegua.BOAS_VINDAS: {
        "ativa": True,
        "dias": 7,
        "assunto": "Bem-vindo(a) à {associacao}",
        "corpo": (
            "Olá, {nome}!\n\n"
            "Sua filiação à {associacao} está ativa. Pelo portal do associado você acompanha a anuidade, "
            "baixa a carteirinha digital, se inscreve em eventos e cursos e fala direto com a diretoria.\n\n"
            "{proximo_evento}\n\n"
            "Seja muito bem-vindo(a)!"
        ),
    },
    TipoRegua.INATIVOS: {
        "ativa": False,
        "dias": 6,
        "assunto": "{nome}, sentimos sua falta na {associacao}",
        "corpo": (
            "Olá, {nome}!\n\n"
            "Faz um tempo que não vemos você por aqui. A {associacao} segue com eventos, cursos e "
            "publicações para associados.\n\n"
            "{proximo_evento}\n\n"
            "Passe no portal para ver as novidades e manter seu perfil atualizado."
        ),
    },
    TipoRegua.AUTOR_NAO_SOCIO: {
        "ativa": True,
        "dias": 30,
        "assunto": "Seu trabalho foi aprovado — que tal se associar à {associacao}?",
        "corpo": (
            "Olá, {nome}!\n\n"
            "Parabéns pela aprovação de \"{trabalho}\" em {evento}.\n\n"
            "A {associacao} reúne a comunidade da área o ano inteiro, não só no congresso: associados em dia "
            "têm desconto em eventos e cursos, acesso às publicações e votam nas decisões da associação.\n\n"
            "Conheça as categorias de filiação no nosso site."
        ),
    },
}

LINKS = {
    TipoRegua.BOAS_VINDAS: "Acessar o portal",
    TipoRegua.INATIVOS: "Ver as novidades",
    TipoRegua.AUTOR_NAO_SOCIO: "Quero me associar",
}


def obter_reguas() -> dict[str, Regua]:
    reguas = {r.tipo: r for r in Regua.objects.all()}
    for tipo, padrao in PADROES.items():
        if tipo not in reguas:
            reguas[tipo], _ = Regua.objects.get_or_create(tipo=tipo, defaults=padrao)
    return reguas


def _associacao() -> str:
    nome = getattr(getattr(connection, "tenant", None), "name", "")
    if not nome:
        from tenants.models import Tenant

        nome = Tenant.objects.filter(schema_name=connection.schema_name).values_list("name", flat=True).first()
    return nome or "nossa associação"


def _proximo_evento() -> str:
    evento = (
        EventoAcademico.objects.filter(publicado_site=True, data_inicio__gte=timezone.now())
        .order_by("data_inicio")
        .first()
    )
    if not evento:
        return ""
    quando = timezone.localtime(evento.data_inicio).strftime("%d/%m/%Y")
    return f"Próximo evento: {evento.titulo}, em {quando}."


def _render(texto: str, contexto: dict) -> str:
    for chave in VARIAVEIS:
        texto = texto.replace("{" + chave + "}", str(contexto.get(chave, "")))
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def _link(tipo: str, schema: str) -> str:
    if tipo == TipoRegua.AUTOR_NAO_SOCIO:
        return frontend_url(f"/site?{urlencode({'schema': schema})}#associe-se")
    return frontend_url("/app/portal")


def _primeiro_nome(nome: str) -> str:
    return (nome or "").split(" ")[0] or "associado(a)"


def _boas_vindas(regua: Regua, hoje) -> list[dict]:
    desde = hoje - timedelta(days=max(regua.dias, 1))
    ja = set(EnvioRegua.objects.filter(tipo=regua.tipo).values_list("chave", flat=True))
    membros = (
        Membro.objects.filter(
            ativo=True,
            filiacoes__status__in=VIGENTES,
            filiacoes__data_inicio__gte=desde,
            filiacoes__data_inicio__lte=hoje,
        )
        .distinct()
        .order_by("nome_completo")
    )
    return [
        {"email": m.email, "nome": m.nome_completo, "membro_id": m.id, "chave": str(m.id), "detalhe": ""}
        for m in membros
        if str(m.id) not in ja
    ]


def ultima_atividade() -> dict:
    """membro_id → data da última ação do associado (login, inscrição, curso, formulário, submissão)."""
    ultimas: dict = {}

    def juntar(linhas):
        for membro_id, quando in linhas:
            if membro_id and quando and (membro_id not in ultimas or quando > ultimas[membro_id]):
                ultimas[membro_id] = quando

    juntar(Membro.objects.exclude(user__last_login=None).values_list("id", "user__last_login"))
    juntar(
        InscricaoEvento.objects.exclude(membro=None)
        .values("membro_id").annotate(q=Max("created_at")).values_list("membro_id", "q")
    )
    juntar(
        SubmissaoTrabalho.objects.exclude(membro=None).exclude(submetido_em=None)
        .values("membro_id").annotate(q=Max("submetido_em")).values_list("membro_id", "q")
    )
    try:
        from courses.models import CourseEnrollment

        juntar(
            CourseEnrollment.objects.values("membro_id").annotate(q=Max("enrolled_at")).values_list("membro_id", "q")
        )
    except (ImportError, LookupError):
        pass
    try:
        from formularios.models import Resposta

        juntar(
            Resposta.objects.exclude(membro=None).exclude(enviada_em=None)
            .values("membro_id").annotate(q=Max("enviada_em")).values_list("membro_id", "q")
        )
    except (ImportError, LookupError):
        pass
    return ultimas


def _inativos(regua: Regua, hoje) -> list[dict]:
    meses = max(regua.dias, 1)
    limite = timezone.now() - timedelta(days=30 * meses)
    recentes = set(
        EnvioRegua.objects.filter(tipo=regua.tipo, enviado_em__gte=limite).values_list("membro_id", flat=True)
    )
    ultimas = ultima_atividade()
    fora = _descadastrados()
    membros = (
        Membro.objects.filter(ativo=True, filiacoes__status__in=VIGENTES)
        .annotate(inicio=Min("filiacoes__data_inicio"))
        .filter(inicio__lte=limite.date())
        .order_by("nome_completo")
    )
    candidatos = []
    for m in membros:
        if m.id in recentes or m.email.lower() in fora:
            continue
        ultima = ultimas.get(m.id)
        if ultima and ultima >= limite:
            continue
        detalhe = f"Última atividade em {timezone.localtime(ultima):%d/%m/%Y}" if ultima else "Sem atividade registrada"
        candidatos.append(
            {"email": m.email, "nome": m.nome_completo, "membro_id": m.id,
             "chave": f"{m.id}:{hoje.isoformat()}", "detalhe": detalhe}
        )
    return candidatos


def _autores_nao_socios(regua: Regua, hoje) -> list[dict]:
    desde = timezone.now() - timedelta(days=max(regua.dias, 1))
    socios = {
        e.lower()
        for e in Membro.objects.filter(ativo=True, filiacoes__status__in=SOCIOS).values_list("email", flat=True)
    }
    fora = _descadastrados()
    ja = set(EnvioRegua.objects.filter(tipo=regua.tipo).values_list("chave", flat=True))
    submissoes = (
        SubmissaoTrabalho.objects.filter(
            status__in=[SubmissaoStatus.ACEITO, SubmissaoStatus.ACEITO_COM_REVISOES], decidido_em__gte=desde
        )
        .select_related("autor", "cfp__evento")
        .order_by("decidido_em")
    )
    vistos: dict[str, dict] = {}
    for sub in submissoes:
        evento = sub.cfp.evento
        pessoas = [(sub.autor.email, sub.autor.get_full_name() or sub.autor.email)]
        pessoas += [(c.get("email"), c.get("nome")) for c in (sub.coautores or []) if isinstance(c, dict)]
        for email, nome in pessoas:
            email = (email or "").strip().lower()
            chave = f"{email}:{evento.id}"
            if not email or email in socios or email in fora or chave in ja or chave in vistos:
                continue
            vistos[chave] = {
                "email": email, "nome": nome or "", "membro_id": None, "chave": chave,
                "detalhe": f"{sub.titulo[:120]} — {evento.titulo}"[:255],
                "evento": evento.titulo, "trabalho": sub.titulo,
            }
    return list(vistos.values())


CANDIDATOS = {
    TipoRegua.BOAS_VINDAS: _boas_vindas,
    TipoRegua.INATIVOS: _inativos,
    TipoRegua.AUTOR_NAO_SOCIO: _autores_nao_socios,
}


def candidatos(regua: Regua, hoje=None) -> list[dict]:
    return CANDIDATOS[regua.tipo](regua, hoje or timezone.localdate())


def montar(regua: Regua, candidato: dict, schema: str, proximo_evento: str = "", conexao=None):
    contexto = {
        "nome": _primeiro_nome(candidato.get("nome")),
        "associacao": _associacao(),
        "evento": candidato.get("evento", ""),
        "trabalho": candidato.get("trabalho", ""),
        "proximo_evento": proximo_evento,
    }
    return montar_mensagem(
        _render(regua.assunto, contexto).replace("\n", " "),
        _render(regua.corpo, contexto),
        candidato["email"],
        schema,
        link=_link(regua.tipo, schema),
        link_label=LINKS[regua.tipo],
        conexao=conexao,
        descadastro=regua.tipo != TipoRegua.BOAS_VINDAS,
    )


def previa(regua: Regua) -> dict:
    lista = candidatos(regua)
    return {
        "total": len(lista),
        "limite_por_dia": LIMITE_POR_EXECUCAO,
        "amostra": [{"nome": c["nome"], "email": c["email"], "detalhe": c["detalhe"]} for c in lista[:8]],
    }


def enviar_teste(regua: Regua, email: str, nome: str = "") -> bool:
    exemplo = {
        "email": email, "nome": nome or "Maria Silva",
        "evento": "Congresso de exemplo", "trabalho": "Título do trabalho de exemplo",
    }
    try:
        msg = montar(regua, exemplo, connection.schema_name, _proximo_evento())
        msg.subject = f"[Teste] {msg.subject}"
        msg.send()
        return True
    except Exception:
        logger.exception("Falha no teste da régua %s", regua.tipo)
        return False


def executar(hoje=None) -> dict:
    """Envia as réguas ativas da associação atual; devolve enviados/falhas por tipo."""
    schema = connection.schema_name
    resultado = {}
    proximo = _proximo_evento()
    for regua in obter_reguas().values():
        if not regua.ativa:
            continue
        lista = candidatos(regua, hoje)[:LIMITE_POR_EXECUCAO]
        enviados = falhas = 0
        if lista:
            conexao = get_connection()
            conexao.open()
            try:
                for cand in lista:
                    try:
                        montar(regua, cand, schema, proximo, conexao).send()
                    except Exception as exc:
                        logger.warning("Régua %s: falha para %s: %s", regua.tipo, cand["email"], exc)
                        falhas += 1
                        continue
                    try:
                        EnvioRegua.objects.create(
                            tipo=regua.tipo, chave=cand["chave"], email=cand["email"], nome=cand["nome"][:255],
                            membro_id=cand.get("membro_id"), detalhe=cand.get("detalhe", ""),
                        )
                    except IntegrityError:
                        pass
                    enviados += 1
            finally:
                conexao.close()
        resultado[regua.tipo] = {"enviados": enviados, "falhas": falhas}
    return resultado
