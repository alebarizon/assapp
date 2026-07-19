# Status dos Sprints — Fase 1 PIPE (MVP)

> **Status:** documento de referência — planejamento + atualizações  
> **Data da análise original:** 2026-07-13  
> **Atualização:** 2026-07-15 — MandatoDetail, User↔Membro, portal associado  
> **Contexto:** pós-Sprint 5; PIPE/ABCiber; Stripe adiado

---

## Resumo executivo

Os **5 sprints** da Fase 1 PIPE estão **concluídos**.  
**2026-07-14:** signup/setup, UI WellSaaS, Finance + Documents.  
**2026-07-15:** MandatoDetail + H2, ponte User↔Membro, portal do associado.

| Conclusão | Detalhe |
|-----------|---------|
| Sprints 1–5 | ✅ Concluídos |
| 2026-07-14 | ✅ Signup/Setup + UI + Finance + Documents |
| 2026-07-15 | ✅ MandatoDetail/H2 + User↔Membro + portal associado |
| Stripe / adminpanel / landing | ❌ Adiado (não comercializar de imediato) |

**Consolidado do dia:** [`CHANGELOG_2026_07_15.md`](../changelog/CHANGELOG_2026_07_15.md)

---

## Tabela geral — Sprints 1 a 5 (+ pós)

| Sprint | Tema | PIPE | Status | Changelog |
|--------|------|------|--------|-----------|
| **1** | Fundação (Docker, models, auth) | — | ✅ Concluído | *(sem changelog dedicado)* |
| **2** | Mandatos + Onboarding H2 | H1 + H2 | ✅ Concluído | [`CHANGELOG_SPRINT2_…`](../changelog/CHANGELOG_SPRINT2_MANDATOS_2026_07.md) + MandatoDetail |
| **3** | Memória Institucional | H1 | ✅ Concluído | [`CHANGELOG_SPRINT3_…`](../changelog/CHANGELOG_SPRINT3_MEMORIA_2026_07.md) |
| **4** | Membros + Anuidades (+ Finance OSC) | — | ✅ Concluído | [`CHANGELOG_SPRINT4_…`](../changelog/CHANGELOG_SPRINT4_MEMBROS_2026_07.md) + finance |
| **5** | Eventos + CFP | H3 | ✅ Concluído | [`CHANGELOG_SPRINT5_…`](../changelog/CHANGELOG_SPRINT5_EVENTOS_2026_07.md) |
| **Pós-5** | Signup/Setup + UI + Finance + Docs | — | ✅ 2026-07-14 | [`CHANGELOG_2026_07_14.md`](../changelog/CHANGELOG_2026_07_14.md) |
| **+15/07** | Mandatos H2 + User↔Membro + Portal | H1–H2 | ✅ 2026-07-15 | [`CHANGELOG_2026_07_15.md`](../changelog/CHANGELOG_2026_07_15.md) |

---

## Sprint 1 — Fundação

**Status:** ✅ Concluído

### Entregas (conforme `README.md`)

- [x] README e estrutura de pastas
- [x] Schema Prisma + modelos Django iniciais
- [x] Docker Compose funcional
- [x] Auth JWT com novos roles

### Observações

- Não há `CHANGELOG_SPRINT1_*.md` — apenas registro no README.
- Infra compartilhada com WellSaaS (~80%): `tenants`, `accounts`, middleware, Docker.

---

## Sprint 2 — Mandatos + Onboarding

**Status:** ✅ Concluído (MandatoDetail + deep-links H2 em 2026-07-15)  
**Hipóteses:** H1 (snapshot, transição) + H2 (onboarding adaptativo)

### Entregas concluídas

- [x] CRUD Mandato com cargos da diretoria
- [x] Transição automática entre mandatos
- [x] Snapshot ao encerrar/iniciar transição (inclui anuidades, finance, eventos ativos)
- [x] Wizard de onboarding (`OnboardingWizard.tsx`)
- [x] API `/api/mandatos/` completa
- [x] Frontend `Mandatos.tsx`, `Login.tsx`
- [x] `MandatoDetail.tsx` — cargos + timeline + snapshots (`/app/mandatos/:id`)
- [x] Deep-links H2: snapshot / membros / finance / eventos / memória

