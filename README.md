# AssApp — Gestão Contínua de Conhecimento Institucional para Associações Científicas

> **Projeto de pesquisa:** PIPE FAPESP Jornada Tecnológica — Fase 1  
> **Empresa sede:** Alexandre Barizon ME  
> **Base tecnológica:** arquitetura WellSaaS/Wellflows (reutilização ~80% da infraestrutura multi-tenant)

---

## Visão Geral

O **AssApp** é um SaaS multi-tenant voltado a **associações científicas e organizações do terceiro setor** no Brasil. O sistema resolve a **ruptura cíclica de memória institucional** causada por mandatos de diretoria curtos (~2 anos), com preservação **ativa** de conhecimento entre gestões — não apenas armazenamento passivo.

### Problema Central (PIPE)

A cada troca de diretoria, informações críticas se perdem: filiações, histórico financeiro, regras de eventos, contratos e padrões de comunicação. O AssApp modela **mandatos**, **contexto histórico** e **fluxos acadêmicos** como entidades de primeira classe, permitindo onboarding guiado e timeline institucional auditável.

### Hipóteses de Pesquisa

| ID | Hipótese | Módulo relacionado |
|----|----------|-------------------|
| **H1** | Modelagem com histórico auditável reduz onboarding em ≥50% | `mandatos`, `memoria` |
| **H2** | Interface adaptativa aumenta adoção sustentada | `frontend` (modo Nova Diretoria) |
| **H3** | Integração membros + eventos + CFP elimina redundâncias | `membros`, `eventos` |

Documentação detalhada: [`docs/pesquisa/HIPOTESES_PIPE.md`](docs/pesquisa/HIPOTESES_PIPE.md)

---

## Stack Técnica

Alinhada ao **WellSaaS** (mesma stack de produção do Wellflows):

| Camada | Tecnologia |
|--------|------------|
| Backend | Django 4.2 + Django REST Framework |
| Multi-tenancy | `django-tenants` (schema PostgreSQL isolado por associação) |
| Autenticação | JWT (`djangorestframework-simplejwt`) |
| Banco de dados | PostgreSQL 14 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + CSS semântico WellSaaS |
| i18n | i18next (pt, en, es) |
| Containerização | Docker + Docker Compose |
| Pagamentos | Stripe (anuidades e inscrições) |
| Integrações | Google Calendar, NF de serviços (fase posterior) |

### Sobre o Schema Prisma

O arquivo [`prisma/schema.prisma`](prisma/schema.prisma) documenta o **modelo de domínio conceitual** da pesquisa PIPE — entidades `Mandato`, `ContextoHistorico` e `EventoAcademico` com relacionamentos explícitos.

> **Fonte de verdade em runtime:** Django ORM (`backend/*/models.py`). O Prisma **não** é usado em produção; existe para documentação, revisão científica e eventual geração de diagramas ER.

---

## Arquitetura Multi-Tenant

