# Website CMS do Tenant — Gesttora

> **Status:** implementado (MVP comercial)  
> **Última revisão:** 2026-08-17

---

## Visão comercial

Cada associação (tenant) tem um **site institucional público** editável pela diretoria, separado da landing SaaS Gesttora (`/`).

**Escopo atual (MVP):**

- Identidade visual (cores, título, tagline)
- Hero + seção institucional
- Notícias e páginas institucionais (CRUD)
- Box **Associe-se** (categorias de filiação + CTA) — referência de UX apenas do box, não do site ABCiber inteiro
- Contato
- Diretoria atual (dados do mandato ativo em `mandatos`)

**Fora do escopo agora** (produtos/módulos futuros):

- Site de evento (vitrine H3 permanece em `/app/eventos`)
- Publicações, certificados, anais, parcerias
- Domínio customizado / subdomínio automático (fase infra)

---

## URLs

| Contexto | URL | Quem acessa |
|----------|-----|-------------|
| Landing SaaS | `/` | Público — produto Gesttora |
| Site do tenant | `/site?schema={tenant}` | Público |
| Página do site | `/site/p/{slug}?schema={tenant}` | Público |
| Painel CMS | `/app/website` | `association_admin` / diretoria |

Demo local: `http://localhost:5174/site?schema=demo`

---

## Backend (`website` — TENANT_APP)

### Modelos

- **`WebsiteConfig`** — singleton por schema (hero, about, box Associe-se, contato, `is_published`)
- **`SitePage`** — notícias (`noticia`) e páginas institucionais (`institucional`)

### API

| Endpoint | Auth | Descrição |
|----------|------|-----------|
| `GET/PATCH /api/website/config/` | Board/Admin | Config singleton |
| CRUD `/api/website/pages/` | Board/Admin | Páginas e notícias |
| `GET /api/website/public/?schema=` | AllowAny | Payload da home |
| `GET /api/website/public/pages/{slug}/?schema=` | AllowAny | Página publicada |
| `GET /api/website/public/diretoria/?schema=` | AllowAny | Mandato ativo |

### Seed demo

```bash
./scripts/init_demo_tenant.sh
# ou dentro do container:
docker compose exec backend python manage.py shell -c "
from django_tenants.utils import schema_context
with schema_context('demo'):
    from website.services import seed_default_config, seed_default_pages
    seed_default_config(site_title='Associação Demo', publish=True)
    seed_default_pages()
"
```

---

## Frontend

| Arquivo | Função |
|---------|--------|
| `pages/TenantSiteHome.tsx` | Home pública `/site` |
| `pages/TenantSitePage.tsx` | Detalhe `/site/p/:slug` |
| `pages/WebsiteAdmin.tsx` | Painel `/app/website` |
| `components/tenant-site/*` | Layout + CSS + box Associe-se |
| `services/website.ts` | Cliente API |

Rotas públicas ficam **fora** de `PrivateRoute` em `App.tsx`.

---

## Box Associe-se

Campos em `WebsiteConfig`:

- `associe_se_title`, `associe_se_lead`
- `associe_se_categories` — JSON `[{label, hint}, …]` (fallback se não houver itens no catálogo)
- `associe_se_cta_label`, `associe_se_cta_link` — use `auto:loja` (padrão) para login → `/app/portal/loja`

Itens de anuidade ativos no catálogo `ecommerce` aparecem automaticamente no box com preços.

### Domínio / subdomínio

| Ambiente | Exemplo | Resolução |
|----------|---------|-----------|
| Dev | `demo.localhost:5174/site` | slug antes de `.localhost` |
| Staging/prod | `abciber.gesttora.vertent.com.br` | tabela `tenants.Domain` |
| Custom | `www.abciber.org.br` | registro em `Domain` (is_primary) |

API: `GET /api/tenants/public/resolve/?host=demo.localhost`

Integração futura: CTA customizado para URL externa ou fluxo de cadastro de associado.

---

## Integrações existentes

| Dado | Origem |
|------|--------|
| Diretoria | `mandatos.Mandato.get_ativo()` |
| Loja / anuidades | `ecommerce` (portal associado) |
| Memória institucional | Conteúdo editável no CMS; link profundo com `memoria` futuro |

---

## Comandos

```bash
docker compose exec backend python manage.py migrate_schemas
./scripts/up-orb.sh -d --build   # rebuild frontend se necessário
```
