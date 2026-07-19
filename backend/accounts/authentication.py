"""JWT multi-tenant — busca usuário no schema correto."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from django_tenants.utils import get_tenant_model, schema_context

from .models import User


class TenantAwareJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            return None
        return self.get_user(validated_token), validated_token

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            raise InvalidToken("Token sem user_id")

        Tenant = get_tenant_model()
        user = None

        with schema_context("public"):
            tenants = list(Tenant.objects.filter(is_active=True))

        for tenant in tenants:
            try:
                with schema_context(tenant.schema_name):
                    found = User.objects.filter(id=user_id).first()
                    if found:
                        user = found
                        user._tenant_schema = tenant.schema_name
                        user._tenant = tenant
                        break
            except Exception:
                continue

        if not user:
            raise AuthenticationFailed("Usuário não encontrado")
        if not user.is_active:
            raise AuthenticationFailed("Usuário inativo")
        return user
