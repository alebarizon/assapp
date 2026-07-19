"""Permissões do módulo Mandatos."""
from rest_framework.permissions import BasePermission

from accounts.models import User


class IsBoardOrAdmin(BasePermission):
    """Acesso para diretoria e administradores da associação."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (
            User.SUPERADMIN,
            User.ASSOCIATION_ADMIN,
            User.BOARD_MEMBER,
        )
