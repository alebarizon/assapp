# Checklist — Secrets GitHub Actions (AssApp)

**URL:** https://github.com/alebarizon/assapp/settings/secrets/actions  
**Changelog / pausa:** `docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`  
**Droplet:** `159.203.183.184` (bootstrap ✅)

---

## Não confundir tokens

| Tipo | Prefixo / origem | Secret AssApp |
|------|------------------|---------------|
| Docker Hub Access Token | hub.docker.com → Personal access tokens | `DOCKER_PASSWORD` |
| GitHub PAT | `ghp_…` (settings/tokens) | `G_TOKEN_DEPLOY` (opcional) |
| SSH privada | `~/.ssh/id_ed25519` | `DO_SSH_KEY` |

WellSaaS já usa imagens `alebarizon/wellnz-*`. AssApp usa **`alebarizon/assapp-backend`** e **`alebarizon/assapp-frontend`** (criar no Hub se ainda não existirem).

---

## Obrigatórios — build

- [ ] `DOCKER_USERNAME` → `alebarizon`
- [ ] `DOCKER_PASSWORD` → Access Token Docker Hub (Read & Write)

## Obrigatórios — droplet

- [ ] `DO_HOST` → `159.203.183.184`
- [ ] `DO_STAGING_HOST` → `159.203.183.184`
- [ ] `DO_USER` → `root` ou `deploy`
- [ ] `DO_SSH_KEY` → `cat ~/.ssh/id_ed25519` (BEGIN…END)

## Opcional

- [ ] `G_TOKEN_DEPLOY` — só se o repo for privado; AssApp público → pode omitir

---

## Branches → deploy

| Branch | Workflow | Porta |
|--------|----------|-------|
| `develop` | staging | 8080 |
| `main` | produção | 80 |
| `orb` | nenhum | — |

---

## Depois dos secrets (ainda falta código)

1. `docker-compose.staging.yml` / `docker-compose.prod.yml` + `scripts/deploy.sh`
2. Actions → Run workflow (staging)
3. Validar health em `:8080` antes de promover `main`
