# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-10-18  
**Changelog recente:** [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](../changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md) (seção 11 — agendador e deploy) · [`CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md`](../changelog/CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md)  
**Roteiro de deploy:** [`PROMPT_DEPLOY.md`](../../PROMPT_DEPLOY.md)

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
| Domínio HTTP | `gesttora.com.br` → A `159.203.183.184` (DNS na DreamHost — ver seção Domínio) |
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

O [`scripts/deploy.sh`](../../scripts/deploy.sh), nesta ordem:

1. `docker pull` das imagens — **antes** de parar a stack: se faltar disco ou rede, a versão anterior continua no ar.
2. `down --remove-orphans` só do projeto do ambiente e `up -d` (a troca leva ~1–2 min fora do ar).
3. Aguarda `/health/` por até 2 min. Se o health passou, as migrations já foram aplicadas.
4. `docker image prune -f` — remove só imagens sem tag e sem container (cada deploy deixa ~1 GB de imagem antiga).

Nunca `system prune`, `container prune`, `volume rm` nem `down -v` no droplet: staging e produção dividem o host.

## Serviços de cada stack

| Serviço | Container | Função |
|---------|-----------|--------|
| `db` | `assapp_db_<amb>` | PostgreSQL 14 (volume `assapp_postgres_data_<amb>`) |
| `backend` | `assapp_backend_<amb>` | Migrations no startup + Gunicorn |
| `agendador` | `assapp_agendador_<amb>` | `manage.py agendador`: lote da newsletter a cada minuto; régua de anuidades e réguas de relacionamento (`reguas_relacionamento`) 1×/dia a partir de `REGUA_HORA` (padrão 8h Brasília). Sem healthcheck HTTP |
| `frontend` | `assapp_frontend_<amb>` | Build Vite servido por nginx (o healthcheck aparece `unhealthy`, mas o site responde — pendente investigar) |
| `nginx` | `assapp_nginx_<amb>` | Proxy na porta 80 (prod) / 8080 (staging) |

Variáveis do `.env.<amb>` ligadas ao agendador: `NEWSLETTER_POR_MINUTO` (padrão 30) e `REGUA_HORA` (padrão 8).
Enquanto o `EMAIL_BACKEND` for console, nada é entregue: a régua de anuidades roda com `--sem-email` e as réguas
de relacionamento nem rodam. Para enviar de verdade é
preciso um provedor por API HTTP (Brevo, Resend, SES): a DigitalOcean bloqueia SMTP de saída.

Na primeira subida após mudanças de modelo, o agendador pode logar `relation ... does not exist` uma vez (rodou antes
das migrations do backend); o ciclo seguinte já funciona.

## Disco do droplet

24 GB. Conferir antes de investigar deploy falho:

```bash
ssh root@159.203.183.184 'df -h /; docker system df'
```

Se encher (`no space left on device` no pull): `docker image prune -f` e, se preciso, `journalctl --vacuum-size=100M`.
Em 2026-10-18 o disco chegou a 98% (16 GB de imagens antigas), o pull falhou depois do `down` e a produção ficou
~1 h fora — origem da reordenação do `deploy.sh`.

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

Credenciais criadas: `diretoria@abciber.example.org` / `abciber123` (tenant `abciber`).

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
| DNS | zona na **DreamHost** (painel → DNS do domínio): **A** `@` → `159.203.183.184`; **CNAME** `www` → `gesttora.com.br` |
| Nameservers (Registro.br) | `ns1.dreamhost.com`, `ns2.dreamhost.com`, `ns3.dreamhost.com` |
| HTTP | `http://gesttora.com.br` |
| HTTPS | ❌ porta **443** sem listener (`Connection refused`) |
| Domínio antigo | `gesttora.vertent.com.br` (A → mesmo IP) segue em `ALLOWED_HOSTS` até ser desligado |

O workflow `deploy-production.yml` reescreve `ALLOWED_HOSTS` e `FRONTEND_URL` no `.env.production` do droplet a cada deploy.

Verificação do DNS:

```bash
dig +short gesttora.com.br NS   # deve listar ns*.dreamhost.com
dig +short gesttora.com.br A    # 159.203.183.184
curl -sS http://gesttora.com.br/health/
```

### E-mail (DreamHost)

Caixas `contato@gesttora.com.br` e `noreply@gesttora.com.br` hospedadas na DreamHost, que também hospeda a zona DNS (só o registro A aponta para o droplet). Registros de e-mail na zona (MX, SPF e DKIM criados automaticamente pela DreamHost; DMARC adicionar manualmente):

| Tipo | Nome | Valor |
|------|------|-------|
| MX (prioridade 0) | `@` | `mx1.dreamhost.com.` |
| MX (prioridade 0) | `@` | `mx2.dreamhost.com.` |
| TXT (SPF) | `@` | `v=spf1 mx include:netblocks.dreamhost.com include:relay.mailchannels.net -all` |
| TXT (DKIM) | `dreamhost._domainkey` | chave gerada no painel DreamHost |
| TXT (DMARC) | `_dmarc` | `v=DMARC1; p=none; rua=mailto:contato@gesttora.com.br` (endurecer para `quarantine`/`reject` depois de validar) |