Changelog: [`CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](../changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md)

### Observação

Memória Institucional mantém timeline do mandato **ativo**; o detalhe do mandato mostra a timeline **daquele** mandato.

---

## Sprint 3 — Memória Institucional

**Status:** ✅ Concluído  
**Hipótese:** H1

### Entregas

- [x] `ContextoHistorico` com vínculo a mandatos
- [x] Notas institucionais contextualizadas
- [x] Arquivamento automático ao encerrar mandato
- [x] API `/api/memoria/`
- [x] Frontend `MemoriaInstitucional.tsx` (registros + timeline)

### Observações

- Página inicial padrão do app: `/app/memoria`
- Gaps arquiteturais documentados em [`ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](ANALISE_VINCULOS_MODULOS_E_TENANCY.md) (links polimórficos fracos) — não bloqueiam o MVP

---

## Sprint 4 — Membros + Anuidades

**Status:** ✅ Concluído (Finance OSC entregue em 2026-07-14)

### Entregas concluídas

- [x] CRUD membros com histórico de filiação
- [x] Anuidades: gerar lote, vencidas, registrar pagamento
- [x] KPIs (`/api/membros/membros/resumo/`)
- [x] Frontend `Membros.tsx`, `MembroDetail.tsx`
- [x] Demo: 4 associados (1 inadimplente) no `init_sistema_tenant.sh`
- [x] **Finance OSC** — `Transaction`, dashboard, espelho anuidade→tx, UI `/app/finance`  
  Detalhe: [`CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](../changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md) · [`FINANCE.md`](../modulos/FINANCE.md)

### Observação

Stripe real para anuidades permanece simulado; o módulo `finance` cobre lançamentos manuais + espelho de pagamento registrado.

---

## Sprint 5 — Eventos Científicos

**Status:** ✅ Concluído  
**Hipótese:** H3

### Entregas

- [x] `EventoAcademico` + Call for Papers
- [x] Submissão e atribuição de pareceristas
- [x] Geração de anais
- [x] API `/api/eventos/` testada
- [x] Frontend `Eventos.tsx`, `EventoDetail.tsx`
- [x] Demo: VII Encontro ABCiber 2026 com CFP e submissão aceita

### Observações

- Integração H3 com membros via resolver User↔Membro (FK + e-mail)
- Validação E2E completa na UI (CFP → submissão → parecer → anais) recomendada antes de demo com ABCiber

---

## O que NÃO é sprint — mas está no roadmap

Módulos e funcionalidades mencionados no `README.md` / `cursor-readme.md` que **nunca viraram sprint numerado**:

| Item | Status | Fase sugerida |
|------|--------|---------------|
| `finance/` — lançamentos, relatórios OSC | ✅ Entregue (2026-07-14) | — |
| `documents/` — upload e compartilhamento | ✅ Entregue (2026-07-14) | Portal associado completo: depois |
| `integrations/` — Google Calendar, NF | Não implementado | Fase 2 |
| `adminpanel/` — superadmin SaaS, planos | Stub, fora de `INSTALLED_APPS` | Produção SaaS |
| `payments/` — Stripe | Stub; signup usa pagamento **simulado** | Produção |
| API de provisionamento de tenants | ✅ Signup simulado (`/api/auth/register/`) | Stripe real depois |
| Setup pós-compra (1º mandato) | ✅ `/app/setup` | — |
| UI padrão WellSaaS | ✅ Shell + páginas | — |
| Ponte `User` ↔ `Membro` | ✅ FK + APIs | Convite SMTP depois |
| Portal associado mínimo | ✅ `/app/portal` (2026-07-15) | Ampliar se necessário |
| Compliance Marco Legal OSCs | Roadmap | Fase 2 |
| Mensagens, agendamentos diretoria | Mencionados vs WellSaaS | Fase 2 |
| Landing AssApp + website do tenant | Não trazido | Fase 2 / produção |

---

## Proposta: o que seria um Sprint 6?

> **Não definido oficialmente.** Opções para discussão futura.  
> **Decisão de produto (2026-07-14):** fluxo assinatura → setup → operação → transição documentado em [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](FLUXO_ASSINATURA_SETUP_TRANSICAO.md).

### Opção A — Fechar lacunas da Fase 1

~~1–2.~~ **Feito (2026-07-15)** — MandatoDetail + deep-links H2; snapshot com eventos ativos.  
Pendências menores: validação E2E ABCiber na UI; seletor histórico na página Memória (opcional).

### Opção B — Financeiro OSC

~~1–3.~~ **Feito (2026-07-14)** — ver [`FINANCE.md`](../modulos/FINANCE.md). Próximo passo natural nesta linha: Stripe real nas anuidades.

### Opção C — Produção SaaS (alinhada ao fluxo oficial)

1. ~~Signup + provisionamento de tenant (fase ①)~~ → **Signup simulado feito** (2026-07-14)
2. ~~Setup wizard pós-compra com **1º mandato** (fase ②)~~ → **Feito**
3. Stripe real + `AdminPlan` + webhooks
4. JWT com claim `tenant_schema` robusto + `adminpanel` / planos editáveis
5. Landing AssApp + website do tenant

### UI (2026-07-14)

- ✅ Shell `AppLayout` + `Dashboard.css` + auth split-screen
- Guia: [`docs/guias/UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md)

