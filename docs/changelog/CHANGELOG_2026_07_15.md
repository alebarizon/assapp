# Changelog consolidado — 2026-07-15

> Resumo de todas as alterações do dia (PIPE / ABCiber).  
> Stripe e comercialização SaaS **não** avançaram — ficam por último.

---

## Decisão de produto

Prioridade: fechar lacunas PIPE e hierarquia **Associação → Membro com login**. Pagamento real (Stripe) adiado.

---

## 1. MandatoDetail + Onboarding H2 + Snapshot eventos

Fecha Sprint 2 / hipóteses H1–H2 na UI.

### Backend
- `Mandato.criar_snapshot` inclui `dados.eventos` (status `inscricoes_abertas`, `cfp_aberto`, `em_avaliacao`)
- Serialização JSON do snapshot normalizada (UUID/datetime)

### Frontend
- `/app/mandatos/:id` — cargos, timeline (`memoria?mandato=`), snapshots
- Lista/banner de mandatos com links para o detalhe
- Onboarding H2 deep-links:
  - `revisar_snapshot` → mandato anterior
  - `revisar_membros` → `/app/membros`
  - `revisar_financeiro` → `/app/finance`
  - `revisar_eventos` → `/app/eventos`
  - `revisar_decisoes` → `/app/memoria`

**Detalhe:** [`CHANGELOG_MANDATO_DETAIL_H2_2026_07.md`](CHANGELOG_MANDATO_DETAIL_H2_2026_07.md) · [`MANDATOS.md`](../modulos/MANDATOS.md)

---

## 2. Ponte User ↔ Membro

Elo formal entre login (`User`) e quadro associativo (`Membro`).

### Backend
- `Membro.user` OneToOne → User (`related_name=membro_perfil`) — migration `membros.0002_membro_user_link`
- Services: `vincular_user`, `desvincular_user`, `resolver_membro_do_user` (FK + fallback e-mail com auto-link)
- `POST /api/membros/membros/{id}/vincular_user/` · `desvincular_user/`
- `GET /api/auth/me/` → `membro_id`, `membro_nome`
- Documents `meus/` e eventos H3 usam o resolver

### Frontend
- `MembroDetail`: badge Vinculado / Sem usuário + ações vincular/desvincular

### Seed
- Diretoria ABCiber vinculada a Membro com o mesmo e-mail

**Detalhe:** [`CHANGELOG_USER_MEMBRO_2026_07.md`](CHANGELOG_USER_MEMBRO_2026_07.md) · [`MEMBROS.md`](../modulos/MEMBROS.md)

---

## 3. Portal mínimo do associado

User `role=member` + vínculo Membro.

### Backend
- `GET /api/membros/meu/` — perfil completo do associado
- `GET /api/membros/meu/anuidades/` — anuidades read-only
- Reutiliza `GET /api/documents/meus/` (+ download)

### Frontend
- Rotas: `/app/portal`, `/app/portal/perfil`, `/app/portal/documentos`
- Nav e login por role (`utils/roles.ts`)
- Associado fora do portal → redirect `/app/portal`
- Diretoria mantém painel completo

### Seed / demo
| Conta | Senha | Papel |
|-------|-------|--------|
| `diretoria@abciber.org.br` | `abciber123` | Diretoria |
| `ana.silva@usp.br` | `associado123` | Associado (portal) |

- Documento pessoal demo: “Comprovante de filiação (Ana)”

**Detalhe:** [`CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](CHANGELOG_PORTAL_ASSOCIADO_2026_07.md) · [`DOCUMENTS.md`](../modulos/DOCUMENTS.md)

---

## 4. Validação ABCiber

- Smoke técnico backend (APIs / snapshot / onboarding) — OK
- Passada na UI pela diretoria — OK (reportado pelo usuário)

---

## 5. Fora de escopo (ainda pendente)

| Item | Status |
|------|--------|
| Stripe real / AdminPlan / webhooks | ❌ (por último) |
| `adminpanel`, landing SaaS, website CMS | ❌ |
| Convite SMTP / senha provisória na UI | ❌ (próximo candidato natural) |
| JWT com claim `tenant_schema` | ❌ |
| Integrations (Calendar / NF) | ❌ |

---

## Arquivos / docs de referência atualizados

| Documento | Papel |
|-----------|--------|
| Este arquivo | Consolidado do dia |
| [`STATUS_SPRINTS_FASE1.md`](../referencia/STATUS_SPRINTS_FASE1.md) | Status sprints + pós-5 |
| [`ANALISE_VINCULOS_MODULOS_E_TENANCY.md`](../referencia/ANALISE_VINCULOS_MODULOS_E_TENANCY.md) | Gaps User↔Membro / snapshot fechados |
| [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Operação + H2 |
| [`README.md`](../../README.md) / [`cursor-readme.md`](../../cursor-readme.md) | Índices e roadmap |

---

## Como verificar rapidamente

```text
1. Login diretoria → Mandatos → detalhe (cargos/timeline/snapshots)
2. Onboarding (se transição ativa) → links para módulos
3. Membros → detalhe → vínculo User
4. Login ana.silva@usp.br / associado123 → /app/portal (perfil + docs)
5. Associado em /app/membros → redirect portal
```

---

**Próximo passo sugerido (sem Stripe):** convite / criação de User a partir do Membro (senha na UI), ou JWT `tenant_schema`.
