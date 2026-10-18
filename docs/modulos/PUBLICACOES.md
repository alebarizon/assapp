# Módulo Publicações

Dossiês, e-books, boletins, livros e relatórios técnicos da associação, com paywall por adimplência e
venda pela loja. App TENANT `publicacoes`; módulo de acesso `publicacoes` (gestor, diretoria e
administrativo).

## Modelo

`Publicacao`: tipo, título, slug, subtítulo, resumo, autores (`[{nome, instituicao, orcid}]`),
palavras-chave, ano, edição, ISBN/ISSN, capa, arquivo, `acesso`, `publicada`/`publicado_em`, contador de
downloads e `catalog_item` (FK para `ecommerce.CatalogItem`, tipo `digital`).

## Acesso (`publicacoes/services.py`)

| `acesso` | Quem baixa |
|----------|------------|
| `publico` | Qualquer visitante, inclusive pelo site |
| `associados` | Associado adimplente (`membro_adimplente`); com preço, os demais podem comprar |
| `venda` | Quem tem pedido pago do item da loja; o sócio em dia paga o preço de sócio |

A equipe com o módulo `publicacoes` sempre baixa. A compra não precisa de fulfillment: o acesso é
calculado pelo `OrderItem` pago. A loja recusa recomprar a mesma publicação.

O item da loja é criado e atualizado a partir do preço informado na publicação (`sincronizar_item_loja`):
sai da vitrine quando a publicação vira rascunho, passa a acesso aberto, fica sem preço ou é excluída.

## API

```
CRUD  /api/publicacoes/                         painel (multipart: capa, arquivo; preco, preco_socio,
                                                remover_capa, remover_arquivo)
GET   /api/publicacoes/{id}/arquivo/            download pela equipe
GET   /api/publicacoes/minhas/                  portal: publicadas + liberado/motivo/catalog_item/preco_final
GET   /api/publicacoes/minhas/{id}/arquivo/     portal: download conforme o paywall
GET   /api/publicacoes/public/?schema=          site: catálogo
GET   /api/publicacoes/public/{slug}/?schema=
GET   /api/publicacoes/public/{slug}/arquivo/?schema=   só acesso aberto
```

## Frontend

- Painel `/app/publicacoes` — cartões com capa, downloads e vendas; modal de cadastro.
- Portal `/app/portal/publicacoes` — baixar, comprar (adiciona ao carrinho) ou regularizar a anuidade.
- Site `/site/publicacoes` e `/site/publicacoes/:slug` — conteúdo restrito leva ao login do portal.

Testes: `publicacoes/tests.py`.
