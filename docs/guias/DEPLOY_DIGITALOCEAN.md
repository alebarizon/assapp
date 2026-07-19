# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-07-19  
**Padrão:** alinhado ao WellSaaS (mesmo droplet pode hospedar staging + produção)  
**Changelog do dia:** [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](../changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md)

---

## Droplet atual

| Campo | Valor |
|-------|--------|
| IP | `159.203.183.184` |
| Hostname | `drop-assapp` |
| SO | Ubuntu 24.04 LTS |
| SSH | `ssh root@159.203.183.184` |
| App | `/opt/assapp` |
| Bootstrap | **concluído** (`scripts/setup_digitalocean.sh`) |

Portas abertas (UFW): `22`, `80`, `443`, `8080`.

---

## Visão geral do pipeline

```
Push origin/develop  →  GitHub Actions  →  build amd64  →  Docker Hub  →  DO staging  (:8080)
Push origin/main     →  GitHub Actions  →  build amd64  →  Docker Hub  →  DO produção (:80)
```

| Ambiente | Branch | Porta | Compose (a criar) | Diretório |
|----------|--------|-------|-------------------|-----------|
| Staging | `develop` | 8080 | `docker-compose.staging.yml` | `/opt/assapp` |
| Produção | `main` | 80 | `docker-compose.prod.yml` | `/opt/assapp` |

---

## Bootstrap do servidor

### Já executado (2026-07-19)

```bash
scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
```

Instala: Docker, Compose plugin, UFW, fail2ban, swap 2G, usuário `deploy`, `/opt/assapp`, Certbot.

### Reexecutar (idempotente na maior parte)

Mesmos comandos acima. O script pula Docker/swap se já existirem.

### User data (cloud-init) — droplets futuros

Na criação do Droplet: **Additional Options → Startup scripts**.  
Ver: https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/  

Equivale ao `setup_digitalocean.sh` no primeiro boot. Neste droplet o bootstrap foi manual.

---

## Secrets do GitHub Actions

Página: https://github.com/alebarizon/assapp/settings/secrets/actions  

| Secret | Valor neste projeto |
|--------|---------------------|
| `DO_HOST` | `159.203.183.184` |
| `DO_STAGING_HOST` | `159.203.183.184` |
| `DO_USER` | `root` ou `deploy` |
| `DO_SSH_KEY` | chave privada (`cat ~/.ssh/id_ed25519`) |
| `DOCKER_USERNAME` | Docker Hub |
| `DOCKER_PASSWORD` | token Docker Hub |
| `G_TOKEN_DEPLOY` | opcional (repo público) |

Checklist: [`.github/CHECKLIST_SECRETS.md`](../../.github/CHECKLIST_SECRETS.md)

**Status:** aguardando cadastro pelo usuário.

---

## Imagens Docker Hub

| Projeto | Imagens |
|---------|---------|
| WellSaaS (já existem) | `alebarizon/wellnz-backend` · `alebarizon/wellnz-frontend` |
| AssApp (criar) | `alebarizon/assapp-backend` · `alebarizon/assapp-frontend` |

Tags AssApp: staging `develop` · produção `latest` / `main-<sha>`

`DOCKER_USERNAME` = `alebarizon`. `DOCKER_PASSWORD` = token do **Docker Hub**, não PAT GitHub (`ghp_`).

---

## Regras críticas (lições WellSaaS)

1. Build só no CI — servidor só faz `docker pull`.
2. Concurrency `deploy-server` nos dois workflows.
3. Push sequencial: staging OK → só então `main`.
4. Migrations: `migrate_schemas --shared` depois `migrate_schemas`.
5. `COMPOSE_DOCKER_CLI_BUILD=0` no deploy.

---

## Checklist de progresso

| Passo | Status |
|-------|--------|
| Repo Git + branches `orb` / `develop` / `main` | ✅ |
| OrbStack local (`up-orb.sh`) | ✅ |
| Workflows Actions (scaffold) | ✅ |
| Droplet criado + SSH | ✅ |
| Bootstrap Docker / UFW / `/opt/assapp` | ✅ |
| Docs / changelog de pausa | ✅ |
| Secrets no GitHub | ⏳ em configuração |
| Repos Hub `assapp-backend` / `assapp-frontend` | ⏳ criar (separados de `wellnz-*`) |
| `docker-compose.staging.yml` / `prod.yml` | ❌ |
| `scripts/deploy.sh` | ❌ |
| `.env.*` no servidor | ❌ |
| Primeiro deploy staging | ❌ |
| Domínio + SSL | ❌ |

---

## Deploy local (dev)

```bash
./scripts/up-orb.sh
```

Não use compose de produção para desenvolver.
