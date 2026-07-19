# Changelog — Signup simulado + Setup do 1º mandato

> **Data:** 2026-07-14  
> **Escopo:** fases ① e ② de [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md)  
> **Consolidado do dia:** [`CHANGELOG_2026_07_14.md`](CHANGELOG_2026_07_14.md)  
> **Módulo:** [`AUTH_SIGNUP_SETUP.md`](../modulos/AUTH_SIGNUP_SETUP.md)  
> **Fora de escopo:** Stripe real, AdminPlan, landing/CMS

---

## Backend

- `Tenant`: campos `setup_completed`, `plan_slug`, `payment_simulated` (+ migration `0002`)
- `POST /api/auth/register/` — cria Tenant + Domain + schema + `association_admin` (pagamento simulado)
- `GET /api/auth/plans/` — planos estáticos (`starter`, `profissional`)
- `POST /api/auth/setup/` — 1º mandato + cargos + `setup_completed=True`
- `GET /api/auth/tenant-status/` — flags para o guard do frontend
- Login devolve `setup_completed` + `tenant`

## Frontend

- `/signup` — `Signup.tsx`
- `/app/setup` — `AssociationSetup.tsx` (wizard separado do H2)
- Guard: sem setup → força `/app/setup`; após setup → bloqueia `/app/setup`
- Menu reduzido durante setup

## Seed

- `init_sistema_tenant.sh` marca `sistema` e `abciber` com `setup_completed=True`