```
┌─────────────────────────────────────────────────────────────┐
│  Schema `public` (SHARED_APPS)                              │
│  tenants · domains · adminpanel · payments · accounts       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ schema: abciber│   │ schema: sbpc  │   │ schema: ...   │
│ (TENANT_APPS)  │   │               │   │               │
│ mandatos ★     │   │ mandatos      │   │               │
│ memoria ★      │   │ memoria       │   │               │
│ eventos ★      │   │ eventos       │   │               │
│ membros        │   │ membros       │   │               │
│ finance        │   │ finance       │   │               │
│ documents      │   │ documents     │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

**Papéis de usuário:**

| Role | Descrição |
|------|-----------|
| `superadmin` | Gestão da plataforma AssApp (schema `sistema`) |
| `association_admin` | Administrador da associação (tenant) |
| `board_member` | Membro da diretoria no mandato ativo |
| `member` | Associado filiado |
| `reviewer` | Parecerista em eventos científicos |

---

## Estrutura de Pastas

```
assapp/
├── README.md                    # Este arquivo
├── cursor-readme.md             # Referência rápida para Cursor AI
├── .cursorrules                 # Regras do agente
├── docker-compose.yml
├── docker-compose.dev.yml
│
├── prisma/
│   └── schema.prisma            # Modelo de domínio documentado (PIPE)
│
├── backend/
│   ├── core/                    # Settings, middleware, URLs
│   ├── tenants/                 # Tenant + Domain (multi-tenancy)
│   ├── accounts/                # User, JWT, perfis
│   ├── adminpanel/              # Superadmin, planos SaaS
│   ├── payments/                # Stripe, credenciais criptografadas
│   ├── mandatos/          ★     # Mandatos, transição, onboarding (PIPE core)
│   ├── memoria/           ★     # ContextoHistorico, timeline (PIPE core)
│   ├── eventos/           ★     # EventoAcademico, CFP, pareceres (PIPE core)
│   ├── membros/                 # Filiados, anuidades, histórico
│   ├── finance/                 # Lançamentos, relatórios, compliance BR
│   ├── documents/               # Upload e compartilhamento
│   ├── integrations/            # Google Calendar, NF
│   └── support/                 # Tickets de suporte
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Login.tsx / Signup.tsx   # Auth (split-screen WellSaaS)
│       │   ├── AssociationSetup.tsx     # Setup pós-compra (1º mandato)
│       │   ├── Mandatos.tsx             # Lista e gestão de mandatos
│       │   ├── MandatoDetail.tsx        # Cargos, timeline, snapshots
│       │   ├── OnboardingWizard.tsx     # Wizard Nova Diretoria (H2)
│       │   ├── MemoriaInstitucional.tsx
│       │   ├── Membros.tsx / MembroDetail.tsx
│       │   ├── Eventos.tsx / EventoDetail.tsx
│       │   ├── Finance.tsx
│       │   └── Documents.tsx
│       ├── components/
│       │   └── AppLayout.tsx (+ AppLayout.css)
│       ├── styles/
│       │   └── Dashboard.css            # Padrão visual WellSaaS
│       ├── services/                    # auth, mandatos, memoria, …
│       └── types/
│
├── docs/
│   ├── changelog/               # Incl. CHANGELOG_2026_07_15.md
│   ├── pesquisa/                # Hipóteses H1-H3
│   ├── guias/                   # UI_PADRAO_WELLSAAS, Docker, …
│   ├── referencia/              # Status sprints, fluxo assinatura, vínculos
│   └── modulos/                 # MANDATOS, AUTH_SIGNUP_SETUP, …
│
├── research/                    # Dados anonimizados de entrevistas (PIPE)
├── scripts/                     # init_sistema_tenant.sh, up-dev.sh
└── nginx/                       # Reverse proxy (produção)
```

★ = módulos originais da pesquisa PIPE (prioridade Fase 1)

---

## Modelo de Dados — Entidades Centrais

### Mandato (H1)

Representa um ciclo de gestão da diretoria. Ao encerrar, gera **snapshot automático** com estado consolidado (membros ativos, saldo financeiro, eventos em andamento, decisões pendentes).

```
Mandato ──┬── CargoMandato (usuário + cargo)
          ├── TransicaoMandato (handoff entre mandatos)
          ├── OnboardingEtapa (wizard guiado)
          └── MandatoSnapshot (JSON auditável)
```

### ContextoHistorico (H1)

Preservação **ativa** de memória: cada registro vincula **quem decidiu**, **o quê**, **por quê** e **em qual mandato**.

```
ContextoHistorico ──┬── NotaInstitucional
                    ├── DecisaoRegistrada
                    └── TimelineInstitucional
```

### EventoAcademico (H3)

Fluxo integrado: inscrição → submissão → parecer → anais.

```
EventoAcademico ──┬── CallForPapers
                  ├── SubmissaoTrabalho
                  ├── Parecer
                  └── AnaisPublicacao
