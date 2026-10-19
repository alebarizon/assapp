# Módulo Pagamentos — Documentação Técnica

> App `payments` (TENANT). Pagamento online de anuidades e de pedidos da loja (inscrições, cursos, materiais).
> Cada associação usa a **própria conta** no gateway escolhido — **Asaas**, **PagBank** ou **Mercado Pago** —
> e o dinheiro cai direto nela. Um gateway ativo por vez.

---

## Fluxo

```
Associado (portal /app/portal/perfil) → "Pagar" → escolhe Pix / cartão / boleto
  → POST /api/pagamentos/anuidades/{id}/cobrar/  → cria Cobranca no gateway
  → Pix: QR + copia-e-cola no modal · cartão/boleto: página hospedada do gateway
Gateway → POST /api/pagamentos/webhook/{provedor}/?schema={tenant}
  → confirmar_cobranca: Cobranca paga → Anuidade paga → lançamento em finance
Sem webhook (ex.: site sem HTTPS) → consulta ativa ao gateway (ver "Sincronização")
```

Pedidos da loja: checkout com `payment_method: "online"` cria o pedido pendente; o carrinho abre o mesmo modal
de pagamento e lista os pedidos aguardando pagamento. Na confirmação, `process_order_payment` faz o fulfillment
(inscrição, matrícula, anuidade) e espelha no financeiro. Se o fulfillment falhar (ex.: estoque), a cobrança fica
paga, o pedido continua pendente e o motivo vai para as observações do pedido para a secretaria resolver.

Cartão e boleto passam pela página hospedada do gateway: nenhum dado de cartão trafega pelo sistema.

## Gateways

| Gateway | Pix | Cartão / boleto | Notificação | Teste |
|---------|-----|-----------------|-------------|-------|
| **Asaas** | `POST /payments` + `pixQrCode` | Fatura hospedada (`invoiceUrl`) | Webhook cadastrado no painel Asaas (header `asaas-access-token`) | Sandbox (`api-sandbox.asaas.com`) |
| **PagBank** | `POST /orders` com `qr_codes` (`reference_id` = id da Cobranca) | Checkout PagBank (`POST /checkouts`, link `PAY`) | `notification_urls` enviado em cada cobrança | Sandbox (`sandbox.api.pagseguro.com`) |
| **Mercado Pago** | `POST /v1/payments` (`payment_method_id: pix`, `X-Idempotency-Key`) | Checkout Pro (`POST /checkout/preferences`, `init_point`) | `notification_url` enviado em cada cobrança | Sem sandbox: credenciais da aba **Teste** |

- O cadastro do associado não tem endereço, por isso boleto/cartão vão para a página do gateway (onde o associado
  completa os dados) em vez de API direta.
- PagBank e Mercado Pago: Pix e links valem **72 h**; depois disso, gerar de novo cria uma cobrança nova.
- PagBank exige chave Pix cadastrada na conta para gerar QR Code.
- Todos exigem CPF ou CNPJ do associado.
- Trocar de gateway exige a chave do novo; cobranças pendentes do anterior deixam de ser acompanhadas.

### Webhooks de PagBank e Mercado Pago

`POST webhook/pagbank/?schema=&token=` e `POST webhook/mercadopago/?schema=&token=` — o `token` é o
`webhook_token` da associação e vai na própria URL enviada ao gateway. O corpo da notificação **não é confiável**:
só se usa o id (pedido `ORDE_…` no PagBank, pagamento no Mercado Pago) e o status é relido na API com a chave da
associação. Tentativa recusada no checkout de cartão não cancela a cobrança (o associado pode tentar de novo).

Os dois gateways **só notificam URLs HTTPS**. Enquanto o site estiver em HTTP, a URL não é enviada e a confirmação
depende da sincronização abaixo.

## Sincronização (consulta ativa)

- `GET cobrancas/{id}/` (o modal do portal consulta a cada 5 s) pergunta ao gateway o status da cobrança pendente,
  no máximo a cada 15 s por cobrança — o Pix é confirmado em segundos mesmo sem webhook.
- `python manage.py sincronizar_cobrancas [--schema X]` varre as pendentes dos últimos 10 dias do gateway ativo;
  o `agendador` roda a cada **30 minutos**.
- Cada gateway implementa `consultar(cobranca) → (pago | cancelado | pendente, payload)`.

