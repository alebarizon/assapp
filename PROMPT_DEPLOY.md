# Prompt de Deploy Completo — AssApp

Use este prompt quando as alterações estiverem prontas e testadas localmente na branch `orb`.

Atualizado em **2026-10-22** (HTTPS: nginx do host na frente da produção) — adaptado do padrão WellSaaS para o pipeline AssApp: git no droplet, migrations no startup, gate automático de staging).

---

## Prompt Completo

```
Estou na branch orb com alterações testadas localmente e prontas para deploy.

Execute o fluxo completo de sincronização e deploy:

1. Pré-check: git branch --show-current (tem que ser orb), git status -sb, git fetch origin
2. Verificar migrations pendentes: docker compose exec backend python manage.py makemigrations --check --dry-run
3. Se houver migrations: gerar e aplicar localmente (makemigrations + migrate_schemas --shared + migrate_schemas) e incluir os arquivos de migration no commit
4. Validar o build antes de subir (o CI quebra com erro de TypeScript): docker compose exec -T frontend npm run build (o Mac não tem node_modules no host). Rodar os testes dos apps alterados: docker compose exec -T backend pytest <app>
5. Consolidar commits na orb (só arquivos do lote) → git push origin orb
6. Sincronizar orb → develop → git push origin develop (dispara "Deploy to Staging")
7. ESPERAR o Actions de staging terminar (gh run watch). Só então:
   - curl http://159.203.183.184:8080/health/ (staging)
   - curl https://gesttora.com.br/health/ (produção — tem que continuar healthy)
   Checar no instante do git push é cedo demais: o SSH no droplet ainda não rodou.
8. Se staging falhar: ler o log do Actions + docker logs assapp_backend_staging. Migration quebrada aparece aqui. NÃO seguir para main.
9. Se a produção cair durante o staging: recuperar PRODUÇÃO na hora. Não empilhar outro push.
10. AGUARDAR minha confirmação (staging OK + produção no ar)
11. Após minha confirmação: develop → main → git push origin main (o job verify-staging confere o mesmo SHA em develop)
12. Esperar "Deploy to Production" terminar e checar curl https://gesttora.com.br/health/
13. Sincronizar todas as branches locais (develop, main, orb)
14. Voltar para branch orb

Regras obrigatórias (produção):

- O droplet faz git fetch + git reset --hard origin/<branch> em /opt/assapp a cada deploy. Qualquer edição manual de arquivo versionado no servidor é perdida — toda correção passa pelo repo.
- NUNCA rodar git clean no droplet: .env.staging e .env.production não estão no .gitignore (são untracked) e seriam apagados.
- Abortar se faltar .env.production ou o volume assapp_postgres_data_prod. O workflow recria .env a partir do env.production.example com senha nova de banco — isso não bate com o volume existente e o backend não sobe.
- NÃO apagar dados: nunca docker volume rm, compose down -v, system prune --volumes, rm -rf /opt/assapp.
- Migrations rodam no startup do backend (migrate_schemas --shared → migrate_schemas → gunicorn). Migration quebrada = backend em loop de restart = 502. Não rodar migrations manualmente após deploy, só na recuperação.
- Staging e produção compartilham o droplet e a fila concurrency "deploy-server". Projetos Compose isolados: assapp_staging (:8080) e assapp_prod (127.0.0.1:8081). As portas públicas 80/443 são do nginx do HOST (systemd, TLS Let's Encrypt), que repassa para 8081. NUNCA rodar docker compose down sem COMPOSE_PROJECT_NAME, docker container prune / system prune no host, nem parar o nginx do host ou matar quem escuta em 80/443/8081. `docker image prune -f` (sem `-a`) é permitido: o deploy.sh já roda ao final.
- Ao acompanhar o deploy de produção, checar `curl https://gesttora.com.br/health/` a cada poucos minutos, não só o container novo: o deploy para a stack antes de subir a nova (502 por ~1–2 min durante a troca é esperado).
- Não empilhar push develop e main ao mesmo tempo: esperar staging terminar e validar antes do push main.
- Só commitar o que é do lote. Não incluir .env, .env.staging, .env.production, relatórios .md soltos nem arquivos de outro trabalho em andamento. Se o git status tiver coisa ambígua, perguntar antes.
- Se o login mostrar erro, checar /health/ PRIMEIRO. Conexão recusada = nginx do host fora (systemctl status nginx). HTML 502 = stack prod ou backend fora: no droplet, curl 127.0.0.1:8081/health/ recusado = containers *_prod fora; 502 = backend (ver docker logs). Nenhum é senha.

