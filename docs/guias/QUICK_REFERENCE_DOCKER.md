# Referência Rápida — Docker AssApp

**Última atualização:** 2026-07-19  
**Branch de trabalho no Mac:** `orb`

---

## Como iniciar

### Mac / OrbStack (recomendado)

```bash
./scripts/up-orb.sh          # foreground
./scripts/up-orb.sh -d       # background
./scripts/up-orb.sh --build  # rebuild frontend ARM64
```

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5174 |
| Backend | http://localhost:8001 |

### Sem OrbStack

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

## Comandos essenciais

```bash
# Logs
docker compose logs -f backend
docker compose logs -f frontend

# Status
docker compose ps

# Parar
docker compose down

# Migrations (sempre exec)
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas

# Shell Django
docker compose exec backend python manage.py shell

# Seed sistema
./scripts/init_sistema_tenant.sh
```

---

## Arquivos Compose

| Arquivo | Quando usar |
|---------|-------------|
| `docker-compose.yml` | Base (sempre) |
| `docker-compose.dev.yml` | Hot reload |
| `docker-compose.orb.yml` | Só Mac / OrbStack |

Equivalente OrbStack:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.orb.yml up
```

---

## Volumes (não apagar)

- `assapp_postgres_data`
- `assapp_static_files`
- `assapp_media_files`

```bash
# ❌ NÃO faça em desenvolvimento com dados
docker compose down -v
```

---

## Branches (lembrete)

```
orb → develop (staging) → assapp (produção)
```

Ver: `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`
