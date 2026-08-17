# Fluxo de trabalho Git — AssApp

**Última atualização:** 2026-07-19  
**Padrão:** idêntico ao WellSaaS (`docs/guias/GIT_WORKFLOW.md`)

---

## 1. Branches e remotos

| Branch local | Remoto (origin) | CI disparado | Ambiente |
|-------------|------------------|--------------|----------|
| `orb` | `orb` (opcional) | nenhum | Desenvolvimento Mac / OrbStack |
| `develop` | `develop` | `deploy-staging.yml` | Staging (porta 8080) |
| `main` | `main` | `deploy-production.yml` | **Produção** (porta 80) |

---

## 2. Quando cada Action dispara

| O que você faz | Action |
|----------------|--------|
| `git push origin develop` | Deploy to Staging |
| `git push origin main` | Deploy to Production |

**Importante:** produção só dispara com push em `main`. Push em `develop` não publica produção.

---

## 3. Fluxo adotado: push sequencial + gate no CI

Staging e produção rodam no **mesmo droplet DigitalOcean**. Deploys SSH simultâneos causam race condition.

Os workflows usam:

```yaml
concurrency:
  group: deploy-server
  cancel-in-progress: false
```

**Gate automático (desde 2026-08):** em push para `main`, o job `verify-staging` em `deploy-production.yml`:

1. Confirma que o commit existe em `origin/develop`
2. Aguarda o workflow **Deploy to Staging** concluir com **success** no mesmo SHA
3. Só então build + deploy de produção prosseguem

Assim, mesmo que `develop` e `main` sejam pushados juntos, **produção espera staging**.

Ainda assim, siga o fluxo manual: **push `develop` → validar `:8080` → push `main`** (`docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md`).

---

## 4. Fluxo do dia a dia

### Passo 1 — Trabalhar em `orb`

```bash
git checkout orb
# ... alterações e commits ...
git push origin orb
```

### Passo 2 — Staging

```bash
git checkout develop
git pull origin develop
git merge orb
git push origin develop
```

⏳ Aguardar Actions de staging. Validar health e fluxos críticos.

### Passo 3 — Produção

```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

⏳ Aguardar Actions de produção. Validar ambiente.

---

## 5. Resumo visual

```
orb (local Mac)
  │
  │ merge / push
  ▼
origin/develop ──► deploy-staging.yml ──► Staging (:8080)
                          │
                    [verificar OK]
                          │
  git push origin main    │
  ▼                       │
origin/main ──────────────► deploy-production.yml ──► Produção (:80)
```

---

## 6. Referências

- `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`
- `docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md`
- `docs/guias/DEPLOY_DIGITALOCEAN.md`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`
