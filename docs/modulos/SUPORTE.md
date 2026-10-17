# Módulo Suporte

Chamados da associação para a equipe Gesttora. Inspirado em `support` do WellSaaS, mas com outra
arquitetura de dados.

## Arquitetura

- App **compartilhado** (`SHARED_APPS`): tabelas só no schema `public`. A equipe (superadmin, schema `sistema`)
  vê os chamados de todas as associações sem trocar de schema; as associações acessam pela `search_path`
  (`<tenant>, public`).
- `Chamado.tenant` é FK para `tenants.Tenant`. O autor (usuário do schema do tenant) é guardado de forma
  desnormalizada: `autor_id`, `autor_nome`, `autor_email`.
- No WellSaaS os tickets ficavam no schema de cada tenant e o superadmin percorria todos os schemas — não replicar.

## Modelo

| Modelo | Campos principais |
|--------|-------------------|
| `Chamado` | tenant, assunto, categoria, prioridade, status, autor_*, `lido_pela_equipe`, `lido_pela_associacao`, `ultima_mensagem_em` |
| `MensagemChamado` | autor, `da_equipe`, `interna` (nota só da equipe), texto |
| `AnexoChamado` | arquivo (`support/%Y/%m/`), nome, tamanho — até 5 por mensagem, 10 MB, extensões de imagem/PDF/office/txt/csv |

Status: `aberto`, `em_andamento`, `aguardando_associacao`, `resolvido`, `fechado`.

## Regras

- Diretoria (association_admin / board_member) vê apenas chamados da própria associação; associado não acessa.
- Resposta da equipe → status `aguardando_associacao` + e-mail ao autor.
- Resposta da associação → `em_andamento` (ou reabre se resolvido/fechado) + e-mail para `SUPPORT_EMAIL`.
- Notas internas não aparecem para a associação e não mudam status.
- A associação só pode **fechar** ou **reabrir**; a equipe altera qualquer status e a prioridade.
- Mudança de status registra mensagem no histórico.

## Configuração

```
SUPPORT_EMAIL=suporte@gesttora.com.br   # caixa que recebe avisos (vazio = sem aviso)
FRONTEND_URL=https://...                # base dos links nos e-mails
```

## API

```
GET/POST /api/suporte/                   lista (status=abertos|<status>, categoria, search, tenant*) · abrir (multipart)
GET      /api/suporte/{id}/              detalhe (marca como lido para quem abre)
POST     /api/suporte/{id}/responder/    texto, interna*, anexos[]
POST     /api/suporte/{id}/status/       {status, prioridade*}
GET      /api/suporte/resumo/            por status + não lidos
```
`*` só equipe.

## Frontend

`/app/suporte` e `/app/suporte/:id` (menu “Suporte”). A mesma tela se adapta: para o superadmin mostra a
associação, seletor de status/prioridade e opção de nota interna.

Testes: `support/tests.py`.
