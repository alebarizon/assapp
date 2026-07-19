# Changelog — Infra Git, OrbStack e DigitalOcean (2026-07-19)

> Registro completo da configuração criada neste dia.  
> Secrets do GitHub Actions: **pendentes** (usuário retorna em seguida).

---

## 1. Repositório Git

| Item | Valor |
|------|--------|
| Remote | https://github.com/alebarizon/assapp |
| SSH | `git@github.com:alebarizon/assapp.git` |
| Default / produção | `main` (igual WellSaaS) |
| Staging | `develop` |
| Dev Mac / OrbStack | `orb` |

### Fluxo (padronizado com WellSaaS)

```
orb → develop (staging :8080) → main (produção :80)
```

### Histórico relevante de commits

| Commit | Descrição |
|--------|-----------|
| `3262e34` | Inicialização do repo + OrbStack + estratégia de branches |
| `13a47a6` | Padronização: produção `assapp` → `main` |
| `f96acbf` | Remoção de 43 arquivos de pesquisa PIPE que não deveriam versionar |

### Removidos do Git (não devem voltar)

- Markdowns de proposta PIPE (`0-submissao.md`, `1-objetivo-*.md`, …)
- HTMLs de levantamento (`comparativo_ams_*.html`, …)
- Pasta `v2/` e `funcoes.md`, `prompts_*.md`, etc.

---

## 2. OrbStack / desenvolvimento local (Mac)

| Arquivo | Função |
|---------|--------|
| `docker-compose.orb.yml` | Overrides `platform` ARM64 |
| `scripts/up-orb.sh` | Sobe stack: base + dev + orb |
| `frontend/Dockerfile.dev` | Imagem `assapp-frontend-dev:local` |
| `frontend/Dockerfile` | Build produção (Vite → Nginx) |
| `frontend/nginx.conf` | SPA + assets |

```bash
./scripts/up-orb.sh --build
# Frontend http://localhost:5174 · Backend http://localhost:8001
```

Docs: `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`, `AMBIENTE_DESENVOLVIMENTO_MAC_OS_ARM.md`, `QUICK_REFERENCE_DOCKER.md`

---

## 3. Droplet DigitalOcean

| Campo | Valor |
|-------|--------|
| Nome | `assapp` (hostname `drop-assapp`) |
| IP | **`159.203.183.184`** |
| SO | Ubuntu 24.04.4 LTS |
| Acesso SSH | `ssh root@159.203.183.184` |
| Chave Mac usada | `~/.ssh/id_ed25519` (`mac-ale`) |

### Bootstrap executado em 2026-07-19

Script: `scripts/setup_digitalocean.sh` (adaptado do WellSaaS).

Comando usado:

```bash
scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
```

### Estado pós-bootstrap

| Componente | Status |
|------------|--------|
| Docker | 29.6.2 |
| Docker Compose plugin | v5.3.1 |
| UFW | ativo — 22, 80, 443, **8080** |
| fail2ban | ativo |
| Swap | 2 GB (`/swapfile`) |
| Certbot | instalado (SSL quando houver domínio) |
| Usuário `deploy` | criado (grupo `docker` + sudo; mesma authorized_keys do root) |
| App dir | `/opt/assapp` (`deploy:deploy`) |

### User data (cloud-init)

Documentação DO: https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/

**Relevância:** automatiza o bootstrap no *primeiro* boot. Como o droplet já existia, usamos o script manual (equivalente). Para droplets futuros, o mesmo conteúdo de `setup_digitalocean.sh` pode ir em **Startup scripts**.

---

## 4. GitHub Actions (workflows)

| Workflow | Branch | Arquivo |
|----------|--------|---------|
| Deploy Staging | `develop` | `.github/workflows/deploy-staging.yml` |
| Deploy Production | `main` | `.github/workflows/deploy-production.yml` |

- Concurrency `group: deploy-server` (evita race no mesmo droplet)
- Build amd64 → Docker Hub (`assapp-backend` / `assapp-frontend`)
- SSH deploy para `/opt/assapp` **quando secrets existirem**
- Sem secrets de DO: build ainda roda; deploy SSH é pulado

Checklist: `.github/CHECKLIST_SECRETS.md`

---

## 5. Secrets — o que configurar (pendente)

URL: https://github.com/alebarizon/assapp/settings/secrets/actions  

**New repository secret** (não Environment):

| Name | Valor sugerido | Observação |
|------|----------------|------------|
| `DO_HOST` | `159.203.183.184` | Produção |
| `DO_STAGING_HOST` | `159.203.183.184` | Mesmo droplet |
| `DO_USER` | `root` ou `deploy` | Preferir `deploy` após validar SSH |
| `DO_SSH_KEY` | Conteúdo de `~/.ssh/id_ed25519` | Privada, com BEGIN/END |
| `DOCKER_USERNAME` | usuário Docker Hub | Obrigatório para build |
| `DOCKER_PASSWORD` | token Docker Hub | Obrigatório para build |
| `G_TOKEN_DEPLOY` | PAT `repo` | Opcional enquanto o repo for público |

```bash
# Copiar chave privada para colar no secret (não commitar!)
cat ~/.ssh/id_ed25519
```

---

## 6. Documentação criada / atualizada neste dia

| Documento | Conteúdo |
|-----------|----------|
| `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md` | Branches + OrbStack |
| `docs/guias/GIT_WORKFLOW.md` | Push sequencial |
| `docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md` | orb → develop → main |
| `docs/guias/DEPLOY_DIGITALOCEAN.md` | Deploy DO + estado do droplet |
| `docs/guias/AMBIENTE_DESENVOLVIMENTO_MAC_OS_ARM.md` | Setup Mac |
| `docs/guias/QUICK_REFERENCE_DOCKER.md` | Comandos rápidos |
| `.github/CHECKLIST_SECRETS.md` | Lista de secrets |
| `.cursorrules` / `cursor-readme.md` / `README.md` | Branches + OrbStack |

---

## 7. Ainda não feito (próximos passos)

1. **Usuário:** cadastrar secrets na URL acima.
2. **Código:** `docker-compose.staging.yml` + `docker-compose.prod.yml` (pull-only, sem `build:`).
3. **Código:** `scripts/deploy.sh` (padrão WellSaaS).
4. Clone em `/opt/assapp` (Actions ou manual).
5. `.env.staging` / `.env.production` **só no servidor**.
6. Primeiro deploy: push/`workflow_dispatch` em `develop` → validar `:8080` → promover `main`.
7. Domínio + Certbot quando existir DNS.

Referência WellSaaS: `/Users/ale/Desktop/Wellsaas/docs/guias/BASE_CONHECIMENTO_DEPLOYS.md`

---

## 8. Referência rápida SSH

```bash
ssh root@159.203.183.184
# ou
ssh deploy@159.203.183.184

docker --version
docker compose version
ufw status
ls -ld /opt/assapp
```
