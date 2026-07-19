# Módulo Membros — Documentação Técnica

> **Sprint 4** — Gestão de associados, filiações e anuidades  
> **Compliance:** LGPD (consentimento obrigatório), CPF validado

---

## Modelos

| Modelo | Descrição |
|--------|-----------|
| `Membro` | Dados do associado (nome, email, CPF, Lattes, ORCID) |
| `Filiacao` | Histórico de filiação vinculado a mandato |
| `Anuidade` | Cobrança anual por filiação |

## Valores padrão de anuidade

| Tipo | Valor |
|------|-------|
| Efetivo | R$ 80,00 |
| Estudante | R$ 40,00 |
| Honorário | Isento |
| Institucional | R$ 200,00 |

## API REST

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/membros/membros/resumo/` | KPIs do quadro |
| `GET/POST /api/membros/membros/` | Lista / cria membro + filiação |
| `GET /api/membros/membros/{id}/` | Detalhe com histórico |
| `POST /api/membros/anuidades/gerar_lote/` | Gera anuidades do ano |
| `POST /api/membros/anuidades/atualizar_vencidas/` | Marca inadimplentes |
| `POST /api/membros/anuidades/{id}/registrar_pagamento/` | Registra pagamento |

## Automação

1. **Gerar lote** — cria anuidades para todas filiações ativas/inadimplentes sem cobrança no ano
2. **Atualizar vencidas** — anuidades pendentes após vencimento → `vencida`; filiação → `inadimplente`
3. **Registrar pagamento** — anuidade `paga`; reativa filiação inadimplente

## Frontend

| Página | Rota |
|--------|------|
| `Membros.tsx` | `/app/membros` |
| `MembroDetail.tsx` | `/app/membros/:id` |

UI: padrão WellSaaS (`dashboard-*`, KPIs `stats-grid`) — [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

## Pendente

- Stripe real no pagamento de anuidades (hoje: registro manual + espelho em `finance`)
- Convite SMTP para associados (User criado a partir do Membro)

## Ponte User ↔ Membro

| Campo / API | Descrição |
|-------------|-----------|
| `Membro.user` | OneToOne opcional → `User` |
| `POST /api/membros/membros/{id}/vincular_user/` | `{ user_id }` ou `{ email }` |
| `POST /api/membros/membros/{id}/desvincular_user/` | Remove vínculo |
| `GET /api/auth/me/` | `membro_id`, `membro_nome` |
| `GET /api/membros/meu/` | Perfil do associado autenticado |
| `GET /api/membros/meu/anuidades/` | Anuidades próprias (read-only) |

### Portal associado (FE)

| Rota | Função |
|------|--------|
| `/app/portal` | Home do associado |
| `/app/portal/perfil` | Perfil + anuidades |
| `/app/portal/documentos` | Docs `meus/` |

Demo: `ana.silva@usp.br` / `associado123`.

Documentos `meus/` e submissões H3 resolvem o associado via FK (com fallback por e-mail).

Ver: [`CHANGELOG_USER_MEMBRO_2026_07.md`](../changelog/CHANGELOG_USER_MEMBRO_2026_07.md) · [`CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](../changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md)

---

**Última atualização:** 2026-07-15
