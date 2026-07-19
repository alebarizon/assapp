# Módulo Mandatos — Documentação Técnica

> **Prioridade:** Máxima (core da pesquisa PIPE Fase 1)  
> **Hipóteses:** H1 (modelagem) + H2 (onboarding adaptativo)  
> **App Django:** `backend/mandatos/`

---

## Visão Geral

O módulo Mandatos implementa o ciclo de vida da diretoria de uma associação científica, com transição estruturada entre gestões e preservação ativa de memória institucional via snapshots automáticos.

**1º mandato vs transição:** o mandato inicial nasce no *setup pós-compra* da associação (fase comercial/SaaS). O wizard deste módulo (`OnboardingEtapa` / H2) cobre apenas a **troca de diretoria**. Ver [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md).

---

## Modelos

### Mandato

Ciclo de gestão (~2 anos). Apenas um mandato pode estar `ativo` por tenant.

**Métodos principais:**

| Método | Descrição |
|--------|-----------|
| `get_ativo()` | Retorna mandato ativo |
| `ativar()` | Ativa e encerra outros |
| `iniciar_transicao(mandato_novo)` | Cria transição + snapshot + etapas onboarding |
| `criar_snapshot(tipo)` | H1 — captura estado consolidado |
| `encerrar(observacoes)` | Encerra com snapshot final |

### CargoMandato

Vincula usuário a cargo na diretoria (presidente, tesoureiro, etc.).

### TransicaoMandato

Handoff entre mandatos. Progresso calculado pelas etapas obrigatórias concluídas.

### OnboardingEtapa

Wizard guiado (H2). Etapas padrão definidas em `ETAPAS_ONBOARDING_PADRAO`:

1. Revisar snapshot do mandato anterior
2. Confirmar composição da diretoria
3. Revisar quadro de associados
4. Revisar situação financeira
5. Revisar eventos em andamento (opcional)
6. Revisar decisões institucionais
7. Configurar comunicação (opcional, perfil avançado)

### MandatoSnapshot

JSON auditável com hash SHA-256. Tipos: `encerramento`, `transicao`, `manual`.

**Dados capturados:**
- Metadados do mandato
- Cargos ativos
- Contagem de membros (ativos/inadimplentes)
- Decisões recentes (`ContextoHistorico`)
- Anuidades (pagas / pendentes / vencidas)
- Saldo financeiro do mês corrente (`finance.Transaction`)
- Eventos ativos (`inscricoes_abertas`, `cfp_aberto`, `em_avaliacao`)

---

## API REST (planejada)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/mandatos/` | Lista mandatos |
| POST | `/api/mandatos/` | Cria mandato |
| GET | `/api/mandatos/{id}/` | Detalhe + timeline |
| POST | `/api/mandatos/{id}/ativar/` | Ativa mandato |
| POST | `/api/mandatos/{id}/encerrar/` | Encerra com snapshot |
| POST | `/api/mandatos/{id}/transicao/` | Inicia transição |
| GET | `/api/mandatos/ativo/` | Mandato ativo atual |
| GET | `/api/mandatos/{id}/snapshots/` | Lista snapshots |
| GET | `/api/transicoes/{id}/onboarding/` | Etapas do wizard |
| PATCH | `/api/onboarding/{id}/concluir/` | Marca etapa concluída |

---

## Frontend

| Página | Rota | Status | Função |
|--------|------|--------|--------|
| `Mandatos.tsx` | `/app/mandatos` | ✅ | Lista, criar, iniciar transição |
| `MandatoDetail.tsx` | `/app/mandatos/:id` | ✅ | Cargos + timeline + snapshots |
| `OnboardingWizard.tsx` | `/app/onboarding` | ✅ | Wizard Nova Diretoria (H2) + deep-links |
| `AssociationSetup.tsx` | `/app/setup` | ✅ | **Não é H2** — 1º mandato pós-signup |

UI: classes `dashboard-*` (padrão WellSaaS) — ver [`docs/guias/UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

---

## Fluxo de Transição de Diretoria

```
1. Diretoria eleita → criar Mandato (status: planejado)
2. Definir CargoMandato para cada membro
3. POST /mandatos/{anterior}/transicao/ com mandato_novo_id
   → Snapshot automático do mandato anterior
   → TransicaoMandato criada
   → 7 OnboardingEtapa geradas
4. Nova diretoria completa wizard (modo adaptativo H2)
5. Ao 100% etapas obrigatórias:
   → Mandato novo: ativo
   → Mandato anterior: encerrado
   → TransicaoMandato: concluída
```

---

## Relacionados

| Documento | Conteúdo |
|-----------|----------|
| [`FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Setup vs transição H2 |
| [`AUTH_SIGNUP_SETUP.md`](AUTH_SIGNUP_SETUP.md) | Register + setup API |
| [`CHANGELOG_SPRINT2_MANDATOS_2026_07.md`](../changelog/CHANGELOG_SPRINT2_MANDATOS_2026_07.md) | Sprint 2 |
| [`CHANGELOG_2026_07_14.md`](../changelog/CHANGELOG_2026_07_14.md) | Signup/setup + UI |

---

## Testes de Hipótese H1

Comparar tempo de onboarding ABCiber:
- **Baseline:** planilhas + e-mails (medir em entrevistas)
- **AssApp:** tempo desde login até conclusão do wizard
- **Meta:** redução ≥ 50%

---

**Última atualização:** 2026-07-14
