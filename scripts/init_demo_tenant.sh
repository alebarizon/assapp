#!/bin/bash
# Cria tenant "demo" com association_admin: demo@demo.com / demo
# Acesso a todos os módulos da diretoria (setup já concluído + dados seed).
set -e

CONTAINER="${ASSAPP_BACKEND_CONTAINER:-assapp_backend}"

echo "🏢 Inicializando tenant demo (Gesttora)..."

docker exec "$CONTAINER" python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.utils import timezone as tz
from django_tenants.utils import schema_context

from accounts.models import User
from tenants.models import Tenant, Domain
from mandatos.models import Mandato, MandatoStatus, CargoMandato, TipoCargo

SCHEMA = 'demo'
DOMAIN = 'demo.localhost'
EMAIL = 'demo@demo.com'
PASSWORD = 'demo'

with schema_context('public'):
    tenant, created = Tenant.objects.get_or_create(
        schema_name=SCHEMA,
        defaults={
            'name': 'Associação Demo',
            'slug': SCHEMA,
            'is_active': True,
            'on_trial': False,
            'setup_completed': True,
            'payment_simulated': True,
            'plan_slug': 'profissional',
        },
    )
    if not created:
        tenant.setup_completed = True
        tenant.is_active = True
        tenant.payment_simulated = True
        if not tenant.plan_slug:
            tenant.plan_slug = 'profissional'
        tenant.save(update_fields=['setup_completed', 'is_active', 'payment_simulated', 'plan_slug', 'updated_at'])
    Domain.objects.get_or_create(
        domain=DOMAIN,
        defaults={'tenant': tenant, 'is_primary': True},
    )

