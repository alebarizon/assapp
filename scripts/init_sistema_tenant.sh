#!/bin/bash
# Cria tenant "sistema" (superadmin) e tenant demo "abciber"
set -e

CONTAINER="${ASSAPP_BACKEND_CONTAINER:-assapp_backend}"

echo "🏢 Inicializando tenants AssApp..."

docker exec "$CONTAINER" python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from datetime import date
from django.core.management import call_command
from django_tenants.utils import schema_context
from tenants.models import Tenant, Domain
from accounts.models import User
from mandatos.models import Mandato, MandatoStatus, CargoMandato, TipoCargo

def ensure_tenant(schema_name, name, slug, domain_name, setup_completed=True):
    with schema_context('public'):
        tenant, created = Tenant.objects.get_or_create(
            schema_name=schema_name,
            defaults={
                'name': name,
                'slug': slug,
                'is_active': True,
                'on_trial': False,
                'setup_completed': setup_completed,
                'payment_simulated': True,
                'plan_slug': 'profissional' if schema_name == 'abciber' else None,
            },
        )
        if not created:
            tenant.setup_completed = setup_completed
            if schema_name == 'abciber' and not tenant.plan_slug:
                tenant.plan_slug = 'profissional'
            tenant.save(update_fields=['setup_completed', 'plan_slug', 'updated_at'])
        Domain.objects.get_or_create(
            domain=domain_name,
            defaults={'tenant': tenant, 'is_primary': True},
        )
    call_command('migrate_schemas', schema_name=schema_name, verbosity=0)
    print(f\"{'✅ Criado' if created else 'ℹ️  Existe'}: tenant {schema_name} (setup_completed={setup_completed})\")
    return tenant

# 1. Tenant sistema (superadmin)
ensure_tenant('sistema', 'Sistema AssApp', 'sistema', 'sistema.localhost', setup_completed=True)

with schema_context('sistema'):
    admin, created = User.objects.get_or_create(
        email='admin@assapp.local',
        defaults={
            'username': 'admin',
            'role': User.SUPERADMIN,
            'is_superuser': True,
            'is_staff': True,
            'is_active': True,
            'perfil_tecnico': User.PERFIL_AVANCADO,
        },
    )
    admin.set_password('admin123')
    admin.save()
    print(f\"👤 Superadmin: {admin.email} / admin123\")

# 2. Tenant demo ABCiber (piloto PIPE) — setup já feito (tem 1º mandato)
tenant_abc = ensure_tenant('abciber', 'ABCiber', 'abciber', 'abciber.localhost', setup_completed=True)

with schema_context('abciber'):
    diretor, _ = User.objects.get_or_create(
        email='diretoria@abciber.org.br',
        defaults={
            'username': 'diretoria',
            'role': User.ASSOCIATION_ADMIN,
            'first_name': 'Diretoria',
            'last_name': 'ABCiber',
            'is_active': True,
            'perfil_tecnico': User.PERFIL_INICIANTE,
            'consentimento_lgpd': True,
        },
    )
    diretor.set_password('abciber123')
    diretor.save()

    mandato, _ = Mandato.objects.get_or_create(
        numero_sequencial=1,
        defaults={
            'titulo': 'Diretoria 2024-2026',
            'data_inicio': date(2024, 1, 1),
            'data_fim': date(2026, 12, 31),
            'status': MandatoStatus.ATIVO,
            'descricao': 'Mandato piloto PIPE — ABCiber',
        },
    )

    CargoMandato.objects.get_or_create(
        mandato=mandato,
        usuario=diretor,
        cargo=TipoCargo.PRESIDENTE,
        defaults={'data_inicio': date(2024, 1, 1), 'ativo': True},
    )

    # H1 — registros demo de memória institucional
    from memoria.models import ContextoHistorico
    demos = [
        {
            'tipo': 'decisao',
            'titulo': 'Anuidade 2024 mantida em R$ 80',
            'conteudo': 'Assembleia de associados em março/2024.',
            'decisao': 'Manter valor da anuidade em R$ 80,00 para associados efetivos.',
            'motivo': 'Inflação controlada e reserva financeira adequada do mandato anterior.',
            'tags': ['financeiro', 'anuidade'],
        },
        {
            'tipo': 'processo',
            'titulo': 'Submissão de trabalhos via Google Forms',
            'conteudo': 'Processo usado no Encontro 2023 — a ser substituído pelo AssApp.',
            'decisao': 'Continuar Forms até migração para plataforma integrada.',
            'motivo': 'Falta de alternativa integrada no início do mandato.',
            'tags': ['eventos', 'cfp'],
        },
        {
            'tipo': 'comunicacao',
            'titulo': 'Lista de e-mail no Mailchimp',
            'conteudo': 'Conta compartilhada entre presidentes — credenciais no drive da diretoria.',
            'decisao': 'Migrar lista para o AssApp até dez/2024.',
            'motivo': 'Risco de perda de acesso entre mandatos.',
            'tags': ['comunicacao', 'mailchimp'],
        },
    ]
    for d in demos:
        ContextoHistorico.objects.get_or_create(
            mandato=mandato,
            titulo=d['titulo'],
            defaults={**d, 'autor': diretor, 'visivel_diretoria': True},
        )
    print(f\"📚 Memória institucional: {len(demos)} registros demo\")

    # Sprint 4 — membros demo
    from membros.models import Membro, Filiacao, FiliacaoStatus, Anuidade, AnuidadeStatus
    from decimal import Decimal
    membros_demo = [
        {'nome_completo': 'Ana Silva', 'email': 'ana.silva@usp.br', 'instituicao': 'ECA/USP', 'area_atuacao': 'Cibercultura', 'tipo': 'efetivo'},
        {'nome_completo': 'Bruno Costa', 'email': 'bruno.costa@unifesp.br', 'instituicao': 'UNIFESP', 'area_atuacao': 'Comunicação Digital', 'tipo': 'efetivo'},
        {'nome_completo': 'Carla Mendes', 'email': 'carla.m@pucsp.edu.br', 'instituicao': 'PUC-SP', 'area_atuacao': 'Estudos de Internet', 'tipo': 'estudante'},
        {'nome_completo': 'Prof. Dr. João Nery', 'email': 'joao.nery@unicamp.br', 'instituicao': 'UNICAMP', 'area_atuacao': 'Pesquisa em Mídia', 'tipo': 'honorario'},
    ]
    ano_atual = date.today().year
    for md in membros_demo:
        membro, created = Membro.objects.get_or_create(
            email=md['email'],
            defaults={
                'nome_completo': md['nome_completo'],
                'instituicao': md['instituicao'],
                'area_atuacao': md['area_atuacao'],
                'consentimento_lgpd': True,
                'ativo': True,
            },
        )
        filiacao, _ = Filiacao.objects.get_or_create(
            membro=membro,
            data_inicio=date(2024, 1, 1),
            defaults={'mandato': mandato, 'tipo': md['tipo'], 'status': FiliacaoStatus.ATIVA},
        )
        # Um inadimplente para demo
        if md['email'] == 'bruno.costa@unifesp.br':
            filiacao.status = FiliacaoStatus.INADIMPLENTE
            filiacao.save(update_fields=['status'])
            Anuidade.objects.get_or_create(
                filiacao=filiacao, ano_referencia=ano_atual - 1,
                defaults={'valor': Decimal('80.00'), 'vencimento': date(ano_atual - 1, 3, 31), 'status': AnuidadeStatus.VENCIDA},
            )
        Anuidade.objects.get_or_create(
            filiacao=filiacao, ano_referencia=ano_atual,
            defaults={
                'valor': Decimal('40.00') if md['tipo'] == 'estudante' else (Decimal('0') if md['tipo'] == 'honorario' else Decimal('80.00')),
                'vencimento': date(ano_atual, 3, 31),
                'status': AnuidadeStatus.ISENTA if md['tipo'] == 'honorario' else AnuidadeStatus.PENDENTE,
            },
        )
    print(f\"👥 Membros demo: {len(membros_demo)} associados\")

    # Associado demo — portal (role member)
    ana_membro = Membro.objects.filter(email='ana.silva@usp.br').first()
    associado, _ = User.objects.get_or_create(
        email='ana.silva@usp.br',
        defaults={
            'username': 'ana.silva',
            'role': User.MEMBER,
            'first_name': 'Ana',
            'last_name': 'Silva',
            'is_active': True,
            'perfil_tecnico': User.PERFIL_INICIANTE,
            'consentimento_lgpd': True,
        },
    )
    associado.role = User.MEMBER
    associado.set_password('associado123')
    associado.save()
    if ana_membro and ana_membro.user_id != associado.id:
        try:
            from membros.services import vincular_user as vincular_user_svc
            # e-mails já coincidem
            ana_membro.user = None
            ana_membro.save(update_fields=['user', 'updated_at'])
            vincular_user_svc(ana_membro, associado)
            print(f\"🔗 Portal associado: {associado.email} / associado123\")
        except Exception as e:
            print(f\"⚠️  Portal associado: {e}\")

    # Ponte User ↔ Membro — diretoria no quadro associativo
    from membros.services import vincular_user
    membro_dir, _ = Membro.objects.get_or_create(
        email=diretor.email,
        defaults={
            'nome_completo': f\"{diretor.first_name} {diretor.last_name}\".strip() or 'Diretoria ABCiber',
            'instituicao': 'ABCiber',
            'area_atuacao': 'Gestão',
            'consentimento_lgpd': True,
            'ativo': True,
        },
    )
    Filiacao.objects.get_or_create(
        membro=membro_dir,
        data_inicio=date(2024, 1, 1),
        defaults={'mandato': mandato, 'tipo': 'efetivo', 'status': FiliacaoStatus.ATIVA},
    )
    if membro_dir.user_id != diretor.id:
        try:
            vincular_user(membro_dir, diretor)
            print(f\"🔗 User↔Membro: {diretor.email}\")
        except Exception as e:
            print(f\"⚠️  User↔Membro: {e}\")

    # Sprint 5 — evento científico demo (H3)
    from eventos.models import EventoAcademico, EventoAcademicoStatus, CallForPapers, SubmissaoTrabalho, SubmissaoStatus
    from eventos.services import submeter_trabalho, atribuir_parecerista, concluir_parecer
    from eventos.models import RecomendacaoParecer
    from django.utils import timezone as tz
    from datetime import datetime, timedelta

    evento, _ = EventoAcademico.objects.get_or_create(
        slug='encontro-abciber-2026',
        defaults={
            'mandato': mandato,
            'titulo': 'VII Encontro ABCiber 2026',
            'descricao': 'Encontro anual de pesquisadores em cibercultura.',
            'data_inicio': tz.make_aware(datetime(2026, 9, 15, 9, 0)),
            'data_fim': tz.make_aware(datetime(2026, 9, 17, 18, 0)),
            'local': 'ECA/USP — São Paulo',
            'modalidade': 'hibrido',
            'status': EventoAcademicoStatus.CFP_ABERTO,
        },
    )
    cfp, _ = CallForPapers.objects.get_or_create(
        evento=evento,
        defaults={
            'titulo': 'CFP — VII Encontro ABCiber 2026',
            'instrucoes': 'Submissões em português ou inglês. Resumo até 500 palavras.',
            'data_abertura': tz.now(),
            'data_fechamento': tz.now() + timedelta(days=60),
            'areas_tematicas': ['Cibercultura', 'Mídia Digital', 'Redes Sociais'],
        },
    )
    ana = Membro.objects.filter(email='ana.silva@usp.br').first()
    if ana:
        sub, created = SubmissaoTrabalho.objects.get_or_create(
            cfp=cfp,
            titulo='Práticas de memória digital em associações científicas',
            defaults={
                'autor': diretor,
                'membro': ana,
                'resumo': 'Este trabalho analisa estratégias de preservação de memória institucional em organizações acadêmicas com liderança rotativa.',
                'area_tematica': 'Cibercultura',
                'palavras_chave': ['memória institucional', 'associações', 'gestão'],
                'status': SubmissaoStatus.SUBMETIDO,
                'submetido_em': tz.now(),
            },
        )
        if created:
            parecer = atribuir_parecerista(sub, diretor)
            concluir_parecer(parecer, RecomendacaoParecer.ACEITAR, nota=5,
                comentarios_autor='Trabalho relevante para o tema do encontro.')
    print(f\"📅 Evento demo: {evento.titulo}\")

    # Finance OSC + Documents demo
    from django.utils import timezone as tz_now
    from django.core.files.base import ContentFile
    from finance.models import Transaction, TransactionType, IncomeCategory, ExpenseCategory
    from documents.models import Document, DocumentAudience

    Transaction.objects.get_or_create(
        referencia='demo:doacao-seed',
        defaults={
            'user': diretor,
            'mandato': mandato,
            'description': 'Doação pontual — demo PIPE',
            'amount': Decimal('500.00'),
            'type': TransactionType.INCOME,
            'category': IncomeCategory.DOACAO,
            'occurred_at': tz_now.now(),
        },
    )
    Transaction.objects.get_or_create(
        referencia='demo:admin-seed',
        defaults={
            'user': diretor,
            'mandato': mandato,
            'description': 'Despesa administrativa — site hospedagem',
            'amount': Decimal('89.90'),
            'type': TransactionType.EXPENSE,
            'category': ExpenseCategory.ADMINISTRATIVA,
            'occurred_at': tz_now.now(),
        },
    )
    print('💰 Financeiro demo: 2 lançamentos')

    if not Document.objects.filter(title='Estatuto social (demo)').exists():
        doc = Document(
            title='Estatuto social (demo)',
            description='Documento geral de exemplo para a ABCiber.',
            audience=DocumentAudience.GERAL,
            uploaded_by=diretor,
            file_type='txt',
        )
        doc.file.save(
            'estatuto-demo.txt',
            ContentFile(b'Estatuto social ABCiber — arquivo demo AssApp PIPE.'),
            save=True,
        )
        print(f\"📄 Documento demo: {doc.title}\")

    ana_m = Membro.objects.filter(email='ana.silva@usp.br').first()
    if ana_m and not Document.objects.filter(title='Comprovante de filiação (Ana)').exists():
        doc_ana = Document(
            title='Comprovante de filiação (Ana)',
            description='Documento pessoal demo para o portal do associado.',
            audience=DocumentAudience.MEMBRO,
            membro=ana_m,
            uploaded_by=diretor,
            file_type='txt',
        )
        doc_ana.file.save(
            'comprovante-ana.txt',
            ContentFile(b'Comprovante de filiação — Ana Silva — demo AssApp.'),
            save=True,
        )
        print(f\"📄 Documento pessoal: {doc_ana.title}\")

    print(f\"🏛️  ABCiber: {diretor.email} / abciber123\")
    print(f\"📋 Mandato ativo: {mandato.titulo}\")

with schema_context('public'):
    tenant_abc.owner_id = diretor.id
    tenant_abc.save(update_fields=['owner_id'])

print('✅ Inicialização concluída!')
"
