# Análise de vínculos entre módulos e multi-tenancy

> **Status:** documento de referência — gaps e backlog  
> **Data da análise:** 2026-07-13  
> **Atualização:** 2026-07-15 — MandatoDetail; User↔Membro; portal associado; Stripe adiado  
> **Contexto:** verificação geral pós-Sprint 5 (MVP Fase 1 PIPE) + evolução SaaS parcial  
> **Decisão:** Stripe/comercialização por último; priorizar PIPE e portal associado.

---

## Objetivo

Registrar o estado atual dos vínculos entre módulos do AssApp, com foco na hierarquia:

```
SaaS (AssApp)  →  Associação (tenant)  →  Membros (da associação)
```

Este material serve para entender o sistema antes de decidir prioridades de evolução (produção SaaS, ponte User↔Membro, financeiro completo, etc.).

---

## 1. Hierarquia de três níveis

```
┌─────────────────────────────────────────────────────────────┐
│  NÍVEL 1 — SaaS (AssApp)                                    │
│  Schema `public`: Tenant, Domain, metadados da plataforma   │
│  Schema `sistema`: superadmin da plataforma                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1 Tenant = 1 Associação
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  NÍVEL 2 — Associação (tenant)                              │
│  Schema PostgreSQL isolado (ex: `abciber`)                  │
│  Contém: User, Mandato, Membro, Evento, Memória...          │
└──────────────────────────────┬──────────────────────────────┘
                               │ quadro associativo
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  NÍVEL 3 — Membros da associação                            │
│  Entidade `Membro` + `Filiacao` + `Anuidade`                │
│  (cadastro institucional; não é o mesmo que login no sistema)│
└─────────────────────────────────────────────────────────────┘
```

### Isolamento por nível

| Nível | Onde vive | Mecanismo |
|-------|-----------|-----------|
| SaaS | `public` + `sistema` | `Tenant` / `Domain` no schema compartilhado |
| Associação | schema `{slug}` (ex: `abciber`) | `django-tenants` — 1 schema por associação |
| Membros | dentro do schema da associação | sem FK para `Tenant`; isolamento pelo schema |

**Nota:** modelos de domínio (`Membro`, `Mandato`, `EventoAcademico`, etc.) **não possuem FK para `Tenant`**. O tenant é inferido pelo schema PostgreSQL ativo no request — padrão esperado com `django-tenants`.

---

## 2. O que está coerente hoje (MVP)

### Multi-tenancy funcional para demo

- `Tenant` representa a associação (`name`, `slug`, `cnpj`, `owner_id`)
- Cada associação tem schema próprio com `TENANT_APPS`: `mandatos`, `memoria`, `eventos`, `membros`, `accounts`
- Demo ABCiber no schema `abciber` com dados isolados

### Eixo central: `Mandato`

O mandato ativo (`Mandato.get_ativo()`) é o hub que conecta os módulos:

```
                    ┌──────────────┐
                    │   Mandato    │
                    │   (ativo)    │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Memória   │  │  Membros   │  │  Eventos   │
    │ contextos  │  │ filiações  │  │  CFP/anais │
    │  timeline  │  │ (opcional) │  │ (opcional) │
    └────────────┘  └────────────┘  └────────────┘
```

### Vínculos implementados e funcionais

| De | Para | Como |
|----|------|------|
| `Filiacao` | `Mandato` | FK opcional — nova filiação amarra ao mandato ativo |
| `ContextoHistorico` | `Mandato` | FK — decisões institucionais por gestão |
| `EventoAcademico` | `Mandato` | FK — evento criado com mandato ativo |
| `SubmissaoTrabalho` | `Membro` | FK opcional + vínculo por e-mail (H3) |
| `CargoMandato` | `User` | Diretoria = usuários do sistema |
| `Mandato.encerrar()` | `memoria` | Arquiva contextos automaticamente |

### H3 — integração membros + eventos

Implementada em `backend/eventos/services.py` via `vincular_membro_por_email()`: submissão de trabalho tenta encontrar `Membro` pelo e-mail do `User` autor.

---

## 3. Lacuna estrutural principal: `User` ≠ `Membro`

Existem **duas entidades distintas** para pessoas na associação:

| Entidade | Papel | Onde é usada |
|----------|-------|--------------|
| `User` | Login, diretoria, parecerista | `CargoMandato`, autenticação, pareceres |
| `Membro` | Cadastro associativo | Filiações, anuidades, submissões |

**Não há FK entre elas.** O único elo atual é matching por e-mail em `vincular_membro_por_email`.

### Consequências práticas

1. Um `User` com role `member` **não cria** automaticamente um `Membro`
2. Um `Membro` cadastrado pela diretoria **não ganha** acesso ao sistema
3. Um membro da diretoria (`CargoMandato.usuario`) pode **não existir** como `Membro` filiado
4. A role `member` no `User` e o registro `Membro` são conceitos paralelos, não sincronizados

### Ação futura sugerida (decisão pendente)

