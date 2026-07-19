# Checklist — Secrets GitHub Actions (AssApp)

**URL:** https://github.com/alebarizon/assapp/settings/secrets/actions  

Clique em **New repository secret** para cada item (Repository secrets, não Environment).

**Droplet:** `159.203.183.184` · Bootstrap já feito · Doc: `docs/guias/DEPLOY_DIGITALOCEAN.md`  
**Changelog:** `docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`

---

## Obrigatórios para build (Docker Hub)

- [ ] `DOCKER_USERNAME` — usuário Docker Hub
- [ ] `DOCKER_PASSWORD` — access token Docker Hub (preferível à senha da conta)

## Obrigatórios para deploy no droplet

- [ ] `DO_HOST` → `159.203.183.184`
- [ ] `DO_STAGING_HOST` → `159.203.183.184` (mesmo servidor)
- [ ] `DO_USER` → `root` (ou `deploy`, se preferir)
- [ ] `DO_SSH_KEY` → chave **privada** completa

```bash
# No Mac — copiar e colar no secret (não compartilhar / não commitar)
cat ~/.ssh/id_ed25519
```

Deve incluir as linhas `BEGIN` e `END`.

## Opcional

- [ ] `G_TOKEN_DEPLOY` — PAT classic com scope `repo`  
  Só necessário se o repositório for privado. AssApp está público → pode omitir por enquanto.

---

## Branches que disparam deploy

| Branch | Workflow |
|--------|----------|
| `develop` | `deploy-staging.yml` → porta 8080 |
| `main` | `deploy-production.yml` → porta 80 |

Push em `orb` **não** dispara deploy.

---

## Após cadastrar os secrets

1. Ainda falta no código: `docker-compose.staging.yml`, `docker-compose.prod.yml`, `scripts/deploy.sh`.
2. Quando existirem: Actions → **Deploy to Staging** → **Run workflow**.
3. Validar `http://159.203.183.184:8080/health/` (quando o stack estiver no ar).
4. Só então promover para `main`.

Documentação: `docs/guias/DEPLOY_DIGITALOCEAN.md`
