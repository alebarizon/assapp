# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-08-17  
**Changelog recente:** [`CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md`](../changelog/CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md) · [`CHANGELOG_2026_07_24_27.md`](../changelog/CHANGELOG_2026_07_24_27.md)

---

## Staging (no ar)

| Campo | Valor |
|-------|--------|
| URL | http://159.203.183.184:8080/ |
| Health | http://159.203.183.184:8080/health/ |
| Branch CI | `develop` |
| Compose | `docker-compose.staging.yml` |
| Tag imagens | `develop` |

**Mesmo droplet, stacks isolados:** staging (`:8080`) e produção (`:80`) usam `COMPOSE_PROJECT_NAME` distinto (`assapp_staging` / `assapp_prod`) em `deploy.sh` — um deploy **não** derruba o outro.

### Produção (no ar)

| Campo | Valor |
|-------|--------|
| URL (IP) | http://159.203.183.184/ |
| URL (domínio) | http://gesttora.vertent.com.br/ |
| Health | http://gesttora.vertent.com.br/health/ |
| Branch CI | `main` |
| Compose | `docker-compose.prod.yml` |
| Tag imagens | `latest` |

Validado em 2026-07-25 (Actions run `30174258426`).

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

**Branches alinhadas** em `b2433e5` (2026-07-25). Fluxo: `orb` → `develop` → `main`.

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
| Produção (`main`) | ✅ (promovida 2026-07-25 · landing Gesttora) |
| Domínio HTTP | ✅ `gesttora.vertent.com.br` → A `159.203.183.184` |
| Domínio + SSL (HTTPS) | ❌ **adiado** — ver seção abaixo |
| Seed tenant sistema (staging) | ❓ |
| Seed tenant `demo` (staging/prod) | Rodar após deploy — ver abaixo |

---

## Migrations (automáticas no startup)

**Não** rodar migrations manualmente após cada deploy — o backend já executa na subida do container, **antes** do Gunicorn (mesmo padrão WellSaaS):

```yaml
# docker-compose.staging.yml / docker-compose.prod.yml — service backend command:
python manage.py wait_for_db &&
python manage.py migrate_schemas --shared &&
python manage.py migrate_schemas &&
python manage.py collectstatic --noinput &&
gunicorn ...
```

O [`scripts/deploy.sh`](../../scripts/deploy.sh) só faz pull + `up -d` e aguarda `/health/`. Se o health passou, as migrations já foram aplicadas.

### Recuperação manual (só se o backend falhar ao subir)

```bash
cd /opt/assapp
docker logs assapp_backend_staging --tail 100   # ou assapp_backend_prod
docker exec assapp_backend_staging python manage.py migrate_schemas --shared --noinput
docker exec assapp_backend_staging python manage.py migrate_schemas --noinput
docker compose -f docker-compose.staging.yml --env-file .env.staging restart backend
```

**Ordem obrigatória:** `--shared` primeiro (schema `public`), depois tenants.

Seed demo (website + anuidades) — **opcional**, só se quiser tenant `demo` no ambiente remoto:

```bash
cd /opt/assapp
chmod +x scripts/init_demo_tenant.sh
# Edite ASSAPP_BACKEND_CONTAINER se o nome do container for _prod
ASSAPP_BACKEND_CONTAINER=assapp_backend_staging ./scripts/init_demo_tenant.sh
```

Validação:

```bash
curl -s "http://159.203.183.184:8080/api/website/public/?schema=demo" | head -c 200
curl -s "http://159.203.183.184:8080/site?schema=demo" -o /dev/null -w "%{http_code}\n"
```

---

## Domínio + HTTPS (adiado — retomar depois)

**Estado em 2026-07-25**

| Item | Valor |
|------|--------|
| Domínio raiz (hospedagem DNS) | `vertent.com.br` (painel do registrador / DNS onde o domínio está) |
| Subdomínio | `gesttora.vertent.com.br` |
| DNS | registro **A** → `159.203.183.184` |
| HTTP | ✅ `http://gesttora.vertent.com.br` |
| HTTPS | ❌ porta **443** sem listener (`Connection refused`) |

**Causa:** produção AssApp só publica `80:80` ([`docker-compose.prod.yml`](../../docker-compose.prod.yml)); o nginx do container ([`nginx/nginx_assapp_prod.conf`](../../nginx/nginx_assapp_prod.conf)) só faz `listen 80`. Let’s Encrypt no host, se instalado, **não** está ligado a um serviço na 443.

### Solução recomendada (quando retomar)

1. Mudar o mapeamento da produção AssApp de `80:80` para interno, ex.: `127.0.0.1:8081:80`.
2. Nginx (ou Caddy) **no host** escutando **80 + 443**, `server_name gesttora.vertent.com.br`, `proxy_pass http://127.0.0.1:8081`.
3. Emitir/renovar certificado:
   ```bash
   sudo certbot --nginx -d gesttora.vertent.com.br
   ```
4. Em `.env.production` no droplet: incluir `gesttora.vertent.com.br` em `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS=https://gesttora.vertent.com.br`.
5. Reiniciar stack + nginx do host; validar `https://gesttora.vertent.com.br`.

**Alternativa (menos preferida):** montar `/etc/letsencrypt` no `assapp_nginx_prod`, `listen 443 ssl` no conf e publicar `443:443` no compose.

Diagnóstico rápido no droplet:

```bash
ss -tlnp | grep -E ':80|:443'
sudo ls /etc/letsencrypt/live/
```

---

## Deploy local (dev)

```bash
./scripts/up-orb.sh
```

---

## Ao retomar

1. `git pull` em `orb` (desenvolvimento local)
2. Desenvolver → merge `orb` → `develop` → push → validar staging `:8080`
3. Quando OK: merge `develop` → `main` → push → validar produção `:80`
4. Confirmar health OK (migrations já rodaram no startup do backend)
5. **HTTPS:** seguir seção [Domínio + HTTPS (adiado)](#domínio--https-adiado--retomar-depois)
