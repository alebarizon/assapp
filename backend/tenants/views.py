"""API pública — resolução de tenant por domínio."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .resolvers import resolve_tenant_from_host, resolve_tenant_from_request


class PublicTenantResolveView(APIView):
    """GET /api/tenants/public/resolve/?host=demo.localhost — schema do tenant."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        host = request.query_params.get("host") or request.get_host()
        tenant = resolve_tenant_from_host(host) or resolve_tenant_from_request(request)
        if not tenant:
            return Response({"detail": "Tenant não encontrado para este host."}, status=404)
        return Response(
            {
                "schema": tenant.schema_name,
                "slug": tenant.slug,
                "name": tenant.name,
            }
        )
