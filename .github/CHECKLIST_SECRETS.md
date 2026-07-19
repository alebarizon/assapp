# Checklist — Secrets GitHub Actions (AssApp)

Configure em: **Settings → Secrets and variables → Actions**

## Obrigatórios para build

- [ ] `DOCKER_USERNAME` — usuário Docker Hub
- [ ] `DOCKER_PASSWORD` — token/senha Docker Hub

## Obrigatórios para deploy no droplet

- [ ] `DO_HOST` — host/IP produção
- [ ] `DO_STAGING_HOST` — host/IP staging (pode ser igual a `DO_HOST`)
- [ ] `DO_USER` — usuário SSH
- [ ] `DO_SSH_KEY` — chave privada SSH (conteúdo completo, incluindo `BEGIN`/`END`)
- [ ] `G_TOKEN_DEPLOY` — GitHub PAT classic com scope `repo` (repositório privado)

## Branches que disparam deploy

| Secret / branch | Workflow |
|-----------------|----------|
| Push em `develop` | `deploy-staging.yml` |
| Push em `main` | `deploy-production.yml` |

## Após configurar

1. Rodar `workflow_dispatch` em Staging uma vez.
2. Validar health em `:8080`.
3. Só então promover para `main`.

Documentação: `docs/guias/DEPLOY_DIGITALOCEAN.md`
