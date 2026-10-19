# AssApp — Referência Técnica para o Cursor

> Consulte este arquivo primeiro. Links para docs detalhados em `docs/`.  
> **Última revisão:** 2026-10-18 (assembleias, newsletter, diretório, agendador da régua · deploy pull-antes-de-parar)

---

## Infra / Deploy (DigitalOcean)

| Ambiente | URL | Branch |
|----------|-----|--------|
| Staging | http://159.203.183.184:8080/ | `develop` |
| Produção | http://gesttora.vertent.com.br/ · http://159.203.183.184/ | `main` |
| Dev Mac | http://localhost:5174 | `orb` |

Droplet: `159.203.183.184` · HTTPS: **adiado**  
Containers por ambiente: `db`, `backend`, `agendador` (fila da newsletter a cada minuto + régua de anuidades e réguas de relacionamento diárias às `REGUA_HORA`), `frontend`, `nginx` — sufixo `_staging` / `_prod`.  
E-mail em staging/prod ainda é console (nada é entregue; a régua roda só marcando vencidas) — falta provedor por API (DigitalOcean bloqueia SMTP).  
Changelog recente: [`CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md`](docs/changelog/CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md) · infra: [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md) (seção 11) · deploy: [`PROMPT_DEPLOY.md`](PROMPT_DEPLOY.md)

**Login remoto (ABCiber):** `diretoria@abciber.org.br` / `abciber123` — requer `init_sistema_tenant.sh` no droplet.

---

## Branches Git

| Branch | Ambiente | CI |
|--------|----------|-----|
| `orb` | Dev Mac / OrbStack | nenhum |
| `develop` | Staging DO `:8080` | `deploy-staging.yml` |
| `main` | **Produção** DO `:80` | `deploy-production.yml` |

```
orb → develop (staging) → main (produção)
```

