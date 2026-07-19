# Auth — Signup, Setup e sessão

> **Status:** implementado (2026-07-14) — signup **simulado** (sem Stripe)  
> **Fluxo de domínio:** [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md)

---

## Endpoints

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/api/auth/simple/login/` | público | Login multi-schema; retorna JWT + `setup_completed` + `tenant` |
| POST | `/api/auth/register/` | público | Cria Tenant + schema + `association_admin`; JWT; `setup_completed=false` |
| GET | `/api/auth/plans/` | público | Planos estáticos (`starter`, `profissional`) |
| POST | `/api/auth/setup/` | JWT | 1º mandato + cargos; marca `setup_completed=true` |
| GET | `/api/auth/tenant-status/` | JWT | Flags e dados leves do Tenant |
| GET/PATCH | `/api/auth/me/` | JWT | Usuário atual |

---

## Modelo `Tenant` (campos novos)

| Campo | Tipo | Uso |
|-------|------|-----|
| `setup_completed` | bool | Guard do frontend pós-login |
| `plan_slug` | str | Plano escolhido no signup |
| `payment_simulated` | bool | `true` neste ciclo (sem Stripe) |

---

## Frontend

| Rota | Página | Quando |
|------|--------|--------|
| `/login` | `Login.tsx` | Entrada |
| `/signup` | `Signup.tsx` | Nova associação |
| `/app/setup` | `AssociationSetup.tsx` | Após register ou login com setup incompleto |

Serviço: `frontend/src/services/auth.ts`.

**Dois wizards:**
- Setup pós-compra → `AssociationSetup` (fase ②)
- Transição de mandato (H2) → `OnboardingWizard` (fase ④)

---

## Seed demo

`scripts/init_sistema_tenant.sh` marca `sistema` e `abciber` com `setup_completed=True` (já têm mandato).

---

## Pendente

- Stripe checkout / webhook / `AdminPlan`
- `adminpanel` (planos editáveis, assinantes)
- Landing pública AssApp
