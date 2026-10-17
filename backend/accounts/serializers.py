from rest_framework import serializers

from .access import modulos_do_user, perfis_do_user
from .models import User


class UserSerializer(serializers.ModelSerializer):
    membro_id = serializers.SerializerMethodField()
    membro_nome = serializers.SerializerMethodField()
    perfis = serializers.SerializerMethodField()
    modulos = serializers.SerializerMethodField()

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
            "perfis",
            "modulos",
        )
        read_only_fields = ("id", "email", "role", "membro_id", "membro_nome", "perfis", "modulos")

    def get_perfis(self, obj):
        return perfis_do_user(obj)

    def get_modulos(self, obj):
        return modulos_do_user(obj)

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


class EquipeUsuarioSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    perfis = serializers.SerializerMethodField()
    convite_pendente = serializers.SerializerMethodField()
    cargos = serializers.SerializerMethodField()
    perfis_sugeridos = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "nome",
            "perfis",
            "is_active",
            "last_login",
            "date_joined",
            "convite_pendente",
            "cargos",
            "perfis_sugeridos",
            "is_self",
        )

    def get_nome(self, obj):
        return obj.get_full_name() or obj.email

    def get_perfis(self, obj):
        return perfis_do_user(obj)

    def get_convite_pendente(self, obj):
        from .equipe import convite_pendente

        return convite_pendente(obj)

    def get_cargos(self, obj):
        from mandatos.models import TipoCargo

        from .equipe import cargos_ativos

        rotulos = dict(TipoCargo.choices)
        return [rotulos.get(c, c) for c in cargos_ativos(obj)]

    def get_perfis_sugeridos(self, obj):
        from .equipe import perfis_sugeridos

        return perfis_sugeridos(obj)

    def get_is_self(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.pk == obj.pk)
