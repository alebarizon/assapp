# Deploy DigitalOcean — AssApp

**Última atualização:** 2026-10-22  
**Changelog recente:** [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](../changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md) (seção 12 — domínio, e-mail e HTTPS) · [`CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md`](../changelog/CHANGELOG_ANUIDADE_PAGAMENTO_2026_10.md)  
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

**Mesmo droplet, stacks isolados:** staging (`:8080`) e produção (`127.0.0.1:8081`, atrás do nginx do host) usam `COMPOSE_PROJECT_NAME` distinto (`assapp_staging` / `assapp_prod`) em `deploy.sh` — um deploy **não** derruba o outro.

Validado em 2026-08-17 (commit `5486641`).

### Produção (no ar)

| Campo | Valor |
|-------|--------|
| URL | https://gesttora.com.br/ (`www` e `http` redirecionam / respondem pelo mesmo certificado) |
| Health | https://gesttora.com.br/health/ · pelo IP: http://159.203.183.184/health/ |
| Domínio antigo | `gesttora.vertent.com.br` — redireciona (301) para `https://gesttora.com.br` |
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
main    → GitHub Actions → Docker Hub → deploy.sh production → 127.0.0.1:8081 ← nginx do host (80/443)
```

| Ambiente | Branch | Porta | Compose |
|----------|--------|-------|---------|
| Staging | `develop` | 8080 | `docker-compose.staging.yml` |
| Produção | `main` | 8081 (só localhost; público via nginx do host em 80/443) | `docker-compose.prod.yml` |

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
| Domínio + SSL (HTTPS) | ✅ 2026-10-22 — nginx do host + Let's Encrypt (ver seção HTTPS) |
| E-mail (DreamHost via túnel SSH) | ✅ 2026-10-22 |
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
| `nginx` | `assapp_nginx_<amb>` | Proxy em `127.0.0.1:8081` (prod) / `8080` (staging) |
| `smtp_tunnel` | `assapp_smtp_tunnel_prod` | Só produção: túnel SSH até o SMTP da DreamHost (ver seção E-mail) |

Variáveis do `.env.<amb>` ligadas ao agendador: `NEWSLETTER_POR_MINUTO` (padrão 30) e `REGUA_HORA` (padrão 8).
Enquanto o `EMAIL_BACKEND` for console (caso do staging), nada é entregue: a régua de anuidades roda com `--sem-email`
e as réguas de relacionamento nem rodam. Produção envia pela DreamHost (seção E-mail).

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

## Domínio + HTTPS

**Estado em 2026-10-22** — domínio próprio `gesttora.com.br` substitui `gesttora.vertent.com.br`, com HTTPS

| Item | Valor |
|------|--------|
| Domínio | `gesttora.com.br` (registrado no Registro.br) |
| DNS | zona na **DreamHost** (painel → DNS do domínio): **A** `@` → `159.203.183.184`; **CNAME** `www` → `gesttora.com.br` |
| Nameservers (Registro.br) | `ns1.dreamhost.com`, `ns2.dreamhost.com`, `ns3.dreamhost.com` |
| HTTPS | `https://gesttora.com.br` (Let's Encrypt, `gesttora.com.br` + `www`) |
| HTTP | redireciona (301) para `https://gesttora.com.br`, exceto `/health/` (diagnóstico pelo IP) |
| Domínio antigo | `gesttora.vertent.com.br` (A → mesmo IP) redireciona para o novo; segue em `ALLOWED_HOSTS` até ser desligado |

O workflow `deploy-production.yml` reescreve `ALLOWED_HOSTS` e `FRONTEND_URL=https://gesttora.com.br` no `.env.production` do droplet a cada deploy.

Verificação do DNS:

```bash
dig +short gesttora.com.br NS   # deve listar ns*.dreamhost.com
dig +short gesttora.com.br A    # 159.203.183.184
curl -sS https://gesttora.com.br/health/
```

### HTTPS: nginx do host + Certbot

```
internet :80/:443 → nginx do HOST (TLS) → 127.0.0.1:8081 → assapp_nginx_prod → frontend / backend
```

| Peça | Onde |
|------|------|
| Config do nginx do host | `/etc/nginx/sites-available/gesttora` (cópia versionada: [`nginx/host/gesttora.conf`](../../nginx/host/gesttora.conf)); `default` desabilitado |
| Certificado | `/etc/letsencrypt/live/gesttora.com.br/` (Let's Encrypt, 90 dias) |
| Renovação | `certbot.timer` (systemd, 2×/dia); `certbot renew --dry-run` validado em 2026-10-22 |
| Porta da stack de produção | `127.0.0.1:8081:80` em [`docker-compose.prod.yml`](../../docker-compose.prod.yml); `deploy.sh` checa o health nela |
| Proxy → Django | nginx do host manda `X-Forwarded-Proto`; o do container repassa (`map $proto_origem` em [`nginx_assapp_prod.conf`](../../nginx/nginx_assapp_prod.conf)); `SECURE_PROXY_SSL_HEADER` no settings |

Com `FRONTEND_URL` em https, os webhooks de PagBank e Mercado Pago passam a ser registrados automaticamente na cobrança (`payments.services.notificacao_automatica()`).

Durante o deploy de produção, o site mostra **502** do nginx do host por ~1–2 min (a stack em 8081 está trocando); o nginx do host não é tocado pelo deploy.

Alterar a config do host: editar `nginx/host/gesttora.conf`, copiar para `/etc/nginx/sites-available/gesttora`, `nginx -t && systemctl reload nginx`. Manter as linhas `# managed by Certbot` (a renovação usa o plugin nginx). Se o droplet for refeito: `apt install nginx certbot python3-certbot-nginx`, copiar a config **sem** o bloco 443 e o `default_server` da porta 80 apontando para `127.0.0.1:8081`, `ln -s` em `sites-enabled`, remover `default`, e rodar `certbot --nginx -d gesttora.com.br -d www.gesttora.com.br --redirect -m contato@gesttora.com.br --agree-tos`.

Diagnóstico:

```bash
systemctl status nginx --no-pager | head -5
ss -tlnp | grep -E ':80 |:443 |:8081 '
curl -sS -m 10 http://127.0.0.1:8081/health/     # stack de produção, sem o nginx do host
certbot certificates
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

---

## Google Analytics (GA4)

- Propriedade `G-S7EMQXSSJX`, passada só no build de produção (`build-args: VITE_GA_ID` em `deploy-production.yml`); staging e local não medem.
- [`GoogleAnalytics.tsx`](../../frontend/src/components/GoogleAnalytics.tsx) carrega o `gtag.js` e envia `page_view` só em `/`, `/login` e `/signup`, sem query string. Sites das associações (`/site`), painel (`/app`) e rotas com token não são medidos (`ga-disable-*` fora dessas rotas).
- No painel do GA4: Fluxo de dados → Medição otimizada → **desligar "Alterações de página com base em eventos do histórico do navegador"** (o componente já envia os `page_view`; ligado, duplicaria e mandaria a URL completa).
- Sem aviso de cookies por enquanto: citar o Google Analytics na política de privacidade quando ela existir.

---

## Deploy local (dev)

```bash
./scripts/up-orb.sh
```

---

## Ao retomar

1. `git pull` em `orb` (desenvolvimento local)
2. Desenvolver → merge `orb` → `develop` → push → validar staging `:8080`
3. Quando OK: merge `develop` → `main` → push → validar produção em https://gesttora.com.br/health/
4. Confirmar health OK (migrations já rodaram no startup do backend)