```

Diagrama ER completo: [`docs/modulos/SCHEMA_DOMINIO.md`](docs/modulos/SCHEMA_DOMINIO.md)

---

## Módulos — Reutilização do WellSaaS

| WellSaaS | AssApp | Status MVP |
|----------|--------|------------|
| Multi-tenancy (`tenants`) | ✅ Reutilizar | Fase 1 |
| Auth JWT (`accounts`) | ✅ Adaptar roles | Fase 1 |
| Financeiro (`finance`) | ✅ Adaptar categorias OSC | Fase 1 |
| Documentos (`business`) | ✅ Renomear `documents` | Fase 1 |
| Mensagens | ✅ Reutilizar | Fase 1 |
| Agendamentos | ✅ Eventos/reuniões diretoria | Fase 2 |
| Stripe (`payments`) | ⚠️ Signup simulado; Stripe real depois | Fase 1 parcial |
| Google Calendar | ✅ Reutilizar | Fase 2 |
| **Mandatos + Onboarding H2** | ★ **Novo (PIPE)** | **Fase 1 — entregue** |
| **Memória Institucional** | ★ **Novo (PIPE)** | **Fase 1 — entregue** |
| **Eventos + CFP** | ★ **Novo (PIPE)** | **Fase 1 — entregue** |
| **Signup + Setup (1º mandato)** | ★ Adaptado WellSaaS | **2026-07-14** |
| **UI shell (Dashboard.css)** | ✅ Padrão WellSaaS | **2026-07-14** |
| Planos de refeição | ❌ Não replicar | — |
| E-commerce produtos | ❌ Não replicar | — |
| Prescrições/anamneses | ❌ Não replicar | — |

---

## API REST (prefixos)

| Prefixo | App | Descrição |
|---------|-----|-----------|
| `/api/auth/` | accounts | Login, register, plans, setup, tenant-status, me |
| `/api/mandatos/` | mandatos | CRUD mandatos, transição, onboarding H2 |
| `/api/memoria/` | memoria | Contexto histórico, timeline, notas |
| `/api/eventos/` | eventos | Eventos científicos, CFP, pareceres |
| `/api/membros/` | membros | Filiados, anuidades |
| `/api/finance/` | finance | CRUD txs OSC, dashboard, relatório e-mail |
| `/api/documents/` | documents | Upload, CRUD, download, `meus/` |
| `/api/integrations/` | integrations | Google Calendar, NF *(não implementado)* |
| `/api/admin/` | adminpanel | Superadmin *(stub)* |
| `/health/` | core | Health check |

Auth (signup/setup): [`docs/modulos/AUTH_SIGNUP_SETUP.md`](docs/modulos/AUTH_SIGNUP_SETUP.md)  
Finance: [`docs/modulos/FINANCE.md`](docs/modulos/FINANCE.md) · Documents: [`docs/modulos/DOCUMENTS.md`](docs/modulos/DOCUMENTS.md)  
Fluxo de domínio: [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md)

---

## Branches e Deploy

| Branch | Ambiente | CI |
|--------|----------|-----|
| `orb` | Desenvolvimento Mac / OrbStack | — |
| `develop` | Staging DigitalOcean `:8080` | `deploy-staging.yml` |
| `main` | **Produção** DigitalOcean `:80` | `deploy-production.yml` |

Fluxo: `orb` → `develop` → `main` (igual WellSaaS). Guias: [`docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`](docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md) · [`docs/guias/DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md)

---

## Desenvolvimento Local

### Pré-requisitos

- OrbStack (Mac Apple Silicon) ou Docker + Docker Compose
- Node.js 20+ (build frontend local, opcional)
- Python 3.11+ (desenvolvimento backend local, opcional)

### Subir ambiente (Mac / OrbStack — recomendado)

```bash
cp .env.example .env
./scripts/up-orb.sh --build    # sobe com docker-compose.orb.yml
./scripts/init_sistema_tenant.sh
```

### Subir ambiente (sem overrides ARM)

```bash
cp .env.example .env
docker build -f frontend/Dockerfile.dev -t assapp-frontend-dev:local ./frontend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
./scripts/init_sistema_tenant.sh
```

**URLs locais (padrão `.env.example`):**

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5174 |
| Signup (nova associação) | http://localhost:5174/signup |
| Backend API | http://localhost:8001 |
| Admin Django | http://sistema.localhost:8001/admin/ |

> Portas `5174` / `8001` evitam conflito com WellSaaS (`5173` / `8000`).

### Migrations (protocolo django-tenants)

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

---

## Compliance Brasil (roadmap)

| Requisito | Módulo | Fase |
|-----------|--------|------|
| LGPD — consentimento e exportação | `accounts`, `membros` | 1 |
| CNPJ/CPF com validação | `membros`, `finance` | 1 |
| Marco Legal das OSCs — relatórios | `finance` | 2 |
| NF de serviços (anuidades, inscrições) | `integrations` | 2 |

---

## Roadmap MVP — Fase 1 PIPE

### Sprint 1 (atual) — Fundação
- [x] README e estrutura de pastas
- [x] Schema Prisma + modelos Django iniciais
- [x] Docker Compose funcional
- [x] Auth JWT com novos roles

### Sprint 2 — Mandatos + Onboarding (prioridade máxima)
- [x] CRUD Mandato com cargos da diretoria
- [x] Transição automática entre mandatos
- [x] Snapshot ao encerrar/iniciar transição
- [x] Wizard de onboarding (modo Nova Diretoria — H2)
- [x] Timeline institucional por mandato (`MandatoDetail`)

### Sprint 3 — Memória Institucional
- [x] ContextoHistorico com vínculo a mandatos
- [x] Notas institucionais contextualizadas
- [x] Arquivamento automático com metadados de decisão

### Sprint 4 — Membros + Anuidades
- [x] CRUD membros com histórico de filiação
- [x] Anuidades e renovações automáticas (gerar lote, vencidas, pagamento)
- [x] Financeiro adaptado para OSCs (`finance`)

### Sprint 5 — Eventos Científicos
- [x] EventoAcademico + Call for Papers
- [x] Submissão e atribuição de pareceristas
- [x] Geração de anais

