# Fluxo — Assinatura, Setup da Associação e Transição de Mandato

> **Status:** referência de domínio — decisão de produto **e implementação parcial** (2026-07-14)  
> **Contexto:** alinhamento pós-Sprint 5; fases ① (signup simulado) e ② (setup) **implementadas**  
> **Uso:** consultar ao evoluir Stripe, adminpanel, deep-links H2 ou websites

---

## Decisão resumida

| Tema | Decisão |
|------|--------|
| Quem cria o **1º mandato**? | O `association_admin` (quem assinou), no **setup pós-compra** — não o superadmin |
| Papel do **superadmin** | Planos SaaS, tenants, suspensão/reativação, landing do AssApp |
| Onboarding H2 (PIPE) | Só **transição entre mandatos** (nova diretoria) |
| Setup pós-compra | Wizard **separado** — configuração inicial da associação, incluindo o 1º mandato |

Há **dois wizards**. Não reutilizar o mesmo modelo `OnboardingEtapa` / `TransicaoMandato` para o setup da conta.

---

## Ciclo de vida completo

```
① ASSINATURA (público — SaaS)
   Landing AssApp → Signup → plano → Stripe
        │
        ▼
   Provisiona Tenant + schema + User(association_admin)
   setup_completed = false  |  sem mandato ativo
        │
        ▼
② SETUP DA ASSOCIAÇÃO (painel — uma vez)
   Wizard de configuração inicial
   Inclui: dados cadastrais, 1º mandato, diretoria, logo/preferências
        │
        ▼
   setup_completed = true  |  Mandato #1 ATIVO
        │
        ▼
③ OPERAÇÃO (ciclo do mandato)
   Membros · Memória · Eventos · Anuidades · …
        │
        │  (~2 anos / fim do período)
        ▼
④ TRANSIÇÃO DE MANDATO (H2 — PIPE)
   Inicia transição → snapshot → wizard Nova Diretoria
   Mandato N+1 ativo · Mandato N encerrado
        │
        └──────────► volta a ③
```

---

## Fase ① — Assinatura (compra do SaaS)

### Quem age
Pessoa da associação (futuro `association_admin` / `Tenant.owner`).

### Entrada (dados mínimos)
| Campo | Destino |
|-------|---------|
| Nome da associação | `Tenant.name` |
| CNPJ | `Tenant.cnpj` |
| Endereço / cidade / UF | `Tenant` (estender se necessário) |
| Telefone | `User.phone_number` e/ou `Tenant` |
| Nome + e-mail do contato | `User` (role `association_admin`) |
| Plano escolhido | Stripe + metadados do tenant (`on_trial`, `paid_until`) |

### Efeitos
1. Checkout Stripe (padrão WellSaaS: session no signup, webhook ativa o tenant)
2. Criação do `Tenant` + `Domain` + schema PostgreSQL
3. Criação do `User` owner no schema do tenant
4. Tenant ativo/trial — **ainda sem mandato**, **setup incompleto**

### O que NÃO acontece aqui
- Criação de mandato / diretoria
- Importação de membros
- Configuração do website da associação

### Referência WellSaaS
Cadastro de empreendedor → tenant + checkout Stripe → painel. Adaptar papéis e campos (associação científica, CNPJ).

### Status no AssApp
✅ Signup simulado + JWT — `POST /api/auth/register/` + `Signup.tsx` (sem Stripe).  
Planos estáticos em `GET /api/auth/plans/`.

---

## Fase ② — Setup da associação (configuração pós-compra)

### Quem age
`association_admin` (owner), já autenticado no painel.

### Quando
Primeiro acesso com `setup_completed = false` (campo/flag a implementar). Bloquear ou redirecionar módulos que dependem de mandato ativo até concluir.

### Etapas sugeridas do wizard

| # | Etapa | Obrigatória | Resultado |
|---|-------|-------------|-----------|
| 1 | Confirmar / completar dados cadastrais | Sim | `Tenant` atualizado (logo, endereço, descrição) |
| 2 | Criar **1º mandato** (ex. Diretoria 2026–2028) | Sim | `Mandato` status `ativo`, `numero_sequencial = 1` |
| 3 | Definir presidente e diretoria | Sim | `CargoMandato` (pelo menos presidente) |
| 4 | Preferências (idioma, canais) | Não | `User.locale`, settings do tenant |
| 5 | Importar associados / pular | Não | `Membro` / `Filiacao` opcional |

### Por que o 1º mandato nasce aqui
Sem mandato ativo, eventos e contextos institucionais ficam sem âncora. O setup fecha o pré-requisito operacional **sem** passar pelo superadmin.

### Distinção de domínio
| Estável (Tenant) | Do mandato (setup etapa 2–3) |
|------------------|------------------------------|
| Nome, CNPJ, logo, endereço | Período, título, cargos, presidente |

### Status no AssApp
✅ `POST /api/auth/setup/` + `AssociationSetup.tsx` + guard `setup_completed`.  
Demo ABCiber: `setup_completed=True` via `init_sistema_tenant.sh`.

### Implementação
- Modelo: `Tenant.setup_completed` (não usa `TransicaoMandato`)
- Wizard FE em `/app/setup` — separado do H2 (`OnboardingWizard.tsx`)

