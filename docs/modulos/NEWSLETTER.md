# Módulo Newsletter

Campanhas de e-mail segmentadas para associados, inscritos em eventos e contatos do CRM, com fila de
envio em ritmo controlado e descadastro (LGPD). App TENANT `newsletter`; módulo de acesso `newsletter`
(gestor, diretoria e administrativo).

## Modelo

- `Campanha`: assunto, corpo (texto simples; `{nome}` vira o primeiro nome), link e texto do botão,
  `publico` (JSON), status `rascunho → enviando → enviada` (ou `cancelada`).
- `EnvioCampanha`: um por e-mail e campanha (único), status `pendente | enviado | falha | cancelado`,
  tentativas e último erro.
- `Descadastro`: e-mail fora de todas as campanhas e a campanha que originou o pedido.

## Público (`newsletter/services.destinatarios`)

```json
{"associados": {"situacoes": ["em_dia", "pendente", "inativo"], "tipos": ["estudante"]},
 "eventos": ["<uuid>"], "etiquetas": [3]}
```

- Associados: situação com a mesma regra de `membro_adimplente` (em dia, anuidade em atraso, inativo
  ou ex-associado) e categoria da filiação. Lista vazia vale para todas.
- Eventos: inscritos (`InscricaoEvento`) dos eventos escolhidos.
- Etiquetas: contatos com a etiqueta **e** consentimento LGPD.
- As fontes se somam; cada e-mail aparece uma vez e descadastrados ficam de fora.

## Envio

1. A tela mostra a contagem e uma amostra (`POST campanhas/publico/`) e permite um envio de teste.
2. `enviar` congela a lista em `EnvioCampanha` e passa a campanha para `enviando`. Nada é enviado na
   requisição.
3. O comando `enviar_newsletters` despacha a fila em lotes, com limite por minuto
   (`NEWSLETTER_POR_MINUTO`, padrão 30) dividido entre as associações com campanha em andamento. Ele
   reabre a lista de descadastros a cada lote, tenta cada e-mail até 3 vezes e conclui a campanha
   quando a fila acaba.
4. Em staging e produção o serviço `newsletter` do compose roda `enviar_newsletters --loop`. Em dev,
   rode o comando à mão:

```bash
docker compose exec -T backend python manage.py enviar_newsletters [--schema abciber] [--por-minuto 10]
```

Cada e-mail traz rodapé com link de descadastro e os cabeçalhos `List-Unsubscribe` /
`List-Unsubscribe-Post` (descadastro em um clique nos clientes de e-mail). O token é assinado
(`django.core.signing`) com o schema da associação.

**Entrega real:** com `EMAIL_BACKEND` console (padrão em staging e produção) os e-mails só vão para o
log. A DigitalOcean bloqueia SMTP de saída; a entrega exige um provedor por API HTTP (Brevo, Resend,
Amazon SES) configurado como backend de e-mail.

## API

```
CRUD  /api/newsletter/campanhas/                 (editar/excluir só em rascunho)
POST  /api/newsletter/campanhas/publico/         {publico} → total, por_origem, amostra
GET   /api/newsletter/campanhas/opcoes/          eventos e etiquetas
POST  /api/newsletter/campanhas/{id}/teste/      {email}
POST  /api/newsletter/campanhas/{id}/enviar|cancelar|duplicar/
GET   /api/newsletter/campanhas/{id}/envios/?status=
GET   /api/newsletter/descadastros/              DELETE {id}/ reativa
GET   /api/newsletter/public/descadastrar/?schema=&t=    situação
POST  /api/newsletter/public/descadastrar/?schema=&t=    descadastra (aceita one-click)
```

## Frontend

- Painel `/app/newsletter` — campanhas e descadastros; `/app/newsletter/nova` e `/app/newsletter/:id`
  com editor, público, prévia do e-mail, acompanhamento do envio e lista de envios.
- Site `/site/descadastrar?schema=&t=` — confirmação do descadastro (funciona sem site publicado).

Testes: `newsletter/tests.py`.
