# Integrações

App `integracoes` (TENANT_APPS) · página `/app/integracoes` · módulo de perfil `integracoes` (só **gestor**).

## Catálogo

`backend/integracoes/conectores.py` declara os conectores em código (sem tabela). Cada um tem categoria, descrição,
`acao` (onde configurar no painel) e uma função que calcula a `situacao` na associação:

| Situação | Quando |
|---|---|
| `ativo` | Gateway escolhido e ligado; ou ao menos um webhook ativo |
| `configurado` | Gateway escolhido com chave salva, mas desligado |
| `disponivel` | Pode ser configurado agora |
| `em_breve` | Ainda sem implementação (aparece para medir interesse) |

Gateways de pagamento (Asaas, PagBank, Mercado Pago) continuam em `payments` e abrem o `PagamentoOnlineModal`.
Só existe uma configuração de pagamento por associação: ativar um gateway substitui o anterior.

Novo conector: acrescentar um `Conector(...)` em `CONECTORES`; se tiver configuração própria, criar a `acao`
correspondente na página `frontend/src/pages/Integracoes.tsx`.

## Webhooks de saída

Modelos `WebhookSaida` (url, eventos, segredo, ativo, falhas seguidas) e `EntregaWebhook` (fila e histórico).

| Evento | Origem | `dados` |
|---|---|---|
| `membro.criado` | `post_save` de `Membro` | id, nome, email, instituicao, orcid |
| `anuidade.paga` | `membros.services.registrar_pagamento` | id, ano_referencia, valor, pago_em, membro {id, nome, email} |
| `inscricao.criada` | `post_save` de `InscricaoEvento` | id, evento {id, titulo}, nome, email, membro_id, confirmada |
| `ping` | botão "Testar" | mensagem |

`integracoes.services.disparar(evento, dados)` só grava as entregas (em savepoint; erro nunca derruba quem chamou).
O agendador roda `entregar_webhooks` a cada minuto.

Requisição:

```
POST <url>
Content-Type: application/json
X-Gesttora-Evento: anuidade.paga
X-Gesttora-Entrega: <uuid>
X-Gesttora-Timestamp: <unix>
X-Gesttora-Assinatura: sha256=<hex HMAC-SHA256(segredo, "<timestamp>.<corpo>")>

{"id": "...", "evento": "anuidade.paga", "criado_em": "...", "associacao": "<schema>", "dados": {...}}
```

Verificação no receptor (Python):

```python
esperado = "sha256=" + hmac.new(segredo.encode(), f"{ts}.".encode() + corpo, hashlib.sha256).hexdigest()
ok = hmac.compare_digest(esperado, cabecalho) and abs(time.time() - int(ts)) < 300
```

- Resposta 2xx = entregue. Outra resposta ou erro de rede: nova tentativa após 1, 5, 15, 60, 240 e 720 min; depois
  a entrega fica como "Falhou". O teste (`ping`) não é repetido. Redirecionamentos não são seguidos; timeout de 10 s.
- **Rede interna bloqueada:** só `https://` (em `DEBUG` também `http://`), e o host precisa resolver só para IPs
  públicos. Vale na criação e em cada entrega.
- Entregas concluídas há mais de 30 dias são apagadas.

## API

```
GET    /api/integracoes/catalogo/                    categorias, conectores, eventos, pode_configurar_pagamento
GET    /api/integracoes/webhooks/                    lista
POST   /api/integracoes/webhooks/                    {url, descricao, eventos[]}
PATCH  /api/integracoes/webhooks/{id}/               {ativo} etc. (religar zera as falhas seguidas)
DELETE /api/integracoes/webhooks/{id}/
POST   /api/integracoes/webhooks/{id}/testar/        entrega um ping na hora e devolve a entrega
POST   /api/integracoes/webhooks/{id}/regenerar-segredo/
GET    /api/integracoes/webhooks/{id}/entregas/      últimas 50
```

## Próximos passos

API pública com chave por associação (leitura de associados e eventos), mais eventos (`pedido.pago`,
`inscricao.confirmada`, `mandato.transicao`) e os conectores "em breve".
