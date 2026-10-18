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
| `curso` | Matrícula em `courses.CourseEnrollment` dos cursos vinculados ao item (ver [`COURSES.md`](COURSES.md)) |
| `material` / `digital` | Pedido concluído; entrega manual/futura |

Comprador: **Membro** (associado com user vinculado).

### Preço de sócio adimplente

`CatalogItem.member_price` (opcional, ≤ `price`, não se aplica a anuidade) é o preço para quem está **em dia**:
filiação ativa ou honorária e nenhuma anuidade em atraso (`membros.services.membro_adimplente`, que já considera
anuidade pendente com vencimento passado mesmo antes do cron marcá-la como vencida).

- Vitrine do associado devolve `preco_final` (o preço que ele paga); para a diretoria vem `null`.
- Carrinho devolve `total`, `total_cheio` e `adimplente`; o portal mostra a economia ou quanto o inadimplente economizaria.
- No checkout o preço é recalculado no servidor: `OrderItem.price_at_purchase` = preço pago, `list_price` = preço cheio.
- Cursos: `POST /api/courses/{id}/create-catalog-item/` aceita `member_price`; o site público mostra "Associado em dia paga…".

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

- `payment_method: online` — pedido `pending` pago pelo associado via Asaas (ver [`PAGAMENTOS.md`](PAGAMENTOS.md))
- `payment_method: manual` (padrão) — pedido `pending`; diretoria confirma depois
- `payment_method: simulated` — paga e cumpre na hora; **só com `PAGAMENTO_SIMULADO`** (dev/demo)

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

- Preço de sócio por tipo de filiação (ex.: estudante) e cupons
- Sincronização automática catálogo ↔ lote de anuidades
- **Associe-se no site público** — bloco home + página `/site/associe-se` → catálogo (ver [`WEBSITE_CMS_TENANT.md`](WEBSITE_CMS_TENANT.md))

---

**Última atualização:** 2026-10-17
