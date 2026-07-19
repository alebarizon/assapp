# Changelog consolidado — 2026-07-14

> Resumo de todas as alterações de produto, domínio e UI feitas neste dia.  
> Detalhes técnicos: ver changelogs específicos abaixo.

---

## 1. Fluxo comercial — Signup simulado + Setup do 1º mandato

**Decisão de domínio:** assinatura → setup pós-compra (1º mandato) → operação → transição H2 (dois wizards distintos).

### Backend
- `Tenant`: `setup_completed`, `plan_slug`, `payment_simulated` (migration `tenants.0002`)
- `POST /api/auth/register/` — provisiona Tenant + Domain + schema + `association_admin` (sem Stripe)
- `GET /api/auth/plans/` — planos estáticos `starter` / `profissional`
- `POST /api/auth/setup/` — dados da associação + Mandato #1 + cargos
- `GET /api/auth/tenant-status/` — flag para o guard do frontend
- Login devolve `setup_completed` + objeto `tenant`

### Frontend
- `/signup` — `Signup.tsx`
- `/app/setup` — `AssociationSetup.tsx` (wizard separado do H2)
- Guard: `!setup_completed` → força setup; após setup bloqueia `/app/setup`
- Seed demo: `abciber` e `sistema` com `setup_completed=True`

**Docs:** [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) · [`CHANGELOG_SIGNUP_SETUP_2026_07.md`](CHANGELOG_SIGNUP_SETUP_2026_07.md)

---

## 2. UI alinhada ao WellSaaS

Shell e páginas migrados de Tailwind utilitário puro para **CSS semântico** do WellSaaS (paleta warm `#f6f6f3` / `#131313` / accent `#9a6a0b`).

### Fundação CSS
- `frontend/src/styles/Dashboard.css` — `dashboard-page`, botões, forms, KPIs, loading
- `frontend/src/components/AppLayout.css` — `main-layout`, sidebar card-like
- `frontend/src/pages/Login.css` — auth split-screen
- `frontend/src/index.css` — tokens + extras (`list-card`, `status-badge`, tabs)

### Telas
- Auth: Login, Signup (hero + form)
- Shell: `AppLayout` (sidebar clara, header sticky)
- App: Setup, Mandatos, Memória, Onboarding H2, Membros*, Eventos*, Finance, Documents

**Docs:** [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md) · [`CHANGELOG_UI_WELLSAAS_2026_07.md`](CHANGELOG_UI_WELLSAAS_2026_07.md)

---

## 3. Finance OSC + Documents

Fatia **1A + 2A** (Stripe continua simulado).

### Backend
- `finance` em `TENANT_APPS`: `Transaction` com categorias OSC; CRUD + dashboard + monthly-report + send-report-email (503 se SMTP off)
- Espelho idempotente: pagamento de anuidade → Transaction `income`/`anuidade` (`referencia`)
- `documents`: upload multipart (~10MB), audience `geral`|`diretoria`|`membro`, `GET meus/`
- Snapshot H1: contagens de anuidades + saldo do mês corrente

### Frontend
- `/app/finance`, `/app/documents` + itens no menu
- Deep-link H2: etapa `revisar_financeiro` → Financeiro

**Docs:** [`FINANCE.md`](../modulos/FINANCE.md) · [`DOCUMENTS.md`](../modulos/DOCUMENTS.md) · [`CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](CHANGELOG_FINANCE_DOCUMENTS_2026_07.md)

---

## 4. Fora de escopo (ainda pendente)

| Item | Status |
|------|--------|
| Stripe real / AdminPlan / webhooks | ❌ |
| `adminpanel` no `INSTALLED_APPS` | Stub |
| Landing AssApp + website CMS do tenant | ❌ |
| `MandatoDetail.tsx` + timeline na tela Mandatos | ❌ |
| Onboarding H2 deep-links (membros/eventos) | ⚠️ Parcial (`revisar_financeiro` feito) |
| `integrations/` (Calendar / NF) | Ausente |
| Ponte formal `User` ↔ `Membro` | Gap documentado |

---

## Arquivos de referência atualizados neste dia

| Documento | O que mudou |
|-----------|-------------|
| [`README.md`](../../README.md) | Finance/Documents na API, roadmap e estrutura FE |
| [`cursor-readme.md`](../../cursor-readme.md) | Apps tenant + prefixos API |
| [`STATUS_SPRINTS_FASE1.md`](../referencia/STATUS_SPRINTS_FASE1.md) | Sprint 4 / pós-5 com finance+docs |
| [`ANALISE_VINCULOS_*.md`](../referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Gaps finance/snapshot atualizados |
| [`FLUXO_ASSINATURA_*.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Operação inclui finance/docs |
| [`FINANCE.md`](../modulos/FINANCE.md) / [`DOCUMENTS.md`](../modulos/DOCUMENTS.md) | Novos |
| [`CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](CHANGELOG_FINANCE_DOCUMENTS_2026_07.md) | Detalhe da fatia |