- Avaliar `Membro.user = OneToOneField(User, null=True)` ou fluxo de convite que cria ambos
- Definir regra de negócio: todo associado com acesso ao sistema precisa de `Membro`? E vice-versa?

---

## 4. Lacunas no nível SaaS → Associação

| Item | Status atual | Impacto |
|------|--------------|---------|
| API de provisionamento de tenant | ✅ Signup simulado | `POST /api/auth/register/`; Stripe real ainda não |
| Setup pós-compra (1º mandato) | ✅ | `POST /api/auth/setup/`, `AssociationSetup.tsx` |
| `User.tenant` FK | Existe; populado no register | Login demo/script pode ainda deixar vazio em seeds antigos |
| `Tenant.owner_id` | UUID solto, sem FK | Preenchido no register |
| `Tenant.setup_completed` / `plan_slug` | ✅ | Guard do frontend |
| JWT sem claim de tenant | Varredura O(n) de schemas a cada request | Não escala; e-mail duplicado entre tenants = ambiguidade |
| `Domain` (ex: `abciber.localhost`) | Criado no register/init | Middleware path-based; SPA usa varredura |
| Apps `adminpanel`, `payments` | Stub / fora do fluxo Stripe real | Signup simulado; Stripe depois |
| `finance`, `documents` | ✅ Em `TENANT_APPS` | Ver `FINANCE.md` / `DOCUMENTS.md` |
| Superadmin | Schema `sistema`, não `public` | Correto no código |

### Fluxo real do SPA (hoje)

```
Login → varre schemas → JWT
Request → TenantUserMiddleware varre schemas → connection.set_tenant(abciber)
```

Funciona para demo/MVP, mas não é o modelo SaaS de produção.

---

## 5. Lacunas entre módulos (dentro do tenant)

### 5.1 Snapshot (H1)

`Mandato.criar_snapshot()` inclui:

- dados do mandato e cargos
- contagens de membros (ativos / inadimplentes)
- decisões recentes da memória
- **anuidades** (pagas / pendentes / vencidas)
- **financeiro do mês** (receitas, despesas, saldo) via `finance.Transaction`
- **eventos ativos** (`inscricoes_abertas`, `cfp_aberto`, `em_avaliacao`) + lista resumida

Snapshot H1 considerado completo para o MVP PIPE.

### 5.2 Parâmetro `mandato` morto em anuidades

`gerar_anuidades_ano(..., mandato=)` em `backend/membros/services.py` recebe o mandato ativo mas **não o utiliza** — anuidades não ficam amarradas ao ciclo de gestão.

### 5.3 Financeiro (estado atual)

- ✅ App `finance/` com `Transaction` (categorias OSC), dashboard e espelho anuidade→income
- Stripe de anuidade / planos SaaS permanece **simulado**
- Onboarding H2: deep-link `revisar_financeiro` → `/app/finance`
- `ContextoHistorico` tipo `financeiro` e lançamentos `finance` coexistem (narrativa vs ledger)

### 5.4 Memória com links fracos

- `ContextoHistorico.entidade_tipo` + `entidade_id` — referência polimórfica sem FK
- `TimelineInstitucional.contexto_id` — UUID sem FK para `ContextoHistorico`

### 5.5 Onboarding (H2)

Deep-links nas etapas: `revisar_snapshot` → mandato anterior; `revisar_membros` → Membros; `revisar_financeiro` → Finance; `revisar_eventos` → Eventos; `revisar_decisoes` → Memória. Etapas ainda são checklist (sem fetch automático de KPIs no card).

### 5.6 Frontend

- `MembroDetail` não exibe o mandato da filiação (serializer expõe, UI não)
- `tenant_schema` salvo no `localStorage` mas **não enviado** nas requisições API

---

## 6. Mapa de relacionamentos (FKs reais)

```
Tenant (public) ── Domain

User ── CargoMandato ── Mandato
User ── SubmissaoTrabalho (autor)
User ── Parecer (parecerista)

Mandato ── Filiacao (opcional)
Mandato ── ContextoHistorico
Mandato ── EventoAcademico
Mandato ── MandatoSnapshot
Mandato ── Transaction (finance, opcional)

Membro ── Filiacao ── Anuidade
Membro ── SubmissaoTrabalho (opcional, H3)
Membro ── Document (opcional, audience=membro)
Membro ── user (OneToOne opcional) ── User

User ── Membro   ← ponte formal `membro_perfil` (2026-07-15); fallback e-mail no resolver
```

Arquivos de referência:

- `backend/tenants/models.py` — `Tenant`, `Domain`
- `backend/accounts/models.py` — `User`
- `backend/mandatos/models.py` — `Mandato`, `CargoMandato`, snapshots
- `backend/membros/models.py` — `Membro`, `Filiacao`, `Anuidade`
- `backend/memoria/models.py` — `ContextoHistorico`, `TimelineInstitucional`
- `backend/eventos/models.py` — `EventoAcademico`, CFP, submissões
- `backend/finance/models.py` — `Transaction`
- `backend/documents/models.py` — `Document`

---

## 7. Matriz de saúde por módulo

