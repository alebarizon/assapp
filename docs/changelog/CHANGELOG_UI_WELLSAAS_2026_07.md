# Changelog — UI alinhada ao WellSaaS

> **Data:** 2026-07-14  
> **Escopo:** shell autenticado + auth + páginas do app no padrão CSS do WellSaaS  
> **Consolidado do dia:** [`CHANGELOG_2026_07_14.md`](CHANGELOG_2026_07_14.md)  
> **Guia permanente:** [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md)

---

## O que mudou

### Fundação
- `frontend/src/styles/Dashboard.css` — copiado/adaptado do WellSaaS (`dashboard-page`, botões, forms, KPIs, loading)
- `frontend/src/components/AppLayout.css` — shell `main-layout` / `sidebar` / `page-content` (paleta warm `#f6f6f3`)
- `frontend/src/pages/Login.css` — login/signup split-screen
- `frontend/src/index.css` — tokens AssApp + extras (`list-card`, `status-badge`, `dashboard-tabs`, etc.)

### Componentes / páginas
- `AppLayout.tsx` — sidebar clara card-like, header sticky, logout padronizado
- `Login.tsx` / `Signup.tsx` — hero + formulário (padrão WellSaaS Login)
- `AssociationSetup`, `Mandatos`, `Memoria`, `Onboarding`, `Membros*`, `Eventos*` — classes semânticas `dashboard-*`

### Fora deste ciclo
- Landing pública AssApp / CMS do tenant
- i18n / LanguageSelector do WellSaaS
