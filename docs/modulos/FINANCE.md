# Módulo Finance — OSC

> Categorias para associações científicas / terceiro setor. Stripe permanece simulado nesta fatia.

## Modelo

`Transaction`: `description`, `amount`, `type` (`income`|`expense`), `category`, `occurred_at`, FK opcional `mandato`, `referencia` (idempotência).

**Receitas:** anuidade, evento, doacao, patrocinio, outros  
**Despesas:** administrativa, evento, comunicacao, impostos, outros

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /api/finance/transactions/` | CRUD (filtro type, category, datas) |
| `GET /api/finance/dashboard/?month=&year=` | KPIs do período |
| `GET /api/finance/monthly-report/?month=&year=` | Relatório mensal |
| `POST /api/finance/send-report-email/` | HTML + `send_mail` (503 se SMTP falhar) |

Scoping: todas as txs do schema. Escrita: `IsBoardOrAdmin`.

## Integração anuidades

`membros.services.registrar_pagamento` cria Transaction income categoria `anuidade` com `referencia=anuidade:<uuid>` (idempotente).

## Frontend

`/app/finance` — KPIs, lista do mês, CRUD, envio de fechamento. Onboarding H2 `revisar_financeiro` deep-link.
