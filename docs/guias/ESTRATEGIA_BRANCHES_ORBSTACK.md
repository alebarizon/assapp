# Estratégia de Branches e Workflow OrbStack (ARM) — AssApp

**Última atualização:** 2026-07-19  
**Contexto:** Desenvolvimento no Mac M-series (Apple Silicon) com OrbStack + deploy DigitalOcean  
**Padrão:** idêntico ao WellSaaS (`docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`)

---

## Sumário

1. [Estratégia de Branches](#1-estratégia-de-branches)
2. [Diferenças ARM vs Intel](#2-diferenças-arm-vs-intel)
3. [Fluxo de Trabalho](#3-fluxo-de-trabalho)
4. [Setup Inicial no Mac](#4-setup-inicial-no-mac)
5. [Comandos do Dia a Dia](#5-comandos-do-dia-a-dia)
6. [Merge orb → develop: o que verificar](#6-merge-orb--develop-o-que-verificar)
7. [Arquivos Relacionados](#7-arquivos-relacionados)

---

## 1. Estratégia de Branches

### Visão geral

```
Mac ARM: [orb]  ──── push/pull ──► origin/develop ──► CI staging (DigitalOcean :8080)
                                        │
[main] (produção) ─────────────────────► origin/main    ──► CI produção (DigitalOcean :80)
```

| Branch local | Remoto | CI disparado | Uso |
|---|---|---|---|
| `orb` | `origin/orb` (backup) ou push para `origin/develop` | nenhum em `orb`; staging se push em `develop` | Desenvolvimento Mac / OrbStack |
| `develop` | `origin/develop` | `deploy-staging.yml` | Staging |
| `main` | `origin/main` | `deploy-production.yml` | **Produção** |

### Por que `orb` separada?

1. Identidade da máquina (Mac ARM / OrbStack).
2. Isolamento de ajustes ARM antes de ir para staging.
3. Backup remoto (`origin/orb`) sem disparar CI.
4. Liberdade para experimentar OrbStack sem afetar `develop`/`main`.

---

## 2. Diferenças ARM vs Intel

| Aspecto | Intel / Linux | Mac M-series / OrbStack |
|---|---|---|
| `postgres:14-alpine` | amd64 nativo | arm64 nativo |
| `node:18-alpine` | amd64 nativo | arm64 nativo |
| `python:3.11-slim` | amd64 nativo | arm64 nativo |
| `assapp-frontend-dev:local` | amd64 | arm64 (rebuild no Mac) |
| `platform:` | desnecessário | em `docker-compose.orb.yml` |
| Socket Docker | `/var/run/docker.sock` | transparente no OrbStack |

**Produção:** builds no GitHub Actions (`ubuntu-latest` = amd64). O servidor DigitalOcean só faz `docker pull`.

---

## 3. Fluxo de Trabalho

### Desenvolvimento diário no Mac

```bash
git checkout orb
./scripts/up-orb.sh

# ... desenvolve, testa, commita ...
git add .
git commit -m "feat: descrição"
git push origin orb   # backup sem CI
```

### Promovendo para staging

```bash
git checkout develop
git pull origin develop
git merge orb
git push origin develop   # dispara deploy-staging.yml
```

Alternativa (direto):

```bash
git push origin orb:develop
```

### Promovendo para produção

```bash
git checkout main
git pull origin main
git merge develop
git push origin main   # dispara deploy-production.yml
```

**Regra:** nunca publicar em `main` sem validar staging em `develop`.

---

## 4. Setup Inicial no Mac

```bash
# 1. Clonar
git clone git@github.com:alebarizon/assapp.git
cd assapp

# 2. Branches
git checkout main            # produção
git checkout -b develop      # staging (se ainda não existir no remoto)
git checkout -b orb          # trabalho diário

# 3. Env
cp .env.example .env

# 4. Subir OrbStack
./scripts/up-orb.sh --build

# 5. Verificar
curl http://localhost:8001/health/
# Frontend: http://localhost:5174
```

---

## 5. Comandos do Dia a Dia

```bash
# Mac / OrbStack
./scripts/up-orb.sh
./scripts/up-orb.sh -d
./scripts/up-orb.sh --build

# Linux / amd64 (sem orb)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Migrations (igual em ambas as plataformas)
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

---

## 6. Merge orb → develop: o que verificar

| Item | Verificação |
|---|---|
| `docker-compose.orb.yml` | Pode ir no repo; CI não usa. OK. |
| `scripts/up-orb.sh` | Conveniência local. OK. |
| `platform: linux/arm64` | Só em `docker-compose.orb.yml`. |
| Dependências | Compatíveis com amd64 (CI). |
| Migrations | Portáveis (SQL). OK. |

---

## 7. Arquivos Relacionados

| Arquivo | Função |
|---|---|
| `docker-compose.yml` | Base |
| `docker-compose.dev.yml` | Hot reload |
| `docker-compose.orb.yml` | Overrides ARM / OrbStack |
| `scripts/up-orb.sh` | Sobe o ambiente no Mac |
| `.github/workflows/deploy-staging.yml` | Push em `develop` |
| `.github/workflows/deploy-production.yml` | Push em `main` |
| `docs/guias/GIT_WORKFLOW.md` | Fluxo Git |
| `docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md` | Promoção orb → develop → main |

---

## Referência Rápida

```
DESENVOLVER  → branch orb     → push origin/orb       (sem CI)
STAGING      → branch develop → push origin/develop   (CI staging)
PRODUÇÃO     → branch main    → push origin/main      (CI produção, build amd64)
```