---

## Fase ③ — Operação

Uso normal do painel no mandato ativo:

- Membros e anuidades
- Memória institucional
- Eventos / CFP / pareceres
- Financeiro OSC (`/app/finance`)
- Documentos (`/app/documents`)
- (Futuro) website do tenant

Um tenant tem **vários** mandatos ao longo da vida; apenas **um** com status `ativo` por vez.

---

## Fase ④ — Transição de mandato (H2 — PIPE)

### Quem age
Nova diretoria (`board_member` / `association_admin`).

### Quando
Fim de período ou início explícito de transição (`Mandato.iniciar_transicao`).

### Fluxo já modelado
1. Mandato atual → `transicao`
2. `MandatoSnapshot` do estado consolidado
3. `TransicaoMandato` + `OnboardingEtapa` (wizard adaptativo por `perfil_tecnico`)
4. Conclusão → novo mandato `ativo`, anterior `encerrado` + arquivamento de contextos

### Etapas atuais do wizard H2
`revisar_snapshot` → `confirmar_diretoria` → `revisar_membros` → `revisar_financeiro` → `revisar_eventos` → `revisar_decisoes` → `configurar_comunicacao`

### Status no AssApp
✅ Backend + UI com deep-links para snapshot / membros / finance / eventos / memória (`2026-07-15`). Etapas permanecem checklist (sem KPIs embutidos no card).

---

## Papéis por fase

| Fase | Superadmin | Association admin | Board member |
|------|------------|-------------------|--------------|
| ① Assinatura | Vê tenant nos Assinantes após webhook | Compra / signup | — |
| ② Setup | Não participa | Conduz o wizard | Pode ajudar se já existir User |
| ③ Operação | Suporte / suspensão | Admin do tenant | Gestão do mandato |
| ④ Transição | — | Pode iniciar | Conduz onboarding H2 |

---

## Websites (fora do núcleo deste fluxo, mas relacionados)

| Site | Dono do conteúdo | Fase sugerida |
|------|------------------|---------------|
| Landing do **AssApp** (SaaS) | Superadmin | Manter do WellSaaS; adaptar textos depois |
| Website da **associação** (tenant) | Association admin | Setup opcional ou settings; manter do WellSaaS |

Conteúdo institucional estável → tenant.  
Bloco “diretoria atual” no site público → derivado do `Mandato` ativo / `CargoMandato`.

---

## Mapa “o que já existe × o que falta”

| Capacidade | Status | Onde |
|------------|--------|------|
| Modelos Mandato / Cargo / Transição / Snapshot | ✅ | `backend/mandatos/` |
| Wizard transição H2 | ⚠️ Parcial | `OnboardingWizard.tsx` (+ link financeiro) |
| Signup + Stripe + provisionamento | ⚠️ **Signup simulado** (sem Stripe) | `POST /api/auth/register/`, `Signup.tsx` |
| Flag / wizard de setup pós-compra | ✅ | `Tenant.setup_completed`, `POST /api/auth/setup/`, `AssociationSetup.tsx` |
| Finance OSC | ✅ | `/api/finance/`, `/app/finance` |
| Documents | ✅ | `/api/documents/`, `/app/documents` |
| Adminpanel (planos, assinantes) | ❌ Stub | `backend/adminpanel/` |
| Landing SaaS editável | ❌ | Reutilizar WellSaaS |
| Website CMS do tenant | ❌ | Reutilizar WellSaaS |

> **Implementado em 2026-07-14:** fases ① (signup simulado) e ② (setup com 1º mandato); Finance OSC + Documents. Stripe real e `AdminPlan` permanecem fora de escopo.

---

## Implicações para Sprint futuro

**Já feito (2026-07-14):** fases ①–②; UI WellSaaS; Finance OSC + Documents.

Prioridade natural se o objetivo for “produto SaaS vendável”:

1. Stripe real + AdminPlan + webhooks
2. Aprofundar transição H2 (deep-links membros/eventos; fase ④)
3. Landing AssApp + website do tenant (adaptar do WellSaaS)
4. `adminpanel` (planos editáveis, assinantes)

Se o objetivo imediato for **validação PIPE com ABCiber**, reforçar operação (③) e transição H2 (④).

---

## Documentos relacionados

| Documento | Relação |
|-----------|---------|
| [`STATUS_SPRINTS_FASE1.md`](STATUS_SPRINTS_FASE1.md) | Status dos sprints; pós-Sprint 5 |
| [`AUTH_SIGNUP_SETUP.md`](../modulos/AUTH_SIGNUP_SETUP.md) | Endpoints auth/register/setup |
| [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md) | Padrão visual |
| [`ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Gaps User↔Membro, JWT |
| [`docs/modulos/MANDATOS.md`](../modulos/MANDATOS.md) | Módulo core PIPE |
| [`CHANGELOG_2026_07_14.md`](../changelog/CHANGELOG_2026_07_14.md) | Consolidado do dia |
| [`docs/pesquisa/HIPOTESES_PIPE.md`](../pesquisa/HIPOTESES_PIPE.md) | H1 / H2 / H3 |

---

**Última atualização:** 2026-07-14
