# Módulo Pagamentos — Documentação Técnica

> App `payments` (TENANT). Pagamento online de anuidades e de pedidos da loja (inscrições, cursos, materiais).
> Cada associação usa a **própria conta Asaas** — o dinheiro cai direto nela.

---

## Fluxo

```
Associado (portal /app/portal/perfil) → "Pagar" → escolhe Pix / cartão / boleto
  → POST /api/pagamentos/anuidades/{id}/cobrar/  → cria Cobranca no Asaas
  → Pix: QR + copia-e-cola no modal · cartão/boleto: fatura hospedada do Asaas
Asaas → POST /api/pagamentos/webhook/asaas/?schema={tenant}
  → confirmar_cobranca: Cobranca paga → Anuidade paga → lançamento em finance
```

Pedidos da loja: checkout com `payment_method: "online"` cria o pedido pendente; o carrinho abre o mesmo modal
de pagamento e lista os pedidos aguardando pagamento. Na confirmação, `process_order_payment` faz o fulfillment
(inscrição, matrícula, anuidade) e espelha no financeiro. Se o fulfillment falhar (ex.: estoque), a cobrança fica
paga, o pedido continua pendente e o motivo vai para as observações do pedido para a secretaria resolver.

Cartão e boleto passam pela fatura hospedada do Asaas: nenhum dado de cartão trafega pelo sistema.

## Modelos

| Modelo | Descrição |
|--------|-----------|
| `ConfiguracaoPagamento` | Singleton por tenant (`atual()`): chave de API cifrada (Fernet derivado de `SECRET_KEY`), sandbox, ativo, formas aceitas, token do webhook |
| `Cobranca` | Uma tentativa de pagamento: método, provedor, status, `external_id`, URL da fatura, dados do Pix, payload bruto |

Status da cobrança: `pendente` → `paga` / `cancelada` / `falhou`. Ao pagar uma, as demais pendentes da mesma
anuidade são canceladas (localmente e no Asaas, melhor esforço). Gerar de novo com o mesmo método e valor
reaproveita a cobrança aberta.

## API REST (`/api/pagamentos/`)

| Endpoint | Quem | Descrição |
|----------|------|-----------|
| `GET/PUT/PATCH configuracao/` | financeiro TOTAL | Configuração do Asaas (`api_key` só escrita) |
| `POST configuracao/testar/` | financeiro TOTAL | Testa a chave (consulta saldo) |
| `GET disponibilidade/` | autenticado | `{habilitado, simulado, metodos}` para o portal |
| `POST anuidades/{id}/cobrar/` | associado dono | `{metodo}` → cria/reaproveita cobrança |
| `POST pedidos/{id}/cobrar/` | associado dono | Idem para pedido `pending` da loja (vencimento em 3 dias) |
| `GET cobrancas/{id}/` | associado dono | Status (o modal consulta a cada 5 s) |
| `POST cobrancas/{id}/simular-pagamento/` | associado dono | Só com provedor `simulado` |
| `POST webhook/asaas/?schema=` | Asaas (sem login) | Valida header `asaas-access-token` |

A configuração exige nível **TOTAL** em `financeiro` até para leitura, porque expõe o token do webhook.

## Configuração na associação

1. Painel → **Financeiro** → **Pagamento online**.
2. Colar a chave de API (Asaas → Integrações → Chave de API). Começar em **sandbox**.
3. Cadastrar o webhook no Asaas (Integrações → Webhooks) com a URL e o token exibidos; eventos de cobrança, API v3.
4. **Testar conexão**, marcar as formas aceitas e **Oferecer pagamento online no portal**.
5. Validado, desmarcar sandbox e trocar pela chave de produção.

O cliente no Asaas exige CPF ou CNPJ — o associado sem CPF recebe erro pedindo para atualizar o cadastro.

## Modo simulado

`PAGAMENTO_SIMULADO` (variável de ambiente; padrão = `DEBUG`). Quando ligado e não há Asaas ativo,
o portal usa um gateway falso: Pix fictício e botão "Simular pagamento confirmado". Também é a única condição
em que o checkout da loja aceita `payment_method: "simulated"` (pagamento imediato). Útil em dev e demos;
**desligar em produção** (`PAGAMENTO_SIMULADO=False`).

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `payments/gateways.py` | `AsaasGateway`, `SimuladoGateway` |
| `payments/services.py` | `cobrar_anuidade`, `confirmar_cobranca`, `processar_webhook_asaas` |
| `payments/crypto.py` | Cifragem da chave de API |
| `frontend/src/components/pagamentos/PagarAnuidadeModal.tsx` | Modal do associado |
| `frontend/src/components/pagamentos/PagamentoOnlineModal.tsx` | Configuração no Financeiro |

Régua de cobrança por e-mail e linha do tempo: ver [`MEMBROS.md`](MEMBROS.md).

---

**Última atualização:** 2026-10-17
