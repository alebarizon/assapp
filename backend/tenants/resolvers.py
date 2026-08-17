"""Resolução de tenant por query string, header ou hostname (subdomínio / domínio customizado)."""
from django_tenants.utils import get_public_schema_name, remove_www, schema_context

from .models import Domain, Tenant


def resolve_tenant_from_host(host: str) -> Tenant | None:
    """Resolve tenant pelo hostname (Domain ou padrão slug.localhost em dev)."""
    host = remove_www(host.split(":")[0]).lower()
    if not host:
        return None

    with schema_context(get_public_schema_name()):
        try:
            domain = Domain.objects.select_related("tenant").get(domain=host)
            if domain.tenant.is_active:
                return domain.tenant
        except Domain.DoesNotExist:
            pass

        if host.endswith(".localhost"):
            slug = host[: -len(".localhost")]
            if slug:
                try:
                    return Tenant.objects.get(schema_name=slug, is_active=True)
                except Tenant.DoesNotExist:
                    pass

    return None


def resolve_tenant_from_request(request) -> Tenant | None:
    """Resolve tenant a partir da requisição (schema param, header ou Host)."""
    schema = (
        request.query_params.get("schema")
        or request.query_params.get("subdomain")
        or request.headers.get("X-Tenant-Schema")
    )
    if schema:
        schema = str(schema).strip().lower()
        with schema_context(get_public_schema_name()):
            try:
                return Tenant.objects.get(schema_name=schema, is_active=True)
            except Tenant.DoesNotExist:
                return None

    return resolve_tenant_from_host(request.get_host())