### Opção D — Arquitetura de domínio

1. ~~Ponte `User` ↔ `Membro`~~ → **feito** (FK + vincular; sem SMTP)
2. JWT com claim `tenant_schema`
3. FKs fracos em memória se necessário

Ver detalhes dos gaps em [`ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](ANALISE_VINCULOS_MODULOS_E_TENANCY.md).

---

## Rastreabilidade PIPE ↔ Sprints

| Hipótese | Sprint(s) | Status MVP |
|----------|-----------|------------|
| **H1** — Memória auditável entre mandatos | 2, 3 | ✅ Snapshot completo (membros, anuidades, finance, eventos) + MandatoDetail |
| **H2** — Interface adaptativa / onboarding | 2 | ✅ Wizard + deep-links módulos |
| **H3** — Membros + eventos integrados | 4, 5 | ✅ Funcional (vínculo por e-mail) |

Fonte: [`docs/pesquisa/HIPOTESES_PIPE.md`](../pesquisa/HIPOTESES_PIPE.md)

---

## Checklist rápido — "Falta implementar algum sprint?"

| Pergunta | Resposta |
|----------|----------|
| Existe Sprint 6 planejado? | **Não** formalmente |
| Algum sprint 1–5 inteiro por fazer? | **Não** |
| Itens `[ ]` no README? | Sim — Stripe, integrations |
| Módulos no README sem código completo? | `integrations`, `adminpanel`, `payments` (Stripe real) |
| Próximo passo natural? | Convite User a partir do Membro **ou** JWT tenant_schema (Stripe por último) |

---

## Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [`README.md`](../../README.md) | Roadmap MVP + pós-Sprint 5 |
| [`docs/changelog/CHANGELOG_2026_07_15.md`](../changelog/CHANGELOG_2026_07_15.md) | **Consolidado 2026-07-15** |
| [`docs/changelog/CHANGELOG_2026_07_14.md`](../changelog/CHANGELOG_2026_07_14.md) | Consolidado 2026-07-14 |
| [`docs/changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](../changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md) | MandatoDetail + H2 |
| [`docs/changelog/CHANGELOG_USER_MEMBRO_2026_07.md`](../changelog/CHANGELOG_USER_MEMBRO_2026_07.md) | Ponte User ↔ Membro |
| [`docs/changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](../changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md) | Portal associado |
| [`docs/changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](../changelog/CHANGELOG_FINANCE_DOCUMENTS_2026_07.md) | Finance + Documents |
| [`docs/modulos/FINANCE.md`](../modulos/FINANCE.md) / [`DOCUMENTS.md`](../modulos/DOCUMENTS.md) / [`MEMBROS.md`](../modulos/MEMBROS.md) | APIs dos módulos |
| [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Domínio signup → setup → H2 |
| [`docs/guias/UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md) | Padrão visual |
| [`docs/referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Gaps arquiteturais |
| [`docs/pesquisa/HIPOTESES_PIPE.md`](../pesquisa/HIPOTESES_PIPE.md) | H1, H2, H3 |
| [`cursor-readme.md`](../../cursor-readme.md) | Referência técnica rápida |

---

**Última atualização:** 2026-07-15