## Modelos

| Modelo | Descrição |
|--------|-----------|
| `ConfiguracaoPagamento` | Singleton por tenant (`atual()`): provedor, chave de API cifrada (Fernet derivado de `SECRET_KEY`), sandbox, ativo, formas aceitas, token do webhook |
| `Cobranca` | Uma tentativa de pagamento: método, provedor, status, `external_id`, URL da fatura, dados do Pix, payload bruto |

Status da cobrança: `pendente` → `paga` / `cancelada` / `falhou`. Ao pagar uma, as demais pendentes da mesma
anuidade são canceladas (localmente e no gateway, melhor esforço). Gerar de novo com o mesmo método e valor
reaproveita a cobrança aberta (no PagBank/Mercado Pago, só se ainda estiver dentro da validade).

## API REST (`/api/pagamentos/`)

| Endpoint | Quem | Descrição |
|----------|------|-----------|
| `GET/PUT/PATCH configuracao/` | financeiro TOTAL | Provedor e credenciais (`api_key` só escrita); `notificacao_automatica` indica site em HTTPS |
| `POST configuracao/testar/` | financeiro TOTAL | Testa a chave salva (saldo no Asaas, conta no Mercado Pago) |
| `GET disponibilidade/` | autenticado | `{habilitado, simulado, metodos}` para o portal |
| `POST anuidades/{id}/cobrar/` | associado dono | `{metodo}` → cria/reaproveita cobrança |
| `POST pedidos/{id}/cobrar/` | associado dono | Idem para pedido `pending` da loja (vencimento em 3 dias) |
| `GET cobrancas/{id}/` | associado dono | Status (+ consulta ao gateway, ver Sincronização) |
| `POST cobrancas/{id}/simular-pagamento/` | associado dono | Só com provedor `simulado` |
| `POST webhook/asaas/?schema=` | Asaas (sem login) | Valida header `asaas-access-token` |
| `POST webhook/pagbank/?schema=&token=` | PagBank (sem login) | Token na URL; relê o pedido na API |
| `POST webhook/mercadopago/?schema=&token=` | Mercado Pago (sem login) | Token na URL; relê o pagamento na API |

A configuração exige nível **TOTAL** em `financeiro` até para leitura, porque expõe o token do webhook.

## Configuração na associação

1. Painel → **Financeiro** → **Pagamento online** → escolher o **gateway**.
2. Colar a credencial:
   - Asaas: Integrações → Chave de API (começar em **sandbox**);
   - PagBank: Minha conta → Venda online → Integrações → Gerar token (começar em **sandbox**);
   - Mercado Pago: Developers → Suas integrações → aplicação → Credenciais → Access Token (começar com a aba **Teste**).
3. Só Asaas: cadastrar o webhook (Integrações → Webhooks) com a URL e o token exibidos; eventos de cobrança, API v3.
4. **Testar conexão**, marcar as formas aceitas e **Oferecer pagamento online no portal**.
5. Validado, desmarcar sandbox / trocar pela credencial de produção.

## Modo simulado

`PAGAMENTO_SIMULADO` (variável de ambiente; padrão = `DEBUG`). Quando ligado e não há gateway ativo,
o portal usa um gateway falso: Pix fictício e botão "Simular pagamento confirmado". Também é a única condição
em que o checkout da loja aceita `payment_method: "simulated"` (pagamento imediato). Útil em dev e demos;
**desligar em produção** (`PAGAMENTO_SIMULADO=False`).

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `payments/gateways.py` | `AsaasGateway`, `PagBankGateway`, `MercadoPagoGateway`, `SimuladoGateway` |
| `payments/services.py` | `cobrar_anuidade`, `confirmar_cobranca`, webhooks, `sincronizar_cobranca` / `sincronizar_pendentes` |
| `payments/management/commands/sincronizar_cobrancas.py` | Varredura usada pelo agendador |
| `payments/crypto.py` | Cifragem da chave de API |
| `frontend/src/components/pagamentos/PagamentoModal.tsx` | Modal do associado |
| `frontend/src/components/pagamentos/PagamentoOnlineModal.tsx` | Configuração no Financeiro |

Régua de cobrança por e-mail e linha do tempo: ver [`MEMBROS.md`](MEMBROS.md).

---

**Última atualização:** 2026-10-19
