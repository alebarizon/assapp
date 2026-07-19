# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-07-19  
**Padrão:** alinhado ao WellSaaS (mesmo droplet pode hospedar staging + produção)

---

## Visão geral

```
Push origin/develop  →  GitHub Actions  →  build amd64  →  Docker Hub  →  DO staging  (:8080)
Push origin/main     →  GitHub Actions  →  build amd64  →  Docker Hub  →  DO produção (:80)
```

| Ambiente | Branch | Porta | Compose (planejado) | Diretório no servidor |
|----------|--------|-------|---------------------|------------------------|
| Staging | `develop` | 8080 | `docker-compose.staging.yml` | `/opt/assapp` |
| Produção | `main` | 80 | `docker-compose.prod.yml` | `/opt/assapp` |

Staging e produção compartilham o diretório; usam arquivos compose/env diferentes.

---

## Secrets do GitHub Actions

Configurar em **Settings → Secrets and variables → Actions**:

| Secret | Uso |
|--------|-----|
| `DOCKER_USERNAME` | Docker Hub |
| `DOCKER_PASSWORD` | Docker Hub |
| `DO_HOST` | IP/host produção |
| `DO_STAGING_HOST` | IP/host staging (pode ser o mesmo) |
| `DO_USER` | Usuário SSH (ex.: `root` ou `deploy`) |
| `DO_SSH_KEY` | Chave privada SSH |
| `G_TOKEN_DEPLOY` | PAT com scope `repo` (clone privado) |

Checklist: [`.github/CHECKLIST_SECRETS.md`](../../.github/CHECKLIST_SECRETS.md)

---

## Imagens Docker Hub

| Serviço | Imagem sugerida |
|---------|-----------------|
| Backend | `${DOCKER_USERNAME}/assapp-backend` |
| Frontend | `${DOCKER_USERNAME}/assapp-frontend` |

Tags:

- Staging: `develop`, `develop-<sha>`
- Produção: `latest`, `main-<sha>`

---

## Regras críticas (lições WellSaaS)

1. **Build só no CI** — no servidor, Dockerfiles de produção podem ser desabilitados (`*.disabled`) para evitar build local.
2. **Concurrency** — `group: deploy-server` nos dois workflows evita race no mesmo droplet.
3. **Push sequencial** — validar staging antes de `git push origin main`.
4. **Migrations** — `migrate_schemas --shared` depois `migrate_schemas` após o deploy.
5. **Never build on droplet** — `COMPOSE_DOCKER_CLI_BUILD=0` no script de deploy.

---

## Estado atual vs próximo passo

### Já preparado neste repositório

- Branches `orb` / `develop` / `main`
- OrbStack local (`docker-compose.orb.yml`, `scripts/up-orb.sh`)
- Workflows GitHub Actions (scaffold)
- `frontend/Dockerfile` (produção) + `nginx.conf`
- Exemplos `env.staging.example` / `env.production.example`

### A completar quando o droplet existir

1. Criar droplet DigitalOcean (Ubuntu 22.04+) e instalar Docker.
2. Configurar secrets no GitHub.
3. Adicionar `docker-compose.staging.yml` e `docker-compose.prod.yml` (pull-only, sem `build:`).
4. Adicionar `scripts/deploy.sh` (padrão WellSaaS).
5. Primeiro deploy via `workflow_dispatch` ou push em `develop`.

Referência completa no WellSaaS: `/Users/ale/Desktop/Wellsaas/docs/guias/BASE_CONHECIMENTO_DEPLOYS.md`

---

## Deploy local (dev)

```bash
./scripts/up-orb.sh          # Mac / OrbStack
# ou
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Não use o compose de produção para desenvolver.
