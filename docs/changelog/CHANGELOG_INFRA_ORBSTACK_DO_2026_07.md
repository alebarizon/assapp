# Changelog — Infra Git, OrbStack e DigitalOcean

> **Última atualização:** 2026-07-21  
> **Pausa para retomar:** staging validado e no ar. Produção (`main`) ainda não promovida.

---

## Resumo executivo (estado atual)

| Área | Status |
|------|--------|
| Repo GitHub + branches (`orb` / `develop` / `main`) | ✅ |
| OrbStack local (Mac) | ✅ |
| Droplet DO `159.203.183.184` + bootstrap | ✅ |
| Repository secrets GitHub Actions | ✅ |
| Docker Hub `assapp-backend` / `assapp-frontend` | ✅ |
| Compose staging/prod + nginx + `deploy.sh` | ✅ |
| **Staging no ar** (`:8080`) | ✅ validado 2026-07-20 |
| Produção (`main` → `:80`) | ❌ não promovida ainda |
| Domínio + SSL (Certbot) | ❌ |
| Tenant `sistema` / seed no staging | ❓ verificar se necessário |

### URLs staging (funcionando)

| Recurso | URL |
|---------|-----|
| Frontend | http://159.203.183.184:8080/ |
| Health API | http://159.203.183.184:8080/health/ |
| Actions (último deploy OK) | https://github.com/alebarizon/assapp/actions/runs/29778780585 |

---

## 1. Repositório Git

| Item | Valor |
|------|--------|
| Remote | https://github.com/alebarizon/assapp |
| SSH | `git@github.com:alebarizon/assapp.git` |
| Produção (default GitHub) | `main` |
| Staging | `develop` |
| Dev Mac / OrbStack | `orb` |

```
orb → develop (staging :8080) → main (produção :80)
```

### Commits relevantes (infra)

| Commit | Descrição |
|--------|-----------|
| `3262e34` | Init repo + OrbStack + branches |
| `13a47a6` | Produção → branch `main` (padrão WellSaaS) |
| `f96acbf` | Remoção docs PIPE do repositório |
| `275431a` | Docs infra + `setup_digitalocean.sh` |
| `25bc968` | Pausa docs + checklist secrets |
| `e937349` | Fix `vite-env.d.ts` (build CI frontend) |
| `81d99be` | Compose staging/prod + nginx + `deploy.sh` |

### Sincronização de branches (2026-07-21)

| Branch | Commit | Observação |
|--------|--------|------------|
| `orb` | `81d99be` | alinhada com `develop` |
| `develop` | `81d99be` | staging deployado |
| `main` | `275431a` | **atrás** — falta merge de `develop` antes de produção |

---

## 2. Desenvolvimento local (Mac / OrbStack)

```bash
git checkout orb
cp .env.example .env   # se ainda não existir
./scripts/up-orb.sh --build
./scripts/init_sistema_tenant.sh   # tenant sistema (superadmin)
```

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5174 |
| Backend | http://localhost:8001 |
| Health | http://localhost:8001/health/ |

Arquivos: `docker-compose.orb.yml`, `scripts/up-orb.sh` — ver `docs/guias/QUICK_REFERENCE_DOCKER.md`.

---

## 3. Droplet DigitalOcean

| Campo | Valor |
|-------|--------|
| IP | **`159.203.183.184`** |
| Hostname | `drop-assapp` |
| SO | Ubuntu 24.04.4 LTS |
| SSH | `ssh root@159.203.183.184` |
| App dir | `/opt/assapp` |
| Chave Mac | `~/.ssh/id_ed25519` |

### Bootstrap (executado 2026-07-19)

```bash
scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
```

Docker 29.6.2 · UFW: 22, 80, 443, 8080 · swap 2G · usuário `deploy`.

### Containers staging (após deploy)

```
assapp_nginx_staging
assapp_frontend_staging
assapp_backend_staging
assapp_db_staging
```

Verificar: `ssh root@159.203.183.184 'docker ps'`

---

## 4. Pipeline CI/CD

```
Push develop → build amd64 → Hub (tag develop) → SSH → ./scripts/deploy.sh staging → :8080
Push main    → build amd64 → Hub (tag latest)  → SSH → ./scripts/deploy.sh production → :80
```

| Workflow | Arquivo |
|----------|---------|
| Staging | `.github/workflows/deploy-staging.yml` |
| Produção | `.github/workflows/deploy-production.yml` |

