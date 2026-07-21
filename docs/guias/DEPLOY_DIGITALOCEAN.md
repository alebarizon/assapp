# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-07-21  
**Changelog completo:** [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](../changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md)

---

## Staging (no ar)

| Campo | Valor |
|-------|--------|
| URL | http://159.203.183.184:8080/ |
| Health | http://159.203.183.184:8080/health/ |
| Branch CI | `develop` |
| Compose | `docker-compose.staging.yml` |
| Tag imagens | `develop` |

Validado em 2026-07-20 (Actions run `29778780585`).

---

## Droplet

| Campo | Valor |
|-------|--------|
| IP | `159.203.183.184` |
| SSH | `ssh root@159.203.183.184` |
| App | `/opt/assapp` |
| Bootstrap | ✅ `scripts/setup_digitalocean.sh` |

UFW: `22`, `80`, `443`, `8080`.

---

## Pipeline

```
develop → GitHub Actions → Docker Hub → deploy.sh staging → :8080
main    → GitHub Actions → Docker Hub → deploy.sh production → :80
```

| Ambiente | Branch | Porta | Compose |
|----------|--------|-------|---------|
| Staging | `develop` | 8080 | `docker-compose.staging.yml` |
| Produção | `main` | 80 | `docker-compose.prod.yml` |

**Produção ainda não promovida** — branch `main` no GitHub está atrás de `develop`.

---

## Secrets

https://github.com/alebarizon/assapp/settings/secrets/actions → **Repository secrets**

| Secret | Valor |
|--------|--------|
| `DOCKER_USERNAME` | `alebarizon` |
| `DOCKER_PASSWORD` | token Docker Hub |
| `DO_HOST` / `DO_STAGING_HOST` | `159.203.183.184` |
| `DO_USER` | `root` |
| `DO_SSH_KEY` | chave privada SSH |

Checklist: [`.github/CHECKLIST_SECRETS.md`](../../.github/CHECKLIST_SECRETS.md)

---

## Docker Hub

- `alebarizon/assapp-backend` (tags: `develop`, `latest`)
- `alebarizon/assapp-frontend` (tags: `develop`, `latest`)

---

## Checklist

| Passo | Status |
|-------|--------|
| Repo + branches | ✅ |
| OrbStack local | ✅ |
| Droplet + bootstrap | ✅ |
| Secrets | ✅ |
| Hub repos | ✅ |
| Compose + deploy.sh | ✅ |
| Staging no ar | ✅ |
| Produção (`main`) | ❌ |
| Domínio + SSL | ❌ |
| Seed tenant sistema (staging) | ❓ |

---

## Deploy local (dev)

```bash
./scripts/up-orb.sh
```

---

## Ao retomar

1. `git pull` em `orb`
2. Desenvolver → `develop` → validar `:8080`
3. Quando OK: merge `develop` → `main` → validar `:80`
4. Ver seção 9 do changelog de infra para detalhes
