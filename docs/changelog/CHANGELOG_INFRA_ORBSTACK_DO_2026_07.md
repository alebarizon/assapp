# Changelog — Infra Git, OrbStack e DigitalOcean

> **Última atualização:** 2026-10-22 (seção 12)  
> **Domínio:** produção migrou para `gesttora.com.br` (DNS e e-mail na DreamHost, A → mesmo IP do droplet); `gesttora.vertent.com.br` segue aceito na transição. SSL adiado (ver `DEPLOY_DIGITALOCEAN.md`). SMTP de saída bloqueado no droplet.

---

## Resumo executivo (estado atual)

| Área | Status |
|------|--------|
| Repo GitHub + branches (`orb` / `develop` / `main`) | ✅ |
| OrbStack local (Mac) | ✅ |
| Droplet DO `159.203.183.184` + bootstrap | ✅ |
| Repository secrets GitHub Actions | ✅ |
| Docker Hub `assapp-backend` / `assapp-frontend` | ✅ |
| Compose staging/prod + nginx + `deploy.sh` | ✅ |
| **Staging no ar** (`:8080`) | ✅ |
| Produção (`main` → `:80`) | ✅ (2026-07-25) |
| Domínio HTTP `gesttora.com.br` (antes `gesttora.vertent.com.br`) | A → droplet (2026-10-22) |
| Domínio + SSL (HTTPS / Certbot) | ❌ **adiado** — proxy TLS no host + AssApp em `127.0.0.1:8081` (detalhe em [`DEPLOY_DIGITALOCEAN.md`](../guias/DEPLOY_DIGITALOCEAN.md#domínio--https-adiado--retomar-depois)) |
| Tenant `sistema` / seed no staging | ❓ |
| Tenant `demo` em staging/prod | ❌ (script local: `scripts/init_demo_tenant.sh`) |

### URLs produção (funcionando)

| Recurso | URL |
|---------|-----|
| Frontend (domínio) | http://gesttora.com.br/ |
| Frontend (IP) | http://159.203.183.184/ |
| Health API | http://gesttora.com.br/health/ |

### URLs staging (funcionando)

| Recurso | URL |
|---------|-----|
| Frontend | http://159.203.183.184:8080/ |
| Health API | http://159.203.183.184:8080/health/ |
| Actions (último deploy OK) | https://github.com/alebarizon/assapp/actions/runs/30174090008 |

---

## 1. Repositório Git

| Item | Valor |
|------|--------|
| Remote | https://github.com/alebarizon/assapp |
| SSH | `git@github.com:alebarizon/assapp.git` |
| Produção (default GitHub) | `main` |
| Staging | `develop` |
| Dev Mac / OrbStack | `orb` |

```
orb → develop (staging :8080) → main (produção :80)
```

### Commits relevantes (infra)

| Commit | Descrição |
|--------|-----------|
| `3262e34` | Init repo + OrbStack + branches |
| `13a47a6` | Produção → branch `main` (padrão WellSaaS) |
| `f96acbf` | Remoção docs PIPE do repositório |
| `275431a` | Docs infra + `setup_digitalocean.sh` |
| `25bc968` | Pausa docs + checklist secrets |
| `e937349` | Fix `vite-env.d.ts` (build CI frontend) |
| `81d99be` | Compose staging/prod + nginx + `deploy.sh` |

### Sincronização de branches (2026-07-25)

| Branch | Commit | Observação |
|--------|--------|------------|
| `orb` | `b2433e5` | landing Gesttora + tenant demo script |
| `develop` | `b2433e5` | staging deploy OK |
| `main` | `b2433e5` | produção deploy OK |

Deploys: staging run `30174090008` · produção run `30174258426`.

### Sincronização anterior (2026-07-21)

| Branch | Commit | Observação |
|--------|--------|------------|
| `orb` | `81d99be` | alinhada com `develop` |
| `develop` | `81d99be` | staging deployado |
| `main` | `275431a` | atrás de `develop` (corrigido em 2026-07-25) |

---

## 2. Desenvolvimento local (Mac / OrbStack)

```bash
git checkout orb
cp .env.example .env   # se ainda não existir
./scripts/up-orb.sh --build
./scripts/init_sistema_tenant.sh   # tenant sistema (superadmin)
```

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5174 |
| Backend | http://localhost:8001 |
| Health | http://localhost:8001/health/ |

Arquivos: `docker-compose.orb.yml`, `scripts/up-orb.sh` — ver `docs/guias/QUICK_REFERENCE_DOCKER.md`.

---

## 3. Droplet DigitalOcean

| Campo | Valor |
|-------|--------|
| IP | **`159.203.183.184`** |
| Hostname | `drop-assapp` |
| SO | Ubuntu 24.04.4 LTS |
| SSH | `ssh root@159.203.183.184` |
| App dir | `/opt/assapp` |
| Chave Mac | `~/.ssh/id_ed25519` |

### Bootstrap (executado 2026-07-19)

```bash
scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
```

Docker 29.6.2 · UFW: 22, 80, 443, 8080 · swap 2G · usuário `deploy`.

### Containers staging (após deploy)

```
assapp_nginx_staging
assapp_frontend_staging
assapp_agendador_staging   # desde 2026-10-18 (ver seção 11)
assapp_backend_staging
assapp_db_staging
```

Verificar: `ssh root@159.203.183.184 'docker ps'`

---

## 4. Pipeline CI/CD

```
Push develop → build amd64 → Hub (tag develop) → SSH → ./scripts/deploy.sh staging → :8080
Push main    → build amd64 → Hub (tag latest)  → SSH → ./scripts/deploy.sh production → :80
```

| Workflow | Arquivo |
|----------|---------|
| Staging | `.github/workflows/deploy-staging.yml` |
| Produção | `.github/workflows/deploy-production.yml` |

- Concurrency `deploy-server` (mesmo droplet)
- `.env.staging` / `.env.production` gerados/atualizados no deploy (senhas auto se placeholder)
- Frontend build: `VITE_API_URL` vazio → API same-origin via nginx (`/api/`)

---

## 5. Docker Hub

| Repositório | Tags usadas |
|-------------|-------------|
| `alebarizon/assapp-backend` | `develop`, `latest` |
| `alebarizon/assapp-frontend` | `develop`, `latest` |

WellSaaS (separado): `alebarizon/wellnz-backend`, `alebarizon/wellnz-frontend`.

---

## 6. Secrets (Repository secrets)

URL: https://github.com/alebarizon/assapp/settings/secrets/actions  

**Usar Repository secrets** — não Environment secrets/variables.

| Secret | Valor |
|--------|--------|
| `DOCKER_USERNAME` | `alebarizon` |
| `DOCKER_PASSWORD` | Access Token Docker Hub (Read & Write) |
| `DO_HOST` | `159.203.183.184` |
| `DO_STAGING_HOST` | `159.203.183.184` |
| `DO_USER` | `root` (ou `deploy`) |
| `DO_SSH_KEY` | chave privada SSH (`~/.ssh/id_ed25519`) |
| `G_TOKEN_DEPLOY` | opcional (repo público) |

**Não confundir:** token `ghp_…` = GitHub PAT (`G_TOKEN_DEPLOY`), **não** `DOCKER_PASSWORD`.

Checklist: `.github/CHECKLIST_SECRETS.md`

---

## 7. Arquivos de deploy (criados 2026-07-20)

| Arquivo | Função |
|---------|--------|
| `docker-compose.staging.yml` | Stack staging (pull-only) |
| `docker-compose.prod.yml` | Stack produção (pull-only) |
| `nginx/nginx_assapp_staging.conf` | Proxy :8080 |
| `nginx/nginx_assapp_prod.conf` | Proxy :80 |
| `scripts/deploy.sh` | Pull (antes de parar) + up + health check + limpeza de imagens sem tag |
| `scripts/setup_digitalocean.sh` | Bootstrap droplet |
| `env.staging.example` / `env.production.example` | Templates |

---

## 8. Problemas resolvidos nesta fase

| Problema | Solução |
|----------|---------|
| SSH droplet | Chave `mac-ale` em `authorized_keys` |
| Docker Hub 401 insufficient scopes | Token com Read & Write |
| `npm run build` falha no CI | `frontend/src/vite-env.d.ts` |
| Secrets em Environment errado | Mover para **Repository secrets** |
| Deploy sem containers | Compose + `deploy.sh` + nginx |
| Disco cheio derrubou produção (2026-10-18) | Pull antes do `down` + `docker image prune -f` após sucesso (seção 11) |

---

## 9. Ao retomar o projeto

### Imediato (operacional)

1. `git checkout orb && git pull origin orb`
2. Desenvolver em `orb` → merge/push em `develop` para atualizar staging
3. Validar staging (`:8080`) e produção (`gesttora.com.br`) após cada deploy
4. Seeds no droplet (se necessário):
   - `./scripts/init_sistema_tenant.sh` — superadmin + ABCiber
   - `./scripts/init_demo_tenant.sh` — tenant `demo` (`demo@demo.com` / `demo`)

### HTTPS (adiado)

Ver seção em [`DEPLOY_DIGITALOCEAN.md`](../guias/DEPLOY_DIGITALOCEAN.md#domínio--https-adiado--retomar-depois): proxy TLS no host + AssApp em porta interna.

### Promover produção (fluxo habitual)

```bash
git checkout develop && git merge orb && git push origin develop
# validar staging
git checkout main && git merge develop && git push origin main
# validar http://gesttora.com.br/
```

### Produto / PIPE (Fase 1)

Retomar sprints conforme `docs/referencia/STATUS_SPRINTS_FASE1.md` — mandatos (H1+H2), memoria, eventos, membros, etc.

### Infra futura

- HTTPS (Certbot) — ver acima
- Stripe real (último, conforme docs)
- `G_TOKEN_DEPLOY` se repo ficar privado

Referência WellSaaS: `/Users/ale/Desktop/Wellsaas/docs/guias/BASE_CONHECIMENTO_DEPLOYS.md`

---

## 10. Referência rápida

```bash
# Mac — dev
./scripts/up-orb.sh

# Droplet — status
ssh root@159.203.183.184 'docker ps; curl -s http://127.0.0.1:8080/health/'

# Promover código
git checkout develop && git merge orb && git push origin develop

# Actions
open https://github.com/alebarizon/assapp/actions

# Disco do droplet
ssh root@159.203.183.184 'df -h /; docker system df'
```

---

## 11. Agendador e deploy resiliente (2026-10-18)

Deploys do dia, todos validados em staging antes de `main`:

| Commit | Conteúdo |
|--------|----------|
| `5106f5e` | Assembleias e votações, newsletter e diretório público; serviço de fila da newsletter no compose |
| `53f9fed` | Serviço `newsletter` vira `agendador` (fila a cada minuto + régua de anuidades diária) |
| `f3d0852` | `deploy.sh`: pull antes de parar a stack e limpeza de imagens sem tag |

### Agendador

- Novo comando `core/management/commands/agendador.py`, serviço `agendador` em `docker-compose.staging.yml` e
  `docker-compose.prod.yml` (mesma imagem do backend, `environment: *backend_env`, `healthcheck: disable: true`).
- Containers `assapp_agendador_staging` / `assapp_agendador_prod` (~60 MB). O antigo `assapp_newsletter_*` saiu;
  `deploy.sh` ainda o remove por nome, por garantia.
- Régua diária a partir de `REGUA_HORA` (padrão 8, Brasília); falha repete no minuto seguinte; idempotente.
- Com `EMAIL_BACKEND` console (situação atual de staging e produção), roda `regua_anuidades --sem-email`: só marca
  vencidas/inadimplentes, sem registrar lembretes que não saíram.
- Primeira execução em produção: abciber com 3 anuidades → vencida e 2 filiações → inadimplente (impacto conferido
  antes e aprovado).

### Incidente: produção fora por ~1 h

- **Causa:** disco do droplet em 98% (16 GB de imagens antigas acumuladas). O `deploy.sh` fazia `down` antes do
  `docker pull`; o pull da imagem nova (~1 GB) falhou por falta de espaço e a produção ficou sem containers.
  Staging e volumes não foram afetados.
- **Recuperação:** conferidos `.env.production` e o volume `assapp_postgres_data_prod`; `docker image prune -f`
  (16 GB) + `journalctl --vacuum-size=100M` (500 MB); `./scripts/deploy.sh production`. Disco em 31%.
- **Correção (`f3d0852`):** pull antes do `down`; `docker image prune -f` após health OK; espaço livre no log do deploy.
- **Processo:** `PROMPT_DEPLOY.md` agora permite `docker image prune -f` (sem `-a`), manda acompanhar o `/health/`
  da produção durante o deploy (não só o container novo) e lista `no space left on device` entre os logs ruins.

### Pendências de infra

- Provedor de e-mail por API HTTP (Brevo, Resend ou SES) — destrava lembretes da régua e newsletter.
- Healthcheck do `frontend` aparece `unhealthy` em staging e produção, embora o site responda.
- HTTPS (seção 9).

---

## 12. Domínio gesttora.com.br, e-mail DreamHost e verify-staging (2026-10-22)

Deploys do dia, todos validados em staging antes de `main`:

| Commit | Conteúdo | Produção |
|--------|----------|----------|
| `39ae19e` | Domínio `gesttora.com.br` (`ALLOWED_HOSTS`, `FRONTEND_URL`, remetente, landing) + bloco SMTP opcional no deploy | 13:10 (via **Run workflow**) |
| `9b6cb19` | Docs: DNS na DreamHost | junto com o anterior |
| `569d154` | Merge da `orb`: gateways PagBank/Mercado Pago, réguas da newsletter (`newsletter/0002`, `payments/0003`) e correção do `verify-staging` | 13:58 |

### Domínio

- `gesttora.com.br` registrado no Registro.br. DNS e e-mail na **DreamHost**: A `@` → `159.203.183.184`,
  CNAME `www` → `gesttora.com.br`, MX `mx1/mx2.dreamhost.com`, SPF e DKIM criados pela DreamHost.
- Nameservers trocados no Registro.br para `ns1/ns2/ns3.dreamhost.com`. Como o domínio usava o DNS do próprio
  Registro.br (`a/b.auto.dns.br`), a troca tem carência de ~1h20 antes de publicar.
- `ALLOWED_HOSTS`: `159.203.183.184,gesttora.com.br,www.gesttora.com.br,gesttora.vertent.com.br,localhost,127.0.0.1`.
  O domínio antigo segue aceito até ser desligado.
- `deploy-production.yml` reescreve `ALLOWED_HOSTS` e `FRONTEND_URL=http://gesttora.com.br` no `.env.production`
  a cada deploy e troca o remetente antigo `noreply@vertent.com.br` por `noreply@gesttora.com.br`.
- Roteamento de tenant é por path (`TenantPathMiddleware`); `BASE_DOMAIN` não mudou.

### E-mail: SMTP bloqueado no droplet

- Caixas `contato@` e `noreply@gesttora.com.br` criadas na DreamHost (recebimento depende só do DNS).
- `deploy-production.yml` ganhou um bloco que, com o secret `SMTP_PASSWORD`, grava `EMAIL_*` para
  `smtp.dreamhost.com:587` e `SUPPORT_EMAIL=contato@gesttora.com.br` (senha via `envs` do ssh-action, gravada entre
  aspas simples; testada com caracteres especiais no bash 5 e no compose).
- **Testado no droplet em 2026-10-22: portas 25, 465, 587 e 2525 de saída bloqueadas pela DigitalOcean**
  (do Mac, 465 e 587 da DreamHost abrem). Portanto **não criar `SMTP_PASSWORD`** enquanto o bloqueio existir:
  o backend passaria a tentar SMTP e cada envio esperaria o timeout.
- Caminhos: pedir à DigitalOcean a liberação de SMTP (ticket de suporte) ou usar provedor por API HTTP
  (Brevo, Resend ou SES) com o domínio `gesttora.com.br` autenticado (DKIM/SPF do provedor na zona da DreamHost).
- **Decisão (sem clientes ainda): manter tudo na DreamHost** via túnel SSH — serviço `smtp_tunnel` (alias de rede
  `smtp.dreamhost.com`), chave em `/opt/assapp-smtp`, usuário `gesttora@pdx1-shared-a1-07.dreamhost.com`.
  Ensaio no droplet: STARTTLS com certificado verificado e AUTH oferecido. Cota interna `EMAIL_LIMITE_POR_HORA=70`
  (DreamHost bloqueia acima de 100/hora). Brevo documentada como próxima etapa em `DEPLOY_DIGITALOCEAN.md`.
- Tenant `abciber` tinha e-mails de demonstração em domínios reais (abciber.org.br, usp.br, unifesp.br,
  pucsp.edu.br, unicamp.br — todos com MX ativo): com e-mail ligado, sairiam 4 lembretes de anuidade no primeiro dia.
  Trocados em produção, staging e local (Membro + User, em transação) e no `init_sistema_tenant.sh` para
  `@example.org`. **Logins de demonstração:** `diretoria@abciber.example.org` / `abciber123` e
  `ana.silva@example.org` / `associado123`.

### verify-staging travado por commit só de docs

- **Sintoma:** o "Deploy to Production" de `9b6cb19` ficou em "Aguardar staging OK" com `Tentativa n/90: []`.
- **Causa:** o job procurava um run de staging com o SHA exato da `main`; `9b6cb19` só alterava `docs/`, que está
  em `paths-ignore` e não dispara staging. O código (`39ae19e`) tinha passado no staging.
- **Contorno:** cancelar e disparar **Run workflow** (`workflow_dispatch` pula o `verify-staging`). **Re-run** de
  uma execução de push repete o evento e trava de novo.
- **Correção (`34b4425`, em produção com `569d154`):** o job localiza o último commit com código (mesmos
  `paths-ignore` do staging) e aceita staging bem-sucedido dele ou de qualquer commit só de docs posterior.
  Espera se houver staging em andamento; bloqueia se todos falharam ou foram cancelados.

### Pendências

- Confirmar propagação: `dig +short gesttora.com.br NS` (DreamHost) e `curl http://gesttora.com.br/health/`.
- E-mail de saída (ver acima). DMARC (`_dmarc`, `p=none` para começar) a criar na DreamHost.
- HTTPS (seção 9) — também liga o webhook automático de PagBank/Mercado Pago, que exige URL HTTPS.
