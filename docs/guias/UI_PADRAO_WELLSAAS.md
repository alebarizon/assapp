# Guia — UI no padrão WellSaaS

> **Status:** vigente desde 2026-07-14  
> **Objetivo:** manter o frontend AssApp visualmente alinhado ao dashboard WellSaaS (CSS semântico).

---

## Princípio

Não espalhar longas strings Tailwind no JSX para layout de página. Usar classes semânticas:

| Camada | Arquivo | Papel |
|--------|---------|-------|
| Global + extras AssApp | `frontend/src/index.css` | tokens, `list-card`, `status-badge`, tabs |
| Páginas autenticadas | `frontend/src/styles/Dashboard.css` | `dashboard-*`, forms, botões, KPIs |
| Shell | `frontend/src/components/AppLayout.css` | sidebar, header, `page-content` |
| Auth | `frontend/src/pages/Login.css` | Login + Signup split-screen |

Tailwind permanece no projeto para utilitários pontuais; o **esqueleto da UI** é CSS do WellSaaS.

---

## Template de página

```html
<div class="dashboard-page">
  <div class="dashboard-header dashboard-header-row">
    <div>
      <h1 class="dashboard-title">…</h1>
      <p class="dashboard-subtitle">…</p>
    </div>
    <div class="dashboard-header-actions">
      <button class="dashboard-btn-new">+ Novo</button>
    </div>
  </div>

  <div class="dashboard-content-panel">
    <!-- conteúdo / list-stack / tabela -->
  </div>
</div>
```

Loading:

```html
<div class="dashboard-page">
  <div class="dashboard-loading">
    <div class="loading-spinner"></div>
    <p>Carregando…</p>
  </div>
</div>
```

Formulário:

```html
<div class="page-form-container">
  <form class="page-form">
    <div class="form-group">
      <label class="form-label">…</label>
      <input class="form-input" />
    </div>
    <div class="form-actions">
      <button type="button" class="dashboard-btn-cancel">Cancelar</button>
      <button type="submit" class="dashboard-btn-save">Salvar</button>
    </div>
  </form>
</div>
```

---

## Paleta (shell)

| Token | Hex | Uso |
|-------|-----|-----|
| Fundo app | `#f6f6f3` | `.main-layout` |
| Surface | `#ffffff` | sidebar, cards, header |
| Texto | `#131313` | títulos |
| Muted | `#666666` | subtítulos |
| Borda | `#ecebe6` | cards / sidebar |
| Nav ativa | `#efe9dc` | `.nav-link.active` |
| Accent | `#9a6a0b` / `#c79b45` | ícones / spinner |
| CTA verde | `#48bb78` | `.dashboard-btn-new` / save |

---

## Auth

Login e Signup usam o mesmo `Login.css`:

- `login-page` → `login-hero` (desktop ≥1024px) + `login-form-panel`
- Hero AssApp: `.login-hero-fallback` (gradiente; sem imagem de marketing ainda)
- Inputs: `.login-input` / submit: `.login-submit-button` (`#131313`)

---

## Shell (`AppLayout`)

Estrutura espelhada do WellSaaS `MainLayout`:

```
main-layout
  sidebar (+ sidebar-open no mobile)
    sidebar-header / sidebar-nav / sidebar-footer
  main-content
    main-header (menu-toggle)
    page-content → <Outlet />
```

Durante setup incompleto, o menu mostra só “Setup da associação”.

---

## Extras AssApp (`index.css`)

| Classe | Uso |
|--------|-----|
| `list-stack` / `list-card` | listas de mandatos, eventos, etc. |
| `status-badge` / `status-badge-{status}` | chips de status |
| `highlight-banner` | mandato ativo, tips |
| `alert-banner-*` | info / erro / sucesso |
| `dashboard-tabs` / `dashboard-tab` | abas Memória |
| `setup-steps` / `setup-step` | wizard AssociationSetup |

---

## Changelog

[`CHANGELOG_UI_WELLSAAS_2026_07.md`](../changelog/CHANGELOG_UI_WELLSAAS_2026_07.md)