Consulte:
@docs/guias/GIT_WORKFLOW.md
@docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md
@docs/guias/DEPLOY_DIGITALOCEAN.md

Execute passo a passo, pausando antes do deploy de produção para eu confirmar staging e produção.
```

---

## Prompt Curto

```
Deploy completo: orb testada → develop (Actions) → checar :8080 e https://gesttora.com.br DEPOIS do SSH → [pausa] → produção

Consulte:
@docs/guias/GIT_WORKFLOW.md
@docs/guias/DEPLOY_DIGITALOCEAN.md

Droplet faz git reset --hard: nada de edição manual nem git clean (.env.* são untracked).
Migrations rodam no startup do backend: makemigrations --check antes; migration quebrada = 502.
Faltou .env.production ou volume assapp_postgres_data_prod = abortar. Volume nunca se apaga.
https recusado = nginx do host fora. 502 = stack prod (127.0.0.1:8081) ou backend fora. Nenhum é senha.

Execute: migrations (se houver) → npm run build + pytest → commits → push develop → esperar Actions → curl :8080 e https /health/ → [pausa] → push main → curl https → sync
```

---

## Workflow

1. Desenvolver na branch `orb` (`./scripts/up-orb.sh`)
2. Testar localmente (frontend http://localhost:5174 · backend http://localhost:8001)
3. Copiar e colar o prompt acima no Cursor
4. Aguardar o Cursor executar até o push em `develop`
5. Esperar o Actions "Deploy to Staging" **terminar** (build → Docker Hub → SSH → `deploy.sh staging`). Aí sim checar `:8080/health/` e `https://gesttora.com.br/health/`
6. Validar no staging (http://159.203.183.184:8080) as telas do lote e confirmar que a produção continua no ar
7. Após confirmação: push `origin main`
8. Aguardar "Deploy to Production" (o job `verify-staging` espera o staging do mesmo SHA)
9. Validar produção (https://gesttora.com.br)

Alterar só `*.md` / `docs/` / `.github/*.md` **não** dispara os workflows (`paths-ignore`). Mudança em backend, frontend, compose, `scripts/`, `nginx/` ou `.github/workflows/` dispara.

---

## Como o deploy funciona (não quebrar)

1. GitHub Actions **builda as imagens** (`ubuntu-latest`, amd64) e faz push em `alebarizon/assapp-backend` e `alebarizon/assapp-frontend` (tag `develop` no staging, `latest` na produção).
2. SSH no droplet (`/opt/assapp`): `git fetch` → `git checkout <branch>` → `git reset --hard origin/<branch>`. Arquivos untracked (`.env.staging`, `.env.production`) e volumes Docker ficam.
3. Se o `.env.<ambiente>` não existir, o workflow copia do `env.<ambiente>.example` e gera `SECRET_KEY` e senha de banco novas. Em ambiente com volume existente isso **quebra** a conexão com o Postgres.
4. `scripts/deploy.sh <ambiente>`: carrega o `.env`, faz `docker pull` **antes** de parar qualquer coisa (se o pull falhar, a versão anterior continua no ar), para só o projeto daquele ambiente (`assapp_prod` ou `assapp_staging`), libera só a porta do ambiente (8081 ou 8080), `up -d`, espera `/health/` por até 2 minutos e, com health OK, roda `docker image prune -f` (só imagens sem tag e sem container — cada deploy deixa ~1 GB de imagem antiga; em out/2026 o disco encheu e o pull falhou).
5. O backend, ao subir, roda `wait_for_db` → `migrate_schemas --shared` → `migrate_schemas` → `collectstatic` → `gunicorn`. Health OK = migrations aplicadas.
6. Em push para `main`, o job `verify-staging` exige que o SHA esteja em `origin/develop` e que o "Deploy to Staging" tenha concluído com sucesso para o último commit com código (ou para um commit só de docs posterior a ele, já que esses não disparam staging). Timeout 45 min. O **Run workflow** manual pula essa verificação; o **Re-run** de uma execução de push não pula.

Logs bons no Actions:

- `✅ Commit presente em origin/develop` / `✅ Staging validado — produção pode continuar`
- `Pull alebarizon/assapp-backend:<tag>`
- `✅ Health OK — AssApp <ambiente> no ar (porta 8081|8080)`

Logs ruins (parar e investigar, não insistir no login):

- `Health ainda falhou — logs recentes do backend` (ler o trecho: geralmente migration ou variável de ambiente)
- `Arquivo .env.<ambiente> não encontrado`
- `build: encontrado em docker-compose.*.yml` (staging/prod são pull-only)
- `❌ Este commit não está em origin/develop` (pulou o staging)
- `/health/` = HTML 502 · `curl https://gesttora.com.br` = conexão recusada (nginx do host)
- `no space left on device` no pull (checar `df -h /` e `docker system df`; liberar com `docker image prune -f`, nunca com `system prune`/`volume rm`)

---

## Conferência rápida

```bash
curl -sS -m 10 https://gesttora.com.br/health/
curl -sS -m 10 http://159.203.183.184:8080/health/
# Esperado: {"status": "healthy", "message": "AssApp API is running"}
# Produção recusada (exit 7) = nginx do host fora — systemctl start nginx.
# Staging recusado = stack staging fora — subir de novo.
# HTML 502 na produção = stack prod ou backend fora — no droplet: curl 127.0.0.1:8081/health/
#   (recusado = containers *_prod fora; 502 = backend, ler docker logs).

# No servidor, depois de um deploy:
ssh root@159.203.183.184
cd /opt/assapp && git log -1 --oneline   # tem que bater com o SHA do Actions
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

---

## Restore se produção cair com 502 (não apaga banco)

502 = nginx no ar, backend fora. No AssApp a causa mais comum é migration falhando no startup.

```bash
ssh root@159.203.183.184
cd /opt/assapp
docker logs assapp_backend_prod --tail 100
```

Se for migration:

```bash
docker exec assapp_backend_prod python manage.py migrate_schemas --shared --noinput
docker exec assapp_backend_prod python manage.py migrate_schemas --noinput
COMPOSE_PROJECT_NAME=assapp_prod docker compose -f docker-compose.prod.yml --env-file .env.production restart backend
sleep 30
curl -sS -m 10 http://127.0.0.1:8081/health/
```

Se a migration em si estiver errada: corrigir na `orb`, passar por `develop` e só depois `main`. Não editar migration no servidor (o próximo `git reset --hard` apaga).

**Ordem obrigatória:** `--shared` primeiro (schema `public`), depois tenants.

---

## Restore se a produção recusar conexão

**Site recusa conexão** (`https://gesttora.com.br` exit 7): é o nginx do host.

```bash
ssh root@159.203.183.184 'nginx -t && systemctl restart nginx && systemctl status nginx --no-pager | head -3'
```

**Site dá 502 e `curl 127.0.0.1:8081/health/` no droplet recusa:** os containers `*_prod` pararam ou foram removidos. O volume e o `.env.production` devem continuar no servidor.

```bash
cd /opt/assapp
docker volume inspect assapp_postgres_data_prod >/dev/null || { echo ABORT: volume; exit 1; }
test -f .env.production || { echo ABORT: env; exit 1; }

export COMPOSE_PROJECT_NAME=assapp_prod COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 IMAGE_TAG=latest
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
# Se as imagens não existirem no host: docker pull alebarizon/assapp-backend:latest e alebarizon/assapp-frontend:latest, depois up de novo (sem -v).

sleep 30
curl -sS -m 10 http://127.0.0.1:8081/health/
```

Alternativa: `./scripts/deploy.sh production` dentro de `/opt/assapp` (faz pull + up + espera health).

Nunca `down -v`, `volume rm`, `system prune --volumes`, `git clean`. Alternativa sem SSH: re-executar o "Deploy to Production" do SHA já validado via `workflow_dispatch` — só se a stack prod já estiver fora e o usuário pedir recuperar produção.

---

## Validações depois do push em `develop`

Antes de pedir confirmação para ir a `main`:

- [ ] GitHub Actions "Deploy to Staging" **terminou** com sucesso. Não vale o curl feito no instante do `git push`.
- [ ] `curl http://159.203.183.184:8080/health/` → JSON healthy
- [ ] Login no staging (tenant `abciber`) e telas do lote funcionando
- [ ] `curl https://gesttora.com.br/health/` → produção **continua** healthy
- [ ] Não empilhar outro `push develop` enquanto staging ou produção estiverem fora

---

## Validações Produção

- [ ] GitHub Actions "Deploy to Production" terminou (incluindo o job `verify-staging`)
- [ ] `curl https://gesttora.com.br/health/` → JSON healthy (recusada = nginx do host; 502 = stack prod ou backend/migration; não insistir no login)
- [ ] Login em https://gesttora.com.br/login
- [ ] Funcionalidade visível para o usuário

---

**Última atualização:** 2026-10-22
