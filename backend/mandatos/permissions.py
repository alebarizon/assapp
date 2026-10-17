"""Permissões do painel da associação."""
from rest_framework.permissions import BasePermission

from accounts.access import DIRETORIA, GESTOR, perfis_do_user, pode_acessar


class IsBoardOrAdmin(BasePermission):
    """
    Equipe da associação com acesso ao módulo da view (`view.modulo`, str ou tupla
    em que qualquer módulo basta).

    Views sem `modulo` exigem o perfil de gestor ou diretoria.
    """

    message = "Seu perfil não tem acesso a este módulo."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        modulo = getattr(view, "modulo", None)
        if not modulo:
            return bool({GESTOR, DIRETORIA} & set(perfis_do_user(user)))
        modulos = (modulo,) if isinstance(modulo, str) else modulo
        return any(pode_acessar(user, m, request.method) for m in modulos)
