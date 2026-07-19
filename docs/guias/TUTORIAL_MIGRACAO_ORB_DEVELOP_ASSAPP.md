# Tutorial de Migração — orb → develop → assapp

**Última revisão:** 2026-07-19  
**Objetivo:** Promover código da branch local `orb` para `develop` (staging) e depois `assapp` (produção), com segurança.  
**Padrão:** adaptado do WellSaaS (`TUTORIAL_MIGRACAO_ORB_DEVELOP_MAIN.md`); produção = `assapp` (não `main`).

---

## 1) Quando usar

1. Consolidar commits em `orb`.
2. Publicar em `develop` para validar staging.
3. Publicar em `assapp` só após staging OK.

---

## 2) Regras obrigatórias

- Nunca publicar direto em `assapp` sem passar por `develop`.
- Push sequencial: primeiro `develop`, depois `assapp`.
- Validar workflow de staging antes de produção.
- Não usar `reset --hard` / `push --force` neste fluxo.

---

## 3) Pré-check

```bash
git branch --show-current
git status -sb
git fetch origin
git rev-list --left-right --count origin/develop...orb
git rev-list --left-right --count origin/assapp...orb
```

---

## 4) Consolidar na orb

```bash
git checkout orb
git add <arquivos>
git commit -m "feat(modulo): ..."
git push origin orb
```

---

## 5) Staging (develop)

### Caminho A — merge explícito

```bash
git checkout develop
git pull origin develop
git merge orb
git push origin develop
```

### Caminho B — push direto

```bash
git checkout orb
git pull origin develop
git push origin orb:develop
```

---

## 6) Validar staging

1. Aguardar `Deploy to Staging` no GitHub Actions.
2. Health + fluxos críticos.
3. Só então promover para produção.

---

## 7) Produção (assapp)

```bash
git checkout assapp
git pull origin assapp
git merge develop
git push origin assapp
```

---

## 8) Pós-promoção

```bash
git checkout orb
git pull origin develop

git checkout develop
git pull origin develop

git checkout assapp
git pull origin assapp
```

---

## 9) Erros comuns

| Erro | Prevenção |
|------|-----------|
| Push em `assapp` antes de `develop` | Seguir seções 5 → 6 → 7 |
| Conflito por branch desatualizada | `fetch`/`pull` antes do merge |
| Deploy quebrado por migration | Revisar migrations e validar staging |

---

## 10) Referências

- `docs/guias/ESTRATEGIA_BRANCHES_ORBSTACK.md`
- `docs/guias/GIT_WORKFLOW.md`
- `docs/guias/DEPLOY_DIGITALOCEAN.md`
