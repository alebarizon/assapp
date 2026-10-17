"""Fixtures globais: tenant de teste (schema próprio) e usuários por papel."""
import pytest
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from tenants.models import Domain, Tenant

User = get_user_model()


@pytest.fixture
def test_tenant(db):
    tenant = Tenant.objects.create(name="Associação Teste", slug="teste", schema_name="teste")
    Domain.objects.create(domain="teste.localhost", tenant=tenant, is_primary=True)
    return tenant


@pytest.fixture
def board_user(test_tenant):
    with schema_context(test_tenant.schema_name):
        return User.objects.create_user(
            username="diretoria",
            email="diretoria@teste.org",
            password="pass12345",
            role=User.ASSOCIATION_ADMIN,
            first_name="Diretoria",
            tenant=test_tenant,
        )


@pytest.fixture
def member(test_tenant):
    """(user, membro) — associado com login vinculado ao cadastro."""
    from membros.models import Membro

    with schema_context(test_tenant.schema_name):
        user = User.objects.create_user(
            username="ana",
            email="ana@teste.org",
            password="pass12345",
            role=User.MEMBER,
            first_name="Ana",
            tenant=test_tenant,
        )
        membro = Membro.objects.create(user=user, nome_completo="Ana Maria Silva", email="ana@teste.org")
    return user, membro
