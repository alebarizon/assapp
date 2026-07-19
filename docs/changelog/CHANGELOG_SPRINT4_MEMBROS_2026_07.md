# Sprint 4 — Membros + Anuidades

**Data:** 2026-07-13

## Entregas

### Backend `membros/`
- API CRUD Membros com criação automática de filiação
- API Filiações e Anuidades
- Serviços: `gerar_anuidades_ano`, `atualizar_anuidades_vencidas`, `registrar_pagamento`
- KPIs: `/api/membros/membros/resumo/`
- LGPD: consentimento obrigatório no cadastro

### Frontend
- `Membros.tsx` — lista, KPIs, filtros, cadastro, ações em lote
- `MembroDetail.tsx` — histórico de filiações e anuidades, registrar pagamento

### Demo ABCiber
- 4 associados demo (1 inadimplente) no `init_sistema_tenant.sh`

## Financeiro

Anuidades cobrem cobrança do associado. Em **2026-07-14** o app `finance/` OSC foi integrado: pagamento registrado espelha `Transaction` income categoria `anuidade` (idempotente). Detalhe: [`CHANGELOG_FINANCE_DOCUMENTS_2026_07.md`](CHANGELOG_FINANCE_DOCUMENTS_2026_07.md).