#### Envio pelo sistema: túnel SSH até a DreamHost

A DigitalOcean bloqueia a saída nas portas 25, 465 e 587 do droplet (testado em 2026-10-22; 2525 também fecha). O envio passa por um **túnel SSH** (porta 22, liberada) até o servidor da DreamHost:

| Peça | Valor |
|------|-------|
| Serviço | `smtp_tunnel` em `docker-compose.prod.yml` (`alpine:3.20` + `ssh -N -L 0.0.0.0:587:smtp.dreamhost.com:587`) |
| Alias de rede | `smtp.dreamhost.com` — o backend usa `EMAIL_HOST=smtp.dreamhost.com:587` e o certificado TLS confere |
| Usuário SSH | `gesttora@pdx1-shared-a1-07.dreamhost.com` (`SMTP_TUNNEL_USER` / `SMTP_TUNNEL_HOST`) |
| Chave | `/opt/assapp-smtp/id_ed25519` + `known_hosts` no droplet (fora do repo; montado só-leitura) |
| Backend Django | `core.email_backend.CotaSMTPBackend` (SMTP + registro na cota) |
| Autenticação SMTP | `noreply@gesttora.com.br`, senha no secret **`SMTP_PASSWORD`** |

- A chave pública está em `~gesttora/.ssh/authorized_keys` na DreamHost com `restrict,port-forwarding,permitopen=...`, **mas o sshd da DreamHost ignora essas opções**: a chave dá shell ao usuário `gesttora`. Manter esse usuário dedicado ao túnel (sem arquivos de site) e a chave só no droplet (root, `600`).
- **Cota da DreamHost:** 100 destinatários/hora por caixa, não ajustável; estouros repetidos bloqueiam a caixa de vez ([SMTP quota limits](https://help.dreamhost.com/hc/en-us/articles/215730437-SMTP-quota-limits)). `EMAIL_LIMITE_POR_HORA=70` (tabela `core_emailenviado` no schema public) faz newsletter, réguas e lembretes de anuidade pararem ao atingir 70 na última hora e continuarem depois; e-mails individuais (senha, convite, certificado) sempre saem. Réguas e lembretes rodam uma vez por dia: o que sobrar fica para o dia seguinte.
- Com `SMTP_PASSWORD` preenchido, `deploy-production.yml` grava `EMAIL_*`, `EMAIL_LIMITE_POR_HORA=70` e `SUPPORT_EMAIL=contato@gesttora.com.br` no `.env.production` (e falha se faltar a chave do túnel). Sem o secret, o envio continua em modo console (log). `EMAIL_TIMEOUT=15` evita requisição presa se o túnel cair.
- **Antes de ligar:** o agendador passa a enviar lembretes de anuidade e réguas (boas-vindas e autor não sócio nascem ligadas) para os associados cadastrados — conferir se os e-mails do tenant de demonstração são reais.

Diagnóstico:

```bash
docker logs assapp_smtp_tunnel_prod --tail 20          # vazio = túnel de pé
docker exec assapp_backend_prod python manage.py sendtestemail voce@exemplo.com
docker exec assapp_backend_prod python manage.py shell -c "from core.cota_email import usados_na_ultima_hora as u; print(u())"
```

Recriar a chave (se o droplet for refeito): `ssh-keygen -t ed25519 -N "" -f /opt/assapp-smtp/id_ed25519`, `ssh-keyscan -t ed25519,rsa pdx1-shared-a1-07.dreamhost.com > /opt/assapp-smtp/known_hosts`, `chmod 600` e colar a `.pub` em `~/.ssh/authorized_keys` do usuário `gesttora` na DreamHost.

#### Opção futura: Brevo (quando houver volume)

Quando a cota de 100/hora da DreamHost apertar (newsletter de várias associações), trocar o envio para um provedor por API HTTP — recomendado **Brevo** (plano gratuito ~300/dia, painel em PT-BR; alternativas Resend e Amazon SES):

1. Criar conta Brevo e autenticar o domínio `gesttora.com.br` (registros DKIM/Brevo-code na zona da DreamHost; SPF ganha `include:spf.brevo.com`).
2. Backend: `django-anymail[brevo]`, `EMAIL_BACKEND=anymail.backends.brevo.EmailBackend` e `ANYMAIL={"BREVO_API_KEY": ...}` (secret no GitHub). Para manter a cota, criar um backend que estenda o da Anymail registrando em `core.cota_email`, ou zerar `EMAIL_LIMITE_POR_HORA`.
3. Remover o serviço `smtp_tunnel`. As caixas da DreamHost continuam recebendo (`contato@`).

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
