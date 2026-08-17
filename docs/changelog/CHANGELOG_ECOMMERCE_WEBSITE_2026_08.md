# Changelog — E-commerce + Website CMS Tenant (2026-08-17)

> **Branch:** `orb` → `develop` (staging) → `main` (produção)  
> **Visão:** produto comercial SaaS (além do escopo PIPE Fase 1)

---

## Resumo

Entrega de dois módulos tenant para comercialização:

1. **`ecommerce/`** — catálogo, carrinho, pedidos (anuidades, inscrições, materiais)
2. **`website/`** — site público da associação + CMS (`/site`, `/app/website`)

Integração **Associe-se**: box no site público exibe anuidades do catálogo; CTA `auto:loja` → login → `/app/portal/loja`.

---

## Backend

| App | Migration | API |
|-----|-----------|-----|
| `ecommerce` | `0001_initial` | `/api/ecommerce/catalog/`, `cart/`, `orders/`, `resumo/` |
| `website` | `0001_initial` | `/api/website/config/`, `pages/`, `public/` |
| `tenants` | — | `/api/tenants/public/resolve/?host=` |

- `finance.services` — espelho de pedidos pagos
- `tenants.resolvers` — resolve tenant por `?schema=`, header ou hostname (`Domain`)
- `ecommerce` — vitrine pública `GET /api/ecommerce/public/catalog/?schema=`

---

## Frontend

| Rota | Página |
|------|--------|
| `/site`, `/site/p/:slug` | Site público tenant |
| `/app/website` | CMS (diretoria) |
| `/app/ecommerce/catalog` | Catálogo (diretoria) |
| `/app/ecommerce/orders` | Pedidos (diretoria) |
| `/app/portal/loja` | Loja associado |
| `/app/portal/carrinho` | Carrinho |

Subdomínio dev: `http://demo.localhost:5174/site` (sem `?schema=`).

---

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [`docs/modulos/ECOMMERCE.md`](../modulos/ECOMMERCE.md) | Módulo loja |
| [`docs/modulos/WEBSITE_CMS_TENANT.md`](../modulos/WEBSITE_CMS_TENANT.md) | CMS + site público |
| [`cursor-readme.md`](../../cursor-readme.md) | Referência rápida atualizada |

**Fora do escopo (futuro):** site de evento, publicações, certificados, anais, parcerias.

---

## Deploy remoto (staging + produção)

Ver checklist completo: [`CHANGELOG_2026_08_17_DEPLOY_SEED.md`](CHANGELOG_2026_08_17_DEPLOY_SEED.md).

Após push em `develop` / `main`, o CI builda imagens e roda `deploy.sh`.  
Migrations são aplicadas **automaticamente no startup** do backend (compose).

**Seed obrigatório** (1ª vez em cada ambiente):

```bash
ASSAPP_BACKEND_CONTAINER=assapp_backend_staging ./scripts/init_sistema_tenant.sh
ASSAPP_BACKEND_CONTAINER=assapp_backend_prod ./scripts/init_sistema_tenant.sh
```

Login: `diretoria@abciber.org.br` / `abciber123`

Seed demo (opcional): `init_demo_tenant.sh` — tenant `demo` + website/anuidades.

Validação:

```bash
curl -s "http://159.203.183.184:8080/health/"
curl -s -X POST http://159.203.183.184:8080/api/auth/simple/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"diretoria@abciber.org.br","password":"abciber123"}'
```

---

## Comandos locais

```bash
./scripts/up-orb.sh -d --build
docker compose exec backend python manage.py migrate_schemas
./scripts/init_demo_tenant.sh
# Site: http://localhost:5174/site?schema=demo
# CMS:  http://localhost:5174/app/website
```
