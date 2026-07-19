# Fluxo de trabalho Git — AssApp

**Última atualização:** 2026-07-19  
**Padrão:** adaptado do WellSaaS (`docs/guias/GIT_WORKFLOW.md`)

---

## 1. Branches e remotos

| Branch local | Remoto (origin) | CI disparado | Ambiente |
|-------------|------------------|--------------|----------|
| `orb` | `orb` (opcional) | nenhum | Desenvolvimento Mac / OrbStack |
| `develop` | `develop` | `deploy-staging.yml` | Staging (porta 8080) |
| `assapp` | `assapp` | `deploy-production.yml` | **Produção** (porta 80) |

> No WellSaaS a produção é `main`. No AssApp a produção é **`assapp`**.

---

## 2. Quando cada Action dispara

| O que você faz | Action |
|----------------|--------|
| `git push origin develop` | Deploy to Staging |
| `git push origin assapp` | Deploy to Production |

**Importante:** produção só dispara com push em `assapp`. Push em `develop` não publica produção.

---

## 3. Fluxo adotado: push sequencial (sem PR obrigatório)

Staging e produção podem rodar no **mesmo droplet DigitalOcean**. Deploys simultâneos causam race condition.

Os workflows usam:

```yaml
concurrency:
  group: deploy-server
  cancel-in-progress: false
```

Ainda assim: **sempre valide staging antes de promover para `assapp`**.

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
git checkout assapp
git pull origin assapp
git merge develop
git push origin assapp
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
  git push origin assapp  │
  ▼                       │
origin/assapp ────────────► deploy-production.yml ──► Produção (:80)
```

---

## 6. Referências

- `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`
- `docs/guias/TUTORIAL_MIGRACAO_ORB_DEVELOP_ASSAPP.md`
- `docs/guias/DEPLOY_DIGITALOCEAN.md`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`
