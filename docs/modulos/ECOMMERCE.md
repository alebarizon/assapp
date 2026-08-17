# Módulo E-commerce — Gesttora

> **Status:** MVP (2026-08) — motor adaptado do WellSaaS  
> **App Django:** `backend/ecommerce/` (TENANT)

---

## Conceito

Catálogo unificado de ofertas da associação. Cada item tem **tipo** e, após pagamento, dispara **fulfillment** no domínio existente:

| Tipo | Fulfillment |
|------|-------------|
| `anuidade` | `membros.Anuidade` paga + espelho `finance` |
| `inscricao` | `eventos.InscricaoEvento` confirmada + espelho `finance` |
| `curso` / `material` / `digital` | Pedido concluído; entrega manual/futura |

Comprador: **Membro** (associado com user vinculado).

---

## API REST

| Endpoint | Quem | Descrição |
|----------|------|-----------|
| `GET/POST /api/ecommerce/catalog/` | Diretoria / associado (lista ativos) | CRUD catálogo |
| `GET /api/ecommerce/catalog/loja/` | Associado | Vitrine ativa |
| `GET /api/ecommerce/orders/` | Diretoria / próprio associado | Pedidos |
| `POST /api/ecommerce/orders/{id}/confirmar-pagamento/` | Diretoria | Pagamento manual |
| `GET /api/ecommerce/cart/` | Associado | Carrinho |
| `POST /api/ecommerce/cart/add/` | Associado | Adicionar item |
| `PATCH /api/ecommerce/cart/update/{item_id}/` | Associado | Quantidade |
| `DELETE /api/ecommerce/cart/remove/{item_id}/` | Associado | Remover |
| `POST /api/ecommerce/cart/checkout/` | Associado | Finalizar |
| `GET /api/ecommerce/resumo/` | Diretoria | KPIs |
| `GET /api/ecommerce/public/catalog/?schema=` | **Público** | Vitrine anuidades (site Associe-se) |

### Checkout

- `payment_method: simulated` — paga e cumpre na hora (dev/demo)
- `payment_method: manual` — pedido `pending`; diretoria confirma depois

---

## Frontend

| Página | Rota | Público |
|--------|------|---------|
| `EcommerceCatalog.tsx` | `/app/ecommerce/catalog` | Diretoria |
| `EcommerceOrders.tsx` | `/app/ecommerce/orders` | Diretoria |
| `PortalLoja.tsx` | `/app/portal/loja` | Associado |
| `PortalCarrinho.tsx` | `/app/portal/carrinho` | Associado |

---

## Migrations

```bash
docker compose exec backend python manage.py migrate_schemas
```

---

## Pendente

- Stripe real (`payments/` + webhook)
- Sincronização automática catálogo ↔ lote de anuidades
- **Associe-se no site público** — bloco home + página `/site/associe-se` → catálogo (ver [`WEBSITE_CMS_TENANT.md`](WEBSITE_CMS_TENANT.md))