call_command('migrate_schemas', schema_name=SCHEMA, verbosity=0)
print(f\"{'✅ Criado' if created else 'ℹ️  Existe'}: tenant {SCHEMA}\")

with schema_context(SCHEMA):
    admin, _ = User.objects.get_or_create(
        email=EMAIL,
        defaults={
            'username': 'demo',
            'role': User.ASSOCIATION_ADMIN,
            'first_name': 'Admin',
            'last_name': 'Demo',
            'is_active': True,
            'is_staff': True,
            'perfil_tecnico': User.PERFIL_AVANCADO,
            'consentimento_lgpd': True,
            'terms_accepted': True,
        },
    )
    admin.role = User.ASSOCIATION_ADMIN
    admin.is_active = True
    admin.is_staff = True
    admin.perfil_tecnico = User.PERFIL_AVANCADO
    admin.set_password(PASSWORD)
    admin.save()

    mandato, _ = Mandato.objects.get_or_create(
        numero_sequencial=1,
        defaults={
            'titulo': 'Diretoria Demo 2025-2027',
            'data_inicio': date(2025, 1, 1),
            'data_fim': date(2027, 12, 31),
            'status': MandatoStatus.ATIVO,
            'descricao': 'Mandato seed do tenant demo.',
        },
    )
    CargoMandato.objects.get_or_create(
        mandato=mandato,
        usuario=admin,
        cargo=TipoCargo.PRESIDENTE,
        defaults={'data_inicio': date(2025, 1, 1), 'ativo': True},
    )

    from memoria.models import ContextoHistorico
    ContextoHistorico.objects.get_or_create(
        mandato=mandato,
        titulo='Assembleia de posse — diretrizes do mandato',
        defaults={
            'tipo': 'decisao',
            'conteudo': 'Registro inicial da gestão demo.',
            'decisao': 'Adotar a Gesttora como plataforma oficial.',
            'motivo': 'Centralizar memória, membros e eventos.',
            'tags': ['setup', 'plataforma'],
            'autor': admin,
            'visivel_diretoria': True,
        },
    )

    from membros.models import Membro, Filiacao, FiliacaoStatus, Anuidade, AnuidadeStatus
    from membros.services import vincular_user

    membro_admin, _ = Membro.objects.get_or_create(
        email=EMAIL,
        defaults={
            'nome_completo': 'Admin Demo',
            'instituicao': 'Associação Demo',
            'area_atuacao': 'Gestão',
            'consentimento_lgpd': True,
            'ativo': True,
        },
    )
    Filiacao.objects.get_or_create(
        membro=membro_admin,
        data_inicio=date(2025, 1, 1),
        defaults={'mandato': mandato, 'tipo': 'efetivo', 'status': FiliacaoStatus.ATIVA},
    )
    if membro_admin.user_id != admin.id:
        try:
            if membro_admin.user_id:
                membro_admin.user = None
                membro_admin.save(update_fields=['user', 'updated_at'])
            vincular_user(membro_admin, admin)
        except Exception as e:
            print(f'⚠️  User↔Membro: {e}')

    membro_ex, _ = Membro.objects.get_or_create(
        email='associado@demo.com',
        defaults={
            'nome_completo': 'Associado Exemplo',
            'instituicao': 'Universidade Demo',
            'area_atuacao': 'Pesquisa',
            'consentimento_lgpd': True,
            'ativo': True,
        },
    )
    fil_ex, _ = Filiacao.objects.get_or_create(
        membro=membro_ex,
        data_inicio=date(2025, 1, 1),
        defaults={'mandato': mandato, 'tipo': 'efetivo', 'status': FiliacaoStatus.ATIVA},
    )
    Anuidade.objects.get_or_create(
        filiacao=fil_ex,
        ano_referencia=date.today().year,
        defaults={
            'valor': Decimal('80.00'),
            'vencimento': date(date.today().year, 3, 31),
            'status': AnuidadeStatus.PENDENTE,
        },
    )

    from eventos.models import EventoAcademico, EventoAcademicoStatus, CallForPapers
    evento, _ = EventoAcademico.objects.get_or_create(
        slug='encontro-demo-2026',
        defaults={
            'mandato': mandato,
            'titulo': 'I Encontro Demo 2026',
            'descricao': 'Evento seed do tenant demo.',
            'data_inicio': tz.make_aware(datetime(2026, 8, 10, 9, 0)),
            'data_fim': tz.make_aware(datetime(2026, 8, 12, 18, 0)),
            'local': 'Online',
            'modalidade': 'online',
            'status': EventoAcademicoStatus.CFP_ABERTO,
        },
    )
    CallForPapers.objects.get_or_create(
        evento=evento,
        defaults={
            'titulo': 'CFP — I Encontro Demo 2026',
            'instrucoes': 'Submissões em português. Resumo até 500 palavras.',
            'data_abertura': tz.now(),
            'data_fechamento': tz.now() + timedelta(days=90),
            'areas_tematicas': ['Gestão', 'Memória institucional'],
        },
    )

    from finance.models import Transaction, TransactionType, IncomeCategory, ExpenseCategory
    Transaction.objects.get_or_create(
        referencia='demo:doacao',
        defaults={
            'user': admin,
            'mandato': mandato,
            'description': 'Doação — seed demo',
            'amount': Decimal('1000.00'),
            'type': TransactionType.INCOME,
            'category': IncomeCategory.DOACAO,
            'occurred_at': tz.now(),
        },
    )
    Transaction.objects.get_or_create(
        referencia='demo:admin',
        defaults={
            'user': admin,
            'mandato': mandato,
            'description': 'Despesa administrativa — seed demo',
            'amount': Decimal('120.00'),
            'type': TransactionType.EXPENSE,
            'category': ExpenseCategory.ADMINISTRATIVA,
            'occurred_at': tz.now(),
        },
    )

    from documents.models import Document, DocumentAudience
    if not Document.objects.filter(title='Estatuto (demo)').exists():
        doc = Document(
            title='Estatuto (demo)',
            description='Documento geral seed do tenant demo.',
            audience=DocumentAudience.GERAL,
            uploaded_by=admin,
            file_type='txt',
        )
        doc.file.save(
            'estatuto-demo.txt',
            ContentFile(b'Estatuto social - Associacao Demo (seed Gesttora).'),
            save=True,
        )

    print(f'👤 Admin: {EMAIL} / {PASSWORD} (association_admin)')
    print(f'📋 Mandato: {mandato.titulo}')
    print(f'📅 Evento: {evento.titulo}')

    from website.services import seed_default_config, seed_default_pages
    seed_default_config(site_title='Associação Demo', publish=True)
    seed_default_pages()
    print('🌐 Website demo publicado — /site?schema=demo ou http://demo.localhost:5174/site')

    from decimal import Decimal
    from ecommerce.models import CatalogItem, CatalogItemType
    anuidades = [
        ('Anuidade — graduação', 'anuidade-graduacao', Decimal('80.00'), 'graduacao'),
        ('Anuidade — pós-graduação', 'anuidade-pos', Decimal('120.00'), 'pos_graduacao'),
        ('Anuidade — profissional', 'anuidade-profissional', Decimal('200.00'), 'profissional'),
    ]
    for name, slug, price, tipo in anuidades:
        CatalogItem.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': f'Filiação anual ({tipo.replace("_", " ")})',
                'item_type': CatalogItemType.ANUIDADE,
                'price': price,
                'is_active': True,
                'anuidade_ano': date.today().year,
                'tipo_filiacao': tipo,
            },
        )
    print('🛒 Catálogo demo — anuidades para box Associe-se')

with schema_context('public'):
    tenant.owner_id = admin.id
    tenant.save(update_fields=['owner_id'])

print('✅ Tenant demo pronto — login em /login com demo@demo.com / demo')
"