Mac: `./scripts/up-orb.sh` · Docs: [`ESTRATEGIA_BRANCHES_ORBSTACK.md`](docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md) · [`DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md)

---

## Stack

Django 4.2 + DRF + JWT + django-tenants + PostgreSQL 14 + React 18 + TS + Vite

**Não usar Prisma em runtime** — `prisma/schema.prisma` é documentação de domínio.

**UI:** CSS semântico padrão WellSaaS (`Dashboard.css`, `AppLayout.css`, `Login.css`) — ver [`docs/guias/UI_PADRAO_WELLSAAS.md`](docs/guias/UI_PADRAO_WELLSAAS.md).

---

## Rotas públicas (frontend)

| Rota | Página |
|------|--------|
| `/` | Landing SaaS **Gesttora** (`gesttora.vertent.com.br`) — conteúdo estático |
| `/site`, `/site/p/:slug` | **Website do tenant** (público, `?schema=`) · CMS em `/app/website` |
| `/login` | Login |
| `/signup` | Cadastro da associação (simulado) |
| `/app/*` | App autenticado (tenant) |

**Demo tenant:** schema `demo` · `demo@demo.com` / `demo` (`association_admin`, todos os módulos)  
Seed: `./scripts/init_demo_tenant.sh`

CMS / website da associação (tenant): **implementado** — ver [`docs/modulos/WEBSITE_CMS_TENANT.md`](docs/modulos/WEBSITE_CMS_TENANT.md). Site demo: `/site?schema=demo`. Adminpanel editar landing Gesttora: **adiado**.

Changelog: [`docs/changelog/CHANGELOG_LANDING_GESTTORA_2026_07.md`](docs/changelog/CHANGELOG_LANDING_GESTTORA_2026_07.md)

---

## Schemas PostgreSQL

| Schema | Conteúdo |
|--------|----------|
| `public` | tenants (com `setup_completed`, `plan_slug`), domains, **support** (chamados de todas as associações) |
| `sistema` | superadmin |
| `{associacao}` | mandatos ★, memoria ★, eventos ★, membros, finance, documents, ecommerce, courses, formularios, contatos, mensagens, payments, publicacoes, governanca, newsletter, website, accounts |

> `adminpanel` — stub; assinatura do SaaS (Stripe) continua simulada. `payments` é TENANT: pagamento de anuidades via Asaas da própria associação.

---

## Apps TENANT (por associação)

| App | Descrição |
|-----|-----------|
| `mandatos` | Mandatos, transição, onboarding da nova diretoria |
| `memoria` | ContextoHistorico, timeline |
| `eventos` | Chamada de trabalhos (submissão pelo portal, parecer duplo-cego por critérios, decisão, certificados de autor/parecerista), anais com página citável por trabalho (`/site/eventos/:slug/anais`), programação e hotsite (`/site/eventos`) |
| `membros` | Filiados, anuidades, régua de cobrança (`regua_anuidades`, diária pelo serviço `agendador`), linha do tempo do associado, carteirinha digital com QR (`/site/carteirinha/:codigo`), diretório público opt-in (`/site/associados`) |
| `payments` | Pagamento online de anuidades (Asaas: Pix, cartão, boleto) + webhook (`/app/finance` → Pagamento online) |
| `finance` | Lançamentos OSC, dashboard, e-mail fechamento |
| `ecommerce` | Catálogo, carrinho, pedidos (anuidade, evento, curso, material) |
| `courses` | Cursos online: aulas, quiz, Q&A, certificado; venda via loja (`/app/courses`, `/app/portal/cursos`, `/site/cursos`) |
| `formularios` | Pesquisas, avaliação de eventos, consultas: link público, portal e convite por e-mail (`/app/formularios`, `/site/formularios/:token`) |
| `contatos` | CRM leve: formulário de contato do site, funil, etiquetas, conversão em associado, ficha 360 por e-mail (`/app/contatos`) |
| `mensagens` | Conversas diretoria ↔ associado (`/app/mensagens`, `/app/portal/mensagens`) |
| `documents` | Upload / audiência / meus |
| `accounts` | User, JWT, register, setup |
| `website` | Site público tenant + CMS (`/site`, `/app/website`) |
| `publicacoes` | Dossiês, e-books, boletins: acesso aberto, para adimplentes ou venda pela loja (`/app/publicacoes`, `/app/portal/publicacoes`, `/site/publicacoes`) |
| `governanca` | Assembleias (convocação, presença, quórum, ata com hash) e votações com cédula digital (`/app/governanca`, `/app/portal/governanca`) |
| `newsletter` | Campanhas segmentadas (associados, inscritos, etiquetas) com fila limitada por minuto e descadastro (`/app/newsletter`, `/site/descadastrar`); réguas automáticas de boas-vindas, inativos e autor não sócio (`reguas_relacionamento`, diária pelo `agendador`) |

App compartilhado (schema `public`): `support` — chamados associação → equipe Gesttora (`/app/suporte`).
Certificados (cursos e eventos) usam `core/certificates.py` + verificação pública em `/site/certificados`.

---

## Roles de Usuário

```
superadmin | association_admin | board_member | member | reviewer
```

Equipe (`association_admin`/`board_member`) tem **perfis de acesso** acumuláveis em `User.perfis`:
`gestor` (máximo) · `diretoria` · `administrativo` · `financeiro`. Cada view do painel declara
`modulo = "..."` e `IsBoardOrAdmin` checa a matriz em `accounts/access.py`.
Gestão em `/app/usuarios` — ver [`USUARIOS_PERFIS.md`](docs/modulos/USUARIOS_PERFIS.md).

---

## API Prefixos

```
/api/auth/       accounts  (login, register, plans, setup, tenant-status, me, equipe/, senha/esqueci|definir)
/api/mandatos/   mandatos
/api/memoria/    memoria
/api/eventos/    eventos
/api/membros/    membros
/api/finance/    finance (OSC)
/api/pagamentos/ pagamento online (configuracao/, anuidades/{id}/cobrar/, cobrancas/{id}/, webhook/asaas/)
/api/ecommerce/  catalog, cart, orders (+ public/catalog)
/api/courses/    cursos (diretoria, my/ associado, public/ site + certificados)
/api/formularios/ formulários (diretoria, my/ associado, public/f|r/ sem login)
/api/contatos/   contatos/CRM (diretoria, etiquetas/, public/ formulário do site)
/api/mensagens/  conversas (diretoria, my/ associado)
/api/suporte/    chamados de suporte (diretoria da associação + superadmin)
/api/certificados/{codigo}/[pdf/]  verificação pública de certificados (cursos, eventos, autoria e parecer)
/api/documents/  documents (+ meus/)
/api/publicacoes/ publicações (diretoria, minhas/ portal, public/ site)
/api/governanca/ assembleias/, votacoes/ (diretoria), minhas/ (portal: votar, presença, ata)
/api/newsletter/ campanhas/, reguas/, descadastros/ (diretoria), public/descadastrar/ (link do e-mail)
/api/website/    website CMS tenant (config, pages, public)
/api/tenants/    resolve domínio → schema (public/resolve)
```

Auth detalhado: [`docs/modulos/AUTH_SIGNUP_SETUP.md`](docs/modulos/AUTH_SIGNUP_SETUP.md)  
Finance: [`docs/modulos/FINANCE.md`](docs/modulos/FINANCE.md) · Pagamentos: [`docs/modulos/PAGAMENTOS.md`](docs/modulos/PAGAMENTOS.md) · Documents: [`docs/modulos/DOCUMENTS.md`](docs/modulos/DOCUMENTS.md)

---

## Ciclo de vida (domínio)

```
Signup (simulado) → Setup (1º mandato) → Operação → Transição de mandato
```

Ver: [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md)

> Hipóteses H1/H2/H3 (PIPE) **não** orientam mais o desenvolvimento — não citar em código, comentários ou docs novos.

---

## Documentação / ação futura

| Documento | Conteúdo |
|-----------|----------|
| [`docs/changelog/CHANGELOG_2026_07_24_27.md`](docs/changelog/CHANGELOG_2026_07_24_27.md) | **Consolidado 24–27 jul** (landing, deploy, domínio) |
| [`docs/changelog/CHANGELOG_LANDING_GESTTORA_2026_07.md`](docs/changelog/CHANGELOG_LANDING_GESTTORA_2026_07.md) | Landing SaaS Gesttora (`/`) |
| [`docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md) | Infra · **HTTPS adiado** (`gesttora.vertent.com.br`) |
| [`docs/guias/DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md) | Deploy DO + seção **Domínio + HTTPS (adiado)** |
| [`docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`](docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md) | Branches + OrbStack ARM |
| [`docs/guias/GIT_WORKFLOW.md`](docs/guias/GIT_WORKFLOW.md) | Fluxo Git / push sequencial |
| [`docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md`](docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md) | Promoção orb → develop → main |
| [`docs/guias/QUICK_REFERENCE_DOCKER.md`](docs/guias/QUICK_REFERENCE_DOCKER.md) | Comandos Docker rápidos |
| [`docs/changelog/CHANGELOG_2026_07_15.md`](docs/changelog/CHANGELOG_2026_07_15.md) | **Consolidado do dia** (Mandatos H2 + User↔Membro + portal) |
| [`docs/changelog/CHANGELOG_2026_07_14.md`](docs/changelog/CHANGELOG_2026_07_14.md) | Consolidado 2026-07-14 (signup + UI + finance) |
| [`docs/changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](docs/changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md) | Portal do associado |
| [`docs/changelog/CHANGELOG_USER_MEMBRO_2026_07.md`](docs/changelog/CHANGELOG_USER_MEMBRO_2026_07.md) | Ponte User ↔ Membro |
| [`docs/changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](docs/changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md) | MandatoDetail + H2 + snapshot eventos |
| [`docs/changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](docs/changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md) | Finance OSC + Documents |
| [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Domínio: signup → setup → operação → H2 |
| [`docs/guias/UI_PADRAO_WELLSAAS.md`](docs/guias/UI_PADRAO_WELLSAAS.md) | Como estilizar páginas novas |
| [`docs/referencia/STATUS_SPRINTS_FASE1.md`](docs/referencia/STATUS_SPRINTS_FASE1.md) | Status Sprints 1–5 + pós-Sprint 5 |
| [`docs/referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](docs/referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Gaps (User↔Membro, Stripe, etc.) |
| [`docs/modulos/ECOMMERCE.md`](docs/modulos/ECOMMERCE.md) | E-commerce + Associe-se |
| [`docs/modulos/COURSES.md`](docs/modulos/COURSES.md) | **Cursos** (port WellSaaS + loja) |
| [`docs/modulos/FORMULARIOS.md`](docs/modulos/FORMULARIOS.md) | **Formulários** (adaptado do QPC) |
| [`docs/modulos/CONTATOS.md`](docs/modulos/CONTATOS.md) | **Contatos** (CRM do site) |
| [`docs/modulos/SUPORTE.md`](docs/modulos/SUPORTE.md) | **Suporte** (chamados → equipe Gesttora) |
| [`docs/modulos/MENSAGENS.md`](docs/modulos/MENSAGENS.md) | **Mensagens** diretoria ↔ associado |
| [`docs/changelog/CHANGELOG_CONTATOS_SUPORTE_MENSAGENS_2026_10.md`](docs/changelog/CHANGELOG_CONTATOS_SUPORTE_MENSAGENS_2026_10.md) | Contatos, suporte, mensagens, certificados de evento, e-mails |
| [`docs/modulos/USUARIOS_PERFIS.md`](docs/modulos/USUARIOS_PERFIS.md) | **Usuários e perfis** (gestor, diretoria, administrativo, financeiro) |
| [`docs/changelog/CHANGELOG_USUARIOS_PERFIS_2026_10.md`](docs/changelog/CHANGELOG_USUARIOS_PERFIS_2026_10.md) | Perfis de acesso, convite por e-mail, definição/redefinição de senha |
| [`docs/modulos/WEBSITE_CMS_TENANT.md`](docs/modulos/WEBSITE_CMS_TENANT.md) | **Website público do tenant** |
| [`docs/changelog/CHANGELOG_CMS_TENANT_PLANEJAMENTO_2026_08.md`](docs/changelog/CHANGELOG_CMS_TENANT_PLANEJAMENTO_2026_08.md) | Planejamento CMS 2026-08 |
| [`docs/changelog/CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md`](docs/changelog/CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md) | **Roadmap 2026-10**: régua, pagamento online, loja, eventos, anais, carteirinha, ficha 360, publicações, assembleias, newsletter, diretório, agendador |
| [`docs/modulos/MEMBROS.md`](docs/modulos/MEMBROS.md) | **Membros**: anuidades, régua diária, carteirinha, diretório público |
| [`docs/modulos/PUBLICACOES.md`](docs/modulos/PUBLICACOES.md) | **Publicações** (dossiês, e-books, acesso por venda/associado) |
| [`docs/modulos/GOVERNANCA.md`](docs/modulos/GOVERNANCA.md) | **Assembleias e votações** (quórum, cédula, ata com hash) |
| [`docs/modulos/NEWSLETTER.md`](docs/modulos/NEWSLETTER.md) | **Newsletter** (público, fila, descadastro) |
| [`PROMPT_DEPLOY.md`](PROMPT_DEPLOY.md) | Roteiro de deploy staging → produção e regras de segurança do droplet |

---

## Migrations (django-tenants)

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

Seed tenants:
- `./scripts/init_sistema_tenant.sh` — `sistema` + `abciber` (`diretoria@abciber.org.br` / `abciber123`)
- `./scripts/init_demo_tenant.sh` — tenant `demo` (`demo@demo.com` / `demo`) + website/anuidades

**Droplet:** rodar seed em **cada** ambiente após 1º deploy — ver [`DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md).

---

## Reutilização WellSaaS

Já adaptado:
- Multi-tenancy, JWT, middleware
- UI shell + Dashboard.css + Login.css
- Signup simulado + setup 1º mandato
- finance OSC + documents
- MandatoDetail + deep-links da transição
- Ponte User↔Membro + portal associado (`/app/portal`)
- Landing SaaS Gesttora em `/` (estática; `gesttora.vertent.com.br`)
- E-commerce (`ecommerce/`) + Website CMS tenant (`website/`, `/site`, `/app/website`)
- Cursos (`courses/`) integrados à loja + certificado PDF (`core/certificates.py`) — ver [`COURSES.md`](docs/modulos/COURSES.md)
- Formulários (`formularios/`, a partir do QPC) — ver [`FORMULARIOS.md`](docs/modulos/FORMULARIOS.md)
- Contatos (`contatos/`, a partir de `contacts`), Suporte (`support/`, no schema public) e Mensagens (`mensagens/`)
- Certificados de evento com QR + verificação unificada; e-mails transacionais (`core/emails.py`)
- Usuários e perfis de acesso (gestor/diretoria/administrativo/financeiro), convite por e-mail e
  “esqueci a senha” — modelo da equipe da clínica WellSaaS — ver [`USUARIOS_PERFIS.md`](docs/modulos/USUARIOS_PERFIS.md)

Próximos a portar (funcionalidade; UI segue o CSS semântico do AssApp, sem shadcn):
1. Ajuda in-app (`frontend/src/help/`)
2. Esconder ações de edição nas páginas em modo somente leitura (perfis)

Copiar/adaptar depois (Stripe por último):
- Convite de acesso ao portal a partir do cadastro do Membro (associado); JWT `tenant_schema`
- Stripe real, `adminpanel` (edição da landing Gesttora, `AdminPlan`/`PlatformModule`), `subscriptions` (anuidade recorrente)
- Integrações Google Calendar / WhatsApp
- Site de evento, publicações, certificados (módulos futuros)

**Não copiar:** booking/agenda, programs, meal plans, prescricao, phyto, supplement, workouts, habits, metrics, check-ins, clinic/team — e-commerce usa motor WellSaaS adaptado em `ecommerce/`

---

**Última revisão:** 2026-10-16
