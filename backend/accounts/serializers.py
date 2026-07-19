from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    membro_id = serializers.SerializerMethodField()
    membro_nome = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "perfil_tecnico",
            "phone_number",
            "locale",
            "is_active",
            "membro_id",
            "membro_nome",
        )
        read_only_fields = ("id", "email", "role", "membro_id", "membro_nome")

    def get_membro_id(self, obj):
        try:
            from membros.services import resolver_membro_do_user

            membro = resolver_membro_do_user(obj, auto_link=True)
            return str(membro.id) if membro else None
        except Exception:
            return None

    def get_membro_nome(self, obj):
        try:
            from membros.services import resolver_membro_do_user

            membro = resolver_membro_do_user(obj, auto_link=True)
            return membro.nome_completo if membro else None
        except Exception:
            return None
