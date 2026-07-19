# Changelog — Infra Git, OrbStack e DigitalOcean (2026-07-19)

> **Pausa documentada:** 2026-07-19 (fim da manhã).  
> Registro completo do que foi feito. Retomar a partir da seção 9 (pendências).

---

## Resumo executivo

| Área | Status |
|------|--------|
| Repo GitHub + branches (`orb` / `develop` / `main`) | ✅ |
| OrbStack local (Mac) | ✅ |
| Droplet DO `159.203.183.184` + bootstrap | ✅ |
| Workflows Actions (scaffold) | ✅ |
| Documentação operacional | ✅ |
| Secrets GitHub Actions | ⏳ em configuração pelo usuário |
| Repos Docker Hub AssApp | ⏳ criar `assapp-backend` / `assapp-frontend` |
| Compose prod/staging + `deploy.sh` | ❌ próximo bloco de código |
| Primeiro deploy no ar | ❌ |

---

## 1. Repositório Git

| Item | Valor |
|------|--------|
| Remote | https://github.com/alebarizon/assapp |
| SSH | `git@github.com:alebarizon/assapp.git` |
| Produção (default) | `main` — igual WellSaaS |
| Staging | `develop` |
| Dev Mac / OrbStack | `orb` |

```
orb → develop (staging :8080) → main (produção :80)
```

### Commits relevantes

| Commit | Descrição |
|--------|-----------|
| `3262e34` | Init repo + OrbStack + branches |
| `13a47a6` | Produção renomeada para `main` (padrão WellSaaS) |
| `f96acbf` | Remoção de 43 arquivos PIPE que não deveriam versionar |
| `275431a` | Docs infra + `setup_digitalocean.sh` |

### Removidos do Git (não recolocar)

Propostas PIPE (`.md`), HTMLs de levantamento, pasta `v2/`, `funcoes.md`, etc.

---

## 2. OrbStack / desenvolvimento local (Mac)

| Arquivo | Função |
|---------|--------|
| `docker-compose.orb.yml` | Overrides ARM64 |
| `scripts/up-orb.sh` | Sobe base + dev + orb |
| `frontend/Dockerfile` + `nginx.conf` | Imagem de produção |
| `frontend/Dockerfile.dev` | Hot reload local |

```bash
./scripts/up-orb.sh --build
# http://localhost:5174 · http://localhost:8001
```

---

## 3. Droplet DigitalOcean

| Campo | Valor |
|-------|--------|
| IP | **`159.203.183.184`** |
| Hostname | `drop-assapp` |
| SO | Ubuntu 24.04.4 LTS |
| SSH | `ssh root@159.203.183.184` |
| Chave Mac | `~/.ssh/id_ed25519` (`mac-ale`) |

### Bootstrap (já executado)

```bash
scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
```

| Componente | Estado |
|------------|--------|
| Docker | 29.6.2 |
| Compose plugin | v5.3.1 |
| UFW | 22, 80, 443, **8080** |
| fail2ban / swap 2G / certbot | ok |
| Usuário `deploy` | criado (`docker` + sudo) |
| `/opt/assapp` | `deploy:deploy` |

**User data / cloud-init:** útil em droplets *novos* (Startup scripts). Neste servidor o equivalente foi o script manual.  
Ref: https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/

---

## 4. GitHub Actions

| Workflow | Branch | Arquivo |
|----------|--------|---------|
| Staging | `develop` | `.github/workflows/deploy-staging.yml` |
| Produção | `main` | `.github/workflows/deploy-production.yml` |

- Concurrency `deploy-server` (mesmo droplet)
- Build → Docker Hub → SSH em `/opt/assapp` (se secrets DO existirem)
- Push em `orb` **não** dispara deploy

URL secrets: https://github.com/alebarizon/assapp/settings/secrets/actions

---

## 5. Docker Hub

### Já existentes (WellSaaS — não misturar)

- `alebarizon/wellnz-backend`
- `alebarizon/wellnz-frontend`

### Criar para AssApp (combinado na pausa)

- `alebarizon/assapp-backend`
- `alebarizon/assapp-frontend`

Visibility: Private recomendado. O CI faz o primeiro `push` de tags (`develop` / `latest`).

### Credenciais nos Secrets

| Secret | Valor |
|--------|--------|
| `DOCKER_USERNAME` | `alebarizon` |
| `DOCKER_PASSWORD` | **Access Token do Docker Hub** (hub.docker.com → Personal access tokens), *não* senha GitHub |

**Atenção:** token `ghp_…` (GitHub PAT, ex. nota `wellsaas-deploy-token`) é para `G_TOKEN_DEPLOY`, **não** para `DOCKER_PASSWORD`.  
Se um `ghp_` foi exposto em chat/notas, **revogar e regenerar** em https://github.com/settings/tokens.

`G_TOKEN_DEPLOY` é **opcional** enquanto o AssApp for público.

---

## 6. Secrets — checklist na pausa

| Secret | Valor / como obter | Status típico |
|--------|--------------------|---------------|
| `DO_HOST` | `159.203.183.184` | ⏳ usuário |
| `DO_STAGING_HOST` | `159.203.183.184` | ⏳ usuário |
| `DO_USER` | `root` ou `deploy` | ⏳ usuário |
| `DO_SSH_KEY` | `cat ~/.ssh/id_ed25519` (privada) | ⏳ usuário |
| `DOCKER_USERNAME` | `alebarizon` | ⏳ usuário |
| `DOCKER_PASSWORD` | token Docker Hub | ⏳ usuário |
| `G_TOKEN_DEPLOY` | PAT GitHub `repo` | opcional |

Detalhe: `.github/CHECKLIST_SECRETS.md`

---

## 7. Documentação deste dia

| Documento | Conteúdo |
|-----------|----------|
| Este arquivo | Registro mestre / pausa |
| `docs/guias/DEPLOY_DIGITALOCEAN.md` | Droplet + pipeline |
| `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md` | Branches + OrbStack |
| `docs/guias/GIT_WORKFLOW.md` | Push sequencial |
| `docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md` | orb → develop → main |
| `docs/guias/AMBIENTE_DESENVOLVIMENTO_MAC_OS_ARM.md` | Setup Mac |
| `docs/guias/QUICK_REFERENCE_DOCKER.md` | Comandos Docker |
| `.github/CHECKLIST_SECRETS.md` | Secrets |
| `scripts/setup_digitalocean.sh` | Bootstrap servidor |
| `scripts/up-orb.sh` | Dev Mac |

---

## 8. SSH rápido

```bash
ssh root@159.203.183.184
docker --version && docker compose version
ufw status
ls -ld /opt/assapp
```

---

## 9. Ao retomar (próximos passos)

1. Terminar secrets em https://github.com/alebarizon/assapp/settings/secrets/actions  
2. Criar repos Docker Hub `assapp-backend` e `assapp-frontend` (se ainda não criados)  
3. No código: `docker-compose.staging.yml` + `docker-compose.prod.yml` (pull-only) + `scripts/deploy.sh`  
4. `.env.staging` / `.env.production` **só no servidor**  
5. Primeiro deploy: `develop` → validar `:8080` → depois `main`  
6. Domínio + Certbot quando houver DNS  

Referência WellSaaS: `/Users/ale/Desktop/Wellsaas/docs/guias/BASE_CONHECIMENTO_DEPLOYS.md`
