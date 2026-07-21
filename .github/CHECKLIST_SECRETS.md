# Checklist — Secrets GitHub Actions (AssApp)

**URL:** https://github.com/alebarizon/assapp/settings/secrets/actions  
**Usar:** **Repository secrets** (não Environment)

**Estado:** ✅ configurados e validados (deploy staging OK em 2026-07-20)

---

## Repository secrets (obrigatórios)

- [x] `DOCKER_USERNAME` → `alebarizon`
- [x] `DOCKER_PASSWORD` → Access Token Docker Hub (Read & Write)
- [x] `DO_HOST` → `159.203.183.184`
- [x] `DO_STAGING_HOST` → `159.203.183.184`
- [x] `DO_USER` → `root` (ou `deploy`)
- [x] `DO_SSH_KEY` → chave privada (`cat ~/.ssh/id_ed25519`)

## Opcional

- [ ] `G_TOKEN_DEPLOY` — só se o repo for privado

---

## Não confundir

| Token | Secret |
|-------|--------|
| Docker Hub Access Token | `DOCKER_PASSWORD` |
| GitHub PAT (`ghp_…`) | `G_TOKEN_DEPLOY` |

---

## Branches → deploy

| Branch | Porta |
|--------|-------|
| `develop` | 8080 (staging) |
| `main` | 80 (produção) |
| `orb` | nenhum |

---

## Documentação

- Changelog: `docs/changelog/CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`
- Deploy: `docs/guias/DEPLOY_DIGITALOCEAN.md`
