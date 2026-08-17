# Changelog — Deploy, seed e produção comercial (2026-08-17)

> **Commits:** `a56f804` … `5486641` · branches `orb`, `develop`, `main` alinhadas

---

## Resumo do dia

1. **E-commerce + Website CMS** — ver [`CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md`](CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md)
2. **Deploy staging/prod** corrigido e validado no droplet
3. **Seed** `init_sistema_tenant.sh` executado em staging e produção

---

## Infra / CI

| Fix | Detalhe |
|-----|---------|
| Gate produção | Job `verify-staging` — main só deploya após staging OK no mesmo SHA |
| Stacks isolados | `COMPOSE_PROJECT_NAME=assapp_staging` / `assapp_prod` em `deploy.sh` |
| ALLOWED_HOSTS | `gesttora.vertent.com.br` incluído em produção |
| Build TS | `formatCatalogPrice` aceita `PublicCatalogItem` |
| Seed script | `ContentFile` só ASCII (evita SyntaxError no droplet) |

**Migrations:** automáticas no **startup** do backend (compose) — não duplicar no `deploy.sh`.

---

## URLs (droplet `159.203.183.184`)

| Ambiente | Branch | URL |
|----------|--------|-----|
| Staging | `develop` | http://159.203.183.184:8080/ |
| Produção | `main` | http://gesttora.vertent.com.br/ |

Health: `/health/` · Site tenant: `/site?schema=abciber` (após seed website)

---

## Credenciais remotas (após `init_sistema_tenant.sh`)

| Usuário | Senha | Tenant | Papel |
|---------|-------|--------|-------|
| `diretoria@abciber.org.br` | `abciber123` | `abciber` | association_admin |
| `ana.silva@usp.br` | `associado123` | `abciber` | member (portal) |
| `admin@assapp.local` | `admin123` | `sistema` | superadmin |

**Local Mac:** `./scripts/init_sistema_tenant.sh` + opcional `./scripts/init_demo_tenant.sh` (`demo@demo.com` / `demo`).

---

## Pós-deploy obrigatório (cada ambiente, 1ª vez)

```bash
cd /opt/assapp
ASSAPP_BACKEND_CONTAINER=assapp_backend_staging ./scripts/init_sistema_tenant.sh
ASSAPP_BACKEND_CONTAINER=assapp_backend_prod ./scripts/init_sistema_tenant.sh
```

Opcional: `init_demo_tenant.sh` para tenant `demo` + website/anuidades demo.

---

## Fluxo Git (não pular)

```
orb → push develop → validar :8080 → push main → produção aguarda staging (CI)
```

Ver [`docs/guias/GIT_WORKFLOW.md`](../guias/GIT_WORKFLOW.md).

---

## Pendências

- HTTPS (Let's Encrypt) — adiado
- Seed website/ecommerce demo nos VMs (`init_demo_tenant.sh` opcional)
- Stripe / adminpanel