- Concurrency `deploy-server` (mesmo droplet)
- `.env.staging` / `.env.production` gerados/atualizados no deploy (senhas auto se placeholder)
- Frontend build: `VITE_API_URL` vazio → API same-origin via nginx (`/api/`)

---

## 5. Docker Hub

| Repositório | Tags usadas |
|-------------|-------------|
| `alebarizon/assapp-backend` | `develop`, `latest` |
| `alebarizon/assapp-frontend` | `develop`, `latest` |

WellSaaS (separado): `alebarizon/wellnz-backend`, `alebarizon/wellnz-frontend`.

---

## 6. Secrets (Repository secrets)

URL: https://github.com/alebarizon/assapp/settings/secrets/actions  

**Usar Repository secrets** — não Environment secrets/variables.

| Secret | Valor |
|--------|--------|
| `DOCKER_USERNAME` | `alebarizon` |
| `DOCKER_PASSWORD` | Access Token Docker Hub (Read & Write) |
| `DO_HOST` | `159.203.183.184` |
| `DO_STAGING_HOST` | `159.203.183.184` |
| `DO_USER` | `root` (ou `deploy`) |
| `DO_SSH_KEY` | chave privada SSH (`~/.ssh/id_ed25519`) |
| `G_TOKEN_DEPLOY` | opcional (repo público) |

**Não confundir:** token `ghp_…` = GitHub PAT (`G_TOKEN_DEPLOY`), **não** `DOCKER_PASSWORD`.

Checklist: `.github/CHECKLIST_SECRETS.md`

---

## 7. Arquivos de deploy (criados 2026-07-20)

| Arquivo | Função |
|---------|--------|
| `docker-compose.staging.yml` | Stack staging (pull-only) |
| `docker-compose.prod.yml` | Stack produção (pull-only) |
| `nginx/nginx_assapp_staging.conf` | Proxy :8080 |
| `nginx/nginx_assapp_prod.conf` | Proxy :80 |
| `scripts/deploy.sh` | Pull + up + health check |
| `scripts/setup_digitalocean.sh` | Bootstrap droplet |
| `env.staging.example` / `env.production.example` | Templates |

---

## 8. Problemas resolvidos nesta fase

| Problema | Solução |
|----------|---------|
| SSH droplet | Chave `mac-ale` em `authorized_keys` |
| Docker Hub 401 insufficient scopes | Token com Read & Write |
| `npm run build` falha no CI | `frontend/src/vite-env.d.ts` |
| Secrets em Environment errado | Mover para **Repository secrets** |
| Deploy sem containers | Compose + `deploy.sh` + nginx |

---

## 9. Ao retomar o projeto

### Imediato (operacional)

1. `git checkout orb && git pull origin orb`
2. Desenvolver em `orb` → merge/push em `develop` para atualizar staging
3. Validar http://159.203.183.184:8080/ após cada deploy
4. Rodar `./scripts/init_sistema_tenant.sh` no staging se login superadmin não existir:
   ```bash
   ssh root@159.203.183.184
   cd /opt/assapp
   docker compose -f docker-compose.staging.yml exec backend python manage.py shell
   # ou copiar/adaptar init_sistema_tenant.sh para exec no container
   ```

### Promover produção (quando staging OK)

```bash
git checkout main
git pull origin main
git merge develop
git push origin main
# Aguardar Actions → validar http://159.203.183.184/
```

### Produto / PIPE (Fase 1)

Retomar sprints conforme `docs/referencia/STATUS_SPRINTS_FASE1.md` — mandatos (H1+H2), memoria, eventos, membros, etc.

### Infra futura

- Domínio DNS → `ALLOWED_HOSTS` + Certbot
- Stripe real (último, conforme docs)
- `G_TOKEN_DEPLOY` se repo ficar privado

Referência WellSaaS: `/Users/ale/Desktop/Wellsaas/docs/guias/BASE_CONHECIMENTO_DEPLOYS.md`

---

## 10. Referência rápida

```bash
# Mac — dev
./scripts/up-orb.sh

# Droplet — status
ssh root@159.203.183.184 'docker ps; curl -s http://127.0.0.1:8080/health/'

# Promover código
git checkout develop && git merge orb && git push origin develop

# Actions
open https://github.com/alebarizon/assapp/actions
```
