# Módulo Mensagens

Conversas entre a diretoria (secretaria) e cada associado. Inspirado em `business.Message` do WellSaaS,
organizado em conversas com assunto.

## Modelo (app TENANT `mensagens`)

| Modelo | Campos principais |
|--------|-------------------|
| `Conversa` | membro, assunto, status (`aberta`/`arquivada`), `iniciada_pela_diretoria`, `lida_pela_diretoria`, `lida_pelo_associado`, `ultima_mensagem_em` |
| `Mensagem` | conversa, autor (User), `autor_nome`, `da_diretoria`, texto |

## Regras

- Diretoria inicia conversa com um associado, vários ou **todos os ativos** — sempre uma conversa individual
  por associado (respostas não vazam entre associados).
- Associado inicia conversa com a secretaria pelo portal.
- Cada lado tem seu indicador de não lida; abrir a conversa marca como lida.
- Mensagem da diretoria envia e-mail ao associado (opcional na criação) com link para o portal.
- Qualquer resposta reabre conversa arquivada.

## API

```
Diretoria
GET/POST /api/mensagens/                   lista (status, nao_lidas=true, membro, search) · iniciar {membros|todos_ativos, assunto, texto, notificar}
GET      /api/mensagens/{id}/
POST     /api/mensagens/{id}/responder/    {texto}
POST     /api/mensagens/{id}/arquivar/     {arquivar: bool}
GET      /api/mensagens/resumo/

Associado
GET/POST /api/mensagens/my/                suas conversas · iniciar {assunto, texto}
GET      /api/mensagens/my/{id}/
POST     /api/mensagens/my/{id}/responder/
GET      /api/mensagens/my/resumo/
```

## Frontend

- Diretoria: `/app/mensagens`, `/app/mensagens/:id` (menu “Mensagens”).
- Associado: `/app/portal/mensagens`, `/app/portal/mensagens/:id` (menu + card no Portal).
- Componente compartilhado `components/mensagens/ConversaThread.tsx`.

Testes: `mensagens/tests.py`.
