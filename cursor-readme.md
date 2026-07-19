# AssApp — Referência Técnica para o Cursor

> Consulte este arquivo primeiro. Links para docs detalhados em `docs/`.  
> **Última revisão:** 2026-07-19 (branches orb/assapp + OrbStack + DigitalOcean)

---

## Branches Git

| Branch | Ambiente | CI |
|--------|----------|-----|
| `orb` | Dev Mac / OrbStack | nenhum |
| `develop` | Staging DO `:8080` | `deploy-staging.yml` |
| `assapp` | **Produção** DO `:80` | `deploy-production.yml` |

```
orb → develop (staging) → assapp (produção)
```

Mac: `./scripts/up-orb.sh` · Docs: [`ESTRATEGIA_BRANCHES_ORBSTACK.md`](docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md) · [`DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md)

---

## Stack

Django 4.2 + DRF + JWT + django-tenants + PostgreSQL 14 + React 18 + TS + Vite

**Não usar Prisma em runtime** — `prisma/schema.prisma` é documentação de domínio PIPE.

**UI:** CSS semântico padrão WellSaaS (`Dashboard.css`, `AppLayout.css`, `Login.css`) — ver [`docs/guias/UI_PADRAO_WELLSAAS.md`](docs/guias/UI_PADRAO_WELLSAAS.md).

---

## Schemas PostgreSQL

| Schema | Conteúdo |
|--------|----------|
| `public` | tenants (com `setup_completed`, `plan_slug`), domains |
| `sistema` | superadmin |
| `{associacao}` | mandatos ★, memoria ★, eventos ★, membros, finance, documents, accounts |

> `adminpanel` / `payments` — stubs; Stripe continua simulado. `finance` e `documents` ativos no tenant.

---

## Apps TENANT (por associação)

| App | PIPE | Descrição |
|-----|------|-----------|
| `mandatos` | ★ H1+H2 | Mandatos, transição, onboarding H2 |
| `memoria` | ★ H1 | ContextoHistorico, timeline |
| `eventos` | ★ H3 | CFP, pareceres, anais |
| `membros` | — | Filiados, anuidades |
| `finance` | — | Lançamentos OSC, dashboard, e-mail fechamento |
| `documents` | — | Upload / audiência / meus |
| `accounts` | — | User, JWT, register, setup |

---

## Roles de Usuário

```
superadmin | association_admin | board_member | member | reviewer
```

---

## API Prefixos

```
/api/auth/       accounts  (login, register, plans, setup, tenant-status, me)
/api/mandatos/   mandatos  ★
/api/memoria/    memoria   ★
/api/eventos/    eventos   ★
/api/membros/    membros
/api/finance/    finance (OSC)
/api/documents/  documents (+ meus/)
```

Auth detalhado: [`docs/modulos/AUTH_SIGNUP_SETUP.md`](docs/modulos/AUTH_SIGNUP_SETUP.md)  
Finance: [`docs/modulos/FINANCE.md`](docs/modulos/FINANCE.md) · Documents: [`docs/modulos/DOCUMENTS.md`](docs/modulos/DOCUMENTS.md)

---

## Ciclo de vida (domínio)

```
Signup (simulado) → Setup (1º mandato) → Operação → Transição H2
```

Ver: [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md)

---

## Hipóteses PIPE (comentar no código)

- **H1:** MandatoSnapshot, ContextoHistorico
- **H2:** OnboardingEtapa, PerfilTecnico, UI adaptativa (transição — não confundir com Setup)
- **H3:** EventoAcademico integrado com Membro

Ver: [`docs/pesquisa/HIPOTESES_PIPE.md`](docs/pesquisa/HIPOTESES_PIPE.md)

---

## Documentação / ação futura

| Documento | Conteúdo |
|-----------|----------|
| [`docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`](docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md) | Branches + OrbStack ARM |
| [`docs/guias/GIT_WORKFLOW.md`](docs/guias/GIT_WORKFLOW.md) | Fluxo Git / push sequencial |
| [`docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_ASSAPP.md`](docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_ASSAPP.md) | Promoção orb → develop → assapp |
| [`docs/guias/DEPLOY_DIGITALOCEAN.md`](docs/guias/DEPLOY_DIGITALOCEAN.md) | Deploy DigitalOcean |
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

---

## Migrations (django-tenants)

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

Seed demo: `./scripts/init_sistema_tenant.sh`

---

## Reutilização WellSaaS

Já adaptado:
- Multi-tenancy, JWT, middleware
- UI shell + Dashboard.css + Login.css
- Signup simulado + setup 1º mandato
- finance OSC + documents
- MandatoDetail + deep-links H2
- Ponte User↔Membro + portal associado (`/app/portal`)

Copiar/adaptar depois (Stripe por último):
- Convite User a partir de Membro; JWT `tenant_schema`
- Stripe real, `adminpanel`, landing, website CMS

**Não copiar:** business (meal plans, recipes), prescricao, e-commerce

---

**Última revisão:** 2026-07-19
