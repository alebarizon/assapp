"""
Perfis de acesso da equipe da associação e módulos liberados para cada um.

Um usuário da equipe pode acumular perfis; o acesso a um módulo é o maior
nível concedido por qualquer um deles.
"""
from rest_framework.permissions import SAFE_METHODS

GESTOR = "gestor"
DIRETORIA = "diretoria"
ADMINISTRATIVO = "administrativo"
FINANCEIRO = "financeiro"

PERFIL_CHOICES = [
    (GESTOR, "Gestor"),
    (DIRETORIA, "Diretoria"),
    (ADMINISTRATIVO, "Administrativo"),
    (FINANCEIRO, "Financeiro"),
]
PERFIS_VALIDOS = frozenset(p for p, _ in PERFIL_CHOICES)

TOTAL = "total"
LEITURA = "leitura"

MODULOS = [
    ("usuarios", "Usuários e perfis"),
    ("configuracoes", "Configurações da associação"),
    ("memoria", "Memória institucional"),
    ("mandatos", "Mandatos"),
    ("governanca", "Assembleias e votações"),
    ("onboarding", "Onboarding"),
    ("membros", "Associados"),
    ("eventos", "Eventos"),
    ("cursos", "Cursos"),
    ("formularios", "Formulários"),
    ("contatos", "Contatos"),
    ("mensagens", "Mensagens"),
    ("newsletter", "Newsletter"),
    ("website", "Website"),
    ("documentos", "Documentos"),
    ("publicacoes", "Publicações"),
    ("financeiro", "Financeiro"),
    ("loja", "Loja"),
    ("suporte", "Suporte"),
    ("integracoes", "Integrações"),
]
MODULOS_VALIDOS = frozenset(m for m, _ in MODULOS)

_OPERACIONAIS = (
    "membros", "eventos", "cursos", "formularios", "contatos", "mensagens", "newsletter", "website", "documentos",
    "publicacoes",
)

MATRIZ = {
    GESTOR: {m: TOTAL for m in MODULOS_VALIDOS},
    DIRETORIA: {
        **{m: TOTAL for m in MODULOS_VALIDOS - {"usuarios", "configuracoes", "financeiro", "loja", "integracoes"}},
        "financeiro": LEITURA,
        "loja": LEITURA,
    },
    ADMINISTRATIVO: {
        "memoria": LEITURA,
        "mandatos": LEITURA,
        "governanca": LEITURA,
        "onboarding": LEITURA,
        **{m: TOTAL for m in _OPERACIONAIS},
        "suporte": TOTAL,
    },
    FINANCEIRO: {
        "membros": LEITURA,
        "documentos": TOTAL,
        "financeiro": TOTAL,
        "loja": TOTAL,
        "suporte": TOTAL,
    },
}

SUGESTAO_POR_CARGO = {
    "presidente": GESTOR,
    "vice_presidente": DIRETORIA,
    "secretario": ADMINISTRATIVO,
    "secretario_adjunto": ADMINISTRATIVO,
    "tesoureiro": FINANCEIRO,
    "tesoureiro_adjunto": FINANCEIRO,
    "diretor": DIRETORIA,
    "conselho_fiscal": FINANCEIRO,
    "outro": DIRETORIA,
}


def _role(user):
    return getattr(user, "role", None)


def is_superadmin(user):
    return _role(user) == "superadmin"


def is_equipe(user):
    return _role(user) in ("association_admin", "board_member")


def perfis_do_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return []
    if is_superadmin(user):
        return [GESTOR]
    if not is_equipe(user):
        return []
    perfis = [p for p in (getattr(user, "perfis", None) or []) if p in PERFIS_VALIDOS]
    if perfis:
        return perfis
    # Contas anteriores aos perfis: dono vira gestor, diretoria segue diretoria.
    return [GESTOR] if _role(user) == "association_admin" else [DIRETORIA]


def nivel_acesso(user, modulo):
    niveis = {MATRIZ[p].get(modulo) for p in perfis_do_user(user)}
    if TOTAL in niveis:
        return TOTAL
    if LEITURA in niveis:
        return LEITURA
    return None


def modulos_do_user(user):
    return {m: n for m in MODULOS_VALIDOS if (n := nivel_acesso(user, m))}


def pode_acessar(user, modulo, method="GET"):
    nivel = nivel_acesso(user, modulo)
    if nivel == TOTAL:
        return True
    return nivel == LEITURA and method in SAFE_METHODS


def is_gestor(user):
    return nivel_acesso(user, "usuarios") == TOTAL


def sugerir_perfis(cargos):
    sugestoes = []
    for cargo in cargos:
        perfil = SUGESTAO_POR_CARGO.get(cargo)
        if perfil and perfil not in sugestoes:
            sugestoes.append(perfil)
    return sugestoes
