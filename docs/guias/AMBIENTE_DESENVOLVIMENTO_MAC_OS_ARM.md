# Ambiente de Desenvolvimento — Mac OS (ARM / OrbStack) — AssApp

**Última atualização:** 2026-07-19  
**Branch de trabalho:** `orb`  
**Produção:** branch `assapp`

---

## Pré-requisitos

- OrbStack instalado e rodando ([orbstack.dev](https://orbstack.dev))
- Git com acesso ao repositório
- Docker CLI (fornecido pelo OrbStack)

---

## Setup rápido

```bash
git clone <url-do-repo>.git
cd assapp

git checkout assapp
git checkout -b develop   # se ainda não existir
git checkout -b orb

cp .env.example .env
./scripts/up-orb.sh --build
```

| Serviço | URL padrão |
|---------|------------|
| Frontend | http://localhost:5174 |
| Backend | http://localhost:8001 |
| Health | http://localhost:8001/health/ |
| Postgres (host) | localhost:5433 |

Portas evitam conflito com WellSaaS (8000 / 5173).

---

## Permissões no Mac

- OrbStack **não** exige `sudo` para Docker.
- Se o daemon não responder: abrir o OrbStack e tentar de novo.
- Se o container não escrever migrations no host:

```bash
sudo chown -R $USER:$USER ./backend
```

---

## Branches

| Branch | Função |
|--------|--------|
| `orb` | Trabalho diário no Mac |
| `develop` | Staging (CI) |
| `assapp` | Produção (CI) |

Detalhes: [`ESTRATEGIA_BRANCHES_ORBSTACK.md`](ESTRATEGIA_BRANCHES_ORBSTACK.md)

---

## Docker

```bash
# OrbStack (recomendado no Mac)
./scripts/up-orb.sh

# Sem overrides ARM
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Migrations — sempre com exec
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

**Não remover** o volume `assapp_postgres_data`.

---

## Deploys (visão)

- Build das imagens: GitHub Actions (amd64).
- Servidor DigitalOcean: apenas `docker pull` + compose.
- Staging `:8080` · Produção `:80`.

Ver: [`DEPLOY_DIGITALOCEAN.md`](DEPLOY_DIGITALOCEAN.md)
