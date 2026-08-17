"""Permissões do módulo e-commerce Gesttora."""
from rest_framework.permissions import BasePermission

from accounts.models import User
from mandatos.permissions import IsBoardOrAdmin


class IsMember(BasePermission):
    """Associado autenticado (role member)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == User.MEMBER


class IsBoardOrMember(BasePermission):
    """Diretoria/admin ou associado."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == User.MEMBER:
            return True
        return IsBoardOrAdmin().has_permission(request, view)