| Módulo | Isolamento tenant | Vínculo mandato | Vínculo membro | Completude MVP |
|--------|-------------------|-----------------|----------------|----------------|
| `tenants` | N/A (public) | — | — | Signup simulado OK; Stripe real falta |
| `accounts` | Por schema | via `CargoMandato` | `membro_perfil` | Roles OK; ponte User↔Membro |
| `mandatos` | OK | hub central | indireto (snapshot) | MandatoDetail + snapshot completo |
| `memoria` | OK | FK forte | polimórfico fraco | H1 funcional |
| `membros` | OK | FK em filiação | raiz + `user` FK | Anuidades + vínculo User |
| `eventos` | OK | FK em evento | H3 por e-mail | Fluxo CFP completo |
| `finance` | OK | FK opcional | via anuidade espelhada | CRUD + dashboard OSC |
| `documents` | OK | — | FK opcional | Upload + `meus/` |

---

## 8. Backlog de ações futuras (priorizado)

> **Não implementar sem revisão e decisão de produto.** Itens listados para quando houver clareza sobre o modelo de negócio (especialmente User vs Membro).

### Alta prioridade (arquitetura de domínio)

- [x] **Ponte `User` ↔ `Membro`** — `Membro.user` OneToOne + vincular/desvincular (2026-07-15); convite SMTP ainda não
- [x] **Snapshot financeiro (H1)** — anuidades + saldo do mês (2026-07-14)
- [x] **Snapshot eventos ativos (H1)** — 2026-07-15
- [ ] **JWT com `tenant_schema`** — eliminar varredura de schemas a cada request

### Média prioridade (coerência PIPE)

- [ ] Usar parâmetro `mandato` em `gerar_anuidades_ano` (amarrar cobrança ao ciclo de gestão)
- [x] Deep-links onboarding H2 (membros / finance / eventos / memória / snapshot)
- [ ] FK `TimelineInstitucional.contexto` → `ContextoHistorico`

### Baixa prioridade (SaaS produção)

- [x] API de provisionamento de associação — **signup simulado** (`POST /api/auth/register/`, 2026-07-14); Stripe real ainda não
- [x] Setup pós-compra com 1º mandato (`POST /api/auth/setup/`)
- [ ] Popular `User.tenant` no seed `init` (register já popula); FK real `Tenant.owner`
- [x] App `finance` OSC + `documents` (2026-07-14)
- [ ] Stripe / `AdminPlan` / `adminpanel`

---

## 9. Conclusão (estado em 2026-07-14)

O AssApp tem base sólida para o MVP da pesquisa PIPE:

- **Isolamento por associação** funciona via schema PostgreSQL
- **`Mandato`** conecta memória, membros, eventos e (agora) finance
- **H3** (eventos + membros) está implementada, ainda que por e-mail
- **Signup simulado + setup**, **UI WellSaaS**, **Finance OSC**, **Documents**, **MandatoDetail** e deep-links H2 entregues

A maior inconsistência conceitual de User vs Membro foi **atenuada** com `Membro.user` (2026-07-15). Permanecem: convite SMTP, sync de roles e portal do associado.

---

## Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [`CHANGELOG_2026_07_15.md`](../changelog/CHANGELOG_2026_07_15.md) | Consolidado do dia 15/07 |
| [`CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](../changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md) | Portal associado |
| [`CHANGELOG_USER_MEMBRO_2026_07.md`](../changelog/CHANGELOG_USER_MEMBRO_2026_07.md) | Ponte User ↔ Membro |
| [`CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](../changelog/CHANGELOG_MANDATO_DETAIL_H2_2026_07.md) | MandatoDetail + H2 |
| [`CHANGELOG_2026_07_14.md`](../changelog/CHANGELOG_2026_07_14.md) | Consolidado 14/07 |
| [`FINANCE.md`](../modulos/FINANCE.md) / [`DOCUMENTS.md`](../modulos/DOCUMENTS.md) | APIs dos módulos |
| [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Signup → setup → H2 |
| [`AUTH_SIGNUP_SETUP.md`](../modulos/AUTH_SIGNUP_SETUP.md) | Endpoints auth |
| [`STATUS_SPRINTS_FASE1.md`](STATUS_SPRINTS_FASE1.md) | Status dos Sprints 1–5 e pós-5 |
| [`SCHEMA_DOMINIO.md`](../modulos/SCHEMA_DOMINIO.md) | Diagrama ER conceitual |
| [`HIPOTESES_PIPE.md`](../pesquisa/HIPOTESES_PIPE.md) | H1, H2, H3 |
| [`MANDATOS.md`](../modulos/MANDATOS.md) | Ciclo de mandato e onboarding |
| [`MEMBROS.md`](../modulos/MEMBROS.md) | Quadro associativo e anuidades |
| [`EVENTOS.md`](../modulos/EVENTOS.md) | CFP, pareceres, anais (H3) |
| [`cursor-readme.md`](../../cursor-readme.md) | Referência técnica rápida |

---

**Última atualização:** 2026-07-15
