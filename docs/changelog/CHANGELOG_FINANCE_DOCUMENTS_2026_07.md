# Changelog — Finance OSC + Documents (2026-07)

> Consolidado do dia: [`CHANGELOG_2026_07_14.md`](CHANGELOG_2026_07_14.md)

## Entregue

### Backend `finance`
- Model `Transaction` com categorias OSC (não health)
- API: transactions CRUD, dashboard, monthly-report, send-report-email (503 se SMTP off)
- Espelho idempotente anuidade → Transaction income (`referencia`)
- App em `TENANT_APPS`; parsers Multipart no DRF

### Backend `documents`
- Model `Document` com audience geral/diretoria/membro
- CRUD + download; endpoint `meus/` para associado/board
- Limite de upload ~10MB

### Frontend
- `/app/finance` + nav + deep-link onboarding `revisar_financeiro`
- `/app/documents` + nav

### Snapshot / docs / seed
- `Mandato.criar_snapshot` inclui contagens de anuidades + saldo do mês (finance)
- Docs: `docs/modulos/FINANCE.md`, `DOCUMENTS.md`
- Seed ABCiber: 2 txs + 1 documento demo

## Fora de escopo (esta rodada)

- Stripe checkout/webhooks reais
- adminpanel, CMS/landing, mensagens, support, Google Calendar
