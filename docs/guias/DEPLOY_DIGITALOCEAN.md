# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-08-17  
**Changelog recente:** [`CHANGELOG_2026_08_17_DEPLOY_SEED.md`](../changelog/CHANGELOG_2026_08_17_DEPLOY_SEED.md) · [`CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md`](../changelog/CHANGELOG_ECOMMERCE_WEBSITE_2026_08.md)

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

Validado em 2026-08-17 (commit `5486641`).

### Produção (no ar)

| Campo | Valor |
|-------|--------|
| URL (IP) | http://159.203.183.184/ |
| URL (domínio) | http://gesttora.com.br/ |
| Health | http://gesttora.com.br/health/ |
| Domínio antigo | `gesttora.vertent.com.br` — ainda aceito em `ALLOWED_HOSTS` durante a transição |
| Branch CI | `main` |
| Compose | `docker-compose.prod.yml` |
| Tag imagens | `latest` |

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
| Domínio HTTP | `gesttora.com.br` → A `159.203.183.184` (DNS na DigitalOcean — ver seção Domínio) |
| Domínio + SSL (HTTPS) | ❌ **adiado** — ver seção abaixo |
| Seed tenant sistema + abciber | ✅ executado staging + prod (2026-08-17) |

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

Seed demo (website + anuidades) — **opcional**:

```bash
ASSAPP_BACKEND_CONTAINER=assapp_backend_staging ./scripts/init_demo_tenant.sh
```

**Obrigatório após 1º deploy** (login ABCiber e dados piloto):

```bash
cd /opt/assapp
# Staging:
ASSAPP_BACKEND_CONTAINER=assapp_backend_staging ./scripts/init_sistema_tenant.sh
# Produção:
ASSAPP_BACKEND_CONTAINER=assapp_backend_prod ./scripts/init_sistema_tenant.sh
```

Credenciais criadas: `diretoria@abciber.org.br` / `abciber123` (tenant `abciber`).

Validação:

```bash
curl -s "http://159.203.183.184:8080/api/website/public/?schema=demo" | head -c 200
curl -s "http://159.203.183.184:8080/site?schema=demo" -o /dev/null -w "%{http_code}\n"
```

---

## Domínio + HTTPS (adiado — retomar depois)

**Estado em 2026-10-22** — domínio próprio `gesttora.com.br` substitui `gesttora.vertent.com.br`

| Item | Valor |
|------|--------|
| Domínio | `gesttora.com.br` (registrado no Registro.br) |
| DNS | zona na DigitalOcean (Networking → Domains): **A** `@` → `159.203.183.184`; **A** ou **CNAME** `www` → mesmo droplet |
| Nameservers (Registro.br) | `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com` |
| HTTP | `http://gesttora.com.br` |
| HTTPS | ❌ porta **443** sem listener (`Connection refused`) |
| Domínio antigo | `gesttora.vertent.com.br` (A → mesmo IP) segue em `ALLOWED_HOSTS` até ser desligado |

O workflow `deploy-production.yml` reescreve `ALLOWED_HOSTS` e `FRONTEND_URL` no `.env.production` do droplet a cada deploy.

Verificação do DNS:

```bash
dig +short gesttora.com.br NS   # deve listar ns*.digitalocean.com
dig +short gesttora.com.br A    # 159.203.183.184
curl -sS http://gesttora.com.br/health/
```

### E-mail (DreamHost)

Caixas `contato@gesttora.com.br` e `noreply@gesttora.com.br` hospedadas na DreamHost. A DigitalOcean não hospeda e-mail; a zona DNS na DO precisa dos registros da DreamHost (copiar os valores exatos do painel DreamHost → Websites/Mail → DNS do domínio):

| Tipo | Nome | Valor |
|------|------|-------|
| MX (prioridade 0) | `@` | `mx1.dreamhost.com.` |
| MX (prioridade 0) | `@` | `mx2.dreamhost.com.` |
| TXT (SPF) | `@` | `v=spf1 mx include:netblocks.dreamhost.com include:relay.mailchannels.net -all` |
| TXT (DKIM) | `dreamhost._domainkey` | chave gerada no painel DreamHost |
| TXT (DMARC) | `_dmarc` | `v=DMARC1; p=none; rua=mailto:contato@gesttora.com.br` (endurecer para `quarantine`/`reject` depois de validar) |

Envio pelo sistema (convites, senha, certificados, newsletter): SMTP `smtp.dreamhost.com:587` (STARTTLS), usuário `noreply@gesttora.com.br`. A senha fica no secret **`SMTP_PASSWORD`** do GitHub Actions (sem aspas simples); com ele preenchido, `deploy-production.yml` grava o bloco `EMAIL_*` e `SUPPORT_EMAIL=contato@gesttora.com.br` no `.env.production`. Sem o secret, o envio continua em modo console (log).

```bash
dig +short gesttora.com.br MX   # mx1/mx2.dreamhost.com
dig +short gesttora.com.br TXT  # SPF com netblocks.dreamhost.com
```

**Causa:** produção AssApp só publica `80:80` ([`docker-compose.prod.yml`](../../docker-compose.prod.yml)); o nginx do container ([`nginx/nginx_assapp_prod.conf`](../../nginx/nginx_assapp_prod.conf)) só faz `listen 80`. Let’s Encrypt no host, se instalado, **não** está ligado a um serviço na 443.

### Solução recomendada (quando retomar)

1. Mudar o mapeamento da produção AssApp de `80:80` para interno, ex.: `127.0.0.1:8081:80`.
2. Nginx (ou Caddy) **no host** escutando **80 + 443**, `server_name gesttora.com.br www.gesttora.com.br`, `proxy_pass http://127.0.0.1:8081`.
3. Emitir/renovar certificado:
   ```bash
   sudo certbot --nginx -d gesttora.com.br -d www.gesttora.com.br
   ```
4. Em `.env.production` no droplet: `CSRF_TRUSTED_ORIGINS=https://gesttora.com.br,https://www.gesttora.com.br` e `FRONTEND_URL=https://gesttora.com.br` (ajustar também o `sed` de `FRONTEND_URL` em `deploy-production.yml`).
5. Reiniciar stack + nginx do host; validar `https://gesttora.com.br`.

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