### Pós-Sprint 5 (2026-07-14) — SaaS + UI
- [x] Decisão de domínio: signup → setup (1º mandato) → operação → transição H2
- [x] Signup simulado + provisionamento de tenant (`/signup`, `POST /api/auth/register/`)
- [x] Setup wizard pós-compra (`/app/setup`, `POST /api/auth/setup/`)
- [x] UI alinhada ao WellSaaS (shell, auth, páginas `dashboard-*`)
- [x] Financeiro OSC + Documentos (`/app/finance`, `/app/documents`)
- [x] MandatoDetail + deep-links H2 + eventos no snapshot (2026-07-15)
- [x] Ponte User ↔ Membro (`Membro.user`, vincular/desvincular)
- [x] Portal mínimo do associado (`/app/portal`)
- [ ] Stripe real / AdminPlan
- [ ] Integrations (Calendar / NF)

> **Consolidado:** [`docs/changelog/CHANGELOG_2026_07_15.md`](docs/changelog/CHANGELOG_2026_07_15.md) (hoje) · [`CHANGELOG_2026_07_14.md`](docs/changelog/CHANGELOG_2026_07_14.md)  
> **Status detalhado:** [`docs/referencia/STATUS_SPRINTS_FASE1.md`](docs/referencia/STATUS_SPRINTS_FASE1.md)

---

## Pesquisa e Métricas (PIPE)

Indicadores para validação das hipóteses:

| Métrica | Hipótese | Como medir |
|---------|----------|------------|
| Tempo de onboarding (horas) | H1 | Comparar antes/depois com ABCiber |
| Taxa de conclusão do wizard | H2 | Analytics no OnboardingWizard |
| Horas/mês em tarefas redundantes | H3 | Diário de bordo dos gestores |
| Adoção sustentada (90 dias) | H2 | DAU/MAU por mandato |

Protocolo de entrevistas: [`research/`](research/)

---

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [`cursor-readme.md`](cursor-readme.md) | Referência técnica rápida (Cursor AI) |
| [`docs/changelog/CHANGELOG_2026_07_15.md`](docs/changelog/CHANGELOG_2026_07_15.md) | **Consolidado 2026-07-15** (Mandatos H2 + User↔Membro + portal) |
| [`docs/changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](docs/changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md) | Portal do associado |
| [`docs/changelog/CHANGELOG_USER_MEMBRO_2026_07.md`](docs/changelog/CHANGELOG_USER_MEMBRO_2026_07.md) | Ponte User ↔ Membro |
| [`docs/changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](docs/changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md) | MandatoDetail + H2 deep-links |
| [`docs/changelog/CHANGELOG_2026_07_14.md`](docs/changelog/CHANGELOG_2026_07_14.md) | Consolidado 2026-07-14 (signup/setup + UI + finance/docs) |
| [`docs/changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](docs/changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md) | Finance OSC + Documents |
| [`docs/pesquisa/HIPOTESES_PIPE.md`](docs/pesquisa/HIPOTESES_PIPE.md) | H1, H2, H3 detalhadas |
| [`docs/modulos/MANDATOS.md`](docs/modulos/MANDATOS.md) | Módulo core PIPE |
| [`docs/modulos/FINANCE.md`](docs/modulos/FINANCE.md) | Lançamentos OSC, dashboard |
| [`docs/modulos/DOCUMENTS.md`](docs/modulos/DOCUMENTS.md) | Upload e audiência |
| [`docs/modulos/AUTH_SIGNUP_SETUP.md`](docs/modulos/AUTH_SIGNUP_SETUP.md) | Register, setup, tenant-status |
| [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Domínio: assinatura → setup → operação → H2 |
| [`docs/guias/UI_PADRAO_WELLSAAS.md`](docs/guias/UI_PADRAO_WELLSAAS.md) | Padrão visual de páginas |
| [`docs/referencia/STATUS_SPRINTS_FASE1.md`](docs/referencia/STATUS_SPRINTS_FASE1.md) | Status Sprints 1–5 e pós-Sprint 5 |
| [`docs/referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](docs/referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Vínculos, tenancy, gaps User↔Membro |
| [`prisma/schema.prisma`](prisma/schema.prisma) | Schema conceitual |
| [`pre_proposta_pipe_abciber.md`](pre_proposta_pipe_abciber.md) | Pré-proposta FAPESP |

---

## Licença e Pesquisa

Projeto desenvolvido no âmbito da **PIPE FAPESP Jornada Tecnológica — Fase 1**.  
Código proprietário — Alexandre Barizon ME.  
Resultados de pesquisa serão publicados conforme exigências FAPESP.

---

**Última atualização:** 2026-07-15
