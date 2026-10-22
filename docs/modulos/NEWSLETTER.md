# Módulo Newsletter

Campanhas de e-mail segmentadas para associados, inscritos em eventos e contatos do CRM, com fila de
envio em ritmo controlado e descadastro (LGPD), e réguas automáticas de relacionamento (boas-vindas,
reengajamento de inativos, convite ao autor aprovado que não é sócio). App TENANT `newsletter`; módulo de acesso `newsletter`
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
4. Em staging e produção o serviço `agendador` do compose (comando `agendador`) roda um lote por
   minuto. Em dev, rode o comando à mão:

```bash
docker compose exec -T backend python manage.py enviar_newsletters [--schema abciber] [--por-minuto 10]
```

Cada e-mail traz rodapé com link de descadastro e os cabeçalhos `List-Unsubscribe` /
`List-Unsubscribe-Post` (descadastro em um clique nos clientes de e-mail). O token é assinado
(`django.core.signing`) com o schema da associação.

**Entrega real:** com `EMAIL_BACKEND` console (padrão em staging e produção) os e-mails só vão para o
log. A DigitalOcean bloqueia SMTP de saída; a entrega exige um provedor por API HTTP (Brevo, Resend,
Amazon SES) configurado como backend de e-mail.

## Réguas automáticas (`newsletter/reguas.py`)

E-mails de relacionamento disparados por regra, uma vez por dia, pelo comando `reguas_relacionamento`
(chamado pelo `agendador` a partir de `REGUA_HORA`). Modelos: `Regua` (uma linha por tipo: `ativa`, `assunto`,
`corpo`, `dias`; criada com o texto padrão na primeira leitura) e `EnvioRegua` (`tipo` + `chave` únicos — o mesmo
gatilho nunca gera dois e-mails).

| Régua | Padrão | Quem recebe | Chave |
|-------|--------|-------------|-------|
| `boas_vindas` | ligada, 7 dias | Associado ativo com filiação ativa/honorária iniciada nos últimos `dias` dias | membro |
| `inativos` | **desligada**, 6 meses | Associado com filiação ativa/honorária há mais de `dias` meses e sem login, inscrição em evento, matrícula, formulário enviado ou submissão no período; no máximo um e-mail a cada `dias` meses | membro + data |
| `autor_nao_socio` | ligada, 30 dias | Autor e coautores de trabalho aceito nos últimos `dias` dias que não têm filiação ativa/honorária/inadimplente | e-mail + evento |

- Variáveis: `{nome}` (primeiro nome), `{associacao}`, `{proximo_evento}` (próximo evento publicado no site, ou
  vazio), `{trabalho}` e `{evento}` (só autor). Linhas em branco que sobram são removidas.
- Boas-vindas é mensagem de filiação: sem rodapé de descadastro e enviada mesmo a quem saiu da newsletter.
  Inativos e autor levam o rodapé e o `List-Unsubscribe`, e respeitam `Descadastro`.
- Botão: portal (`/app/portal`) em boas-vindas e inativos; `/site?schema=…#associe-se` no convite ao autor.
- No máximo 200 e-mails por régua por dia em cada associação; o restante sai nos dias seguintes.
- Sem provedor que entregue de fato (`EMAIL_BACKEND` console/locmem/arquivo), o agendador **não** roda as
  réguas, para não registrar envios que não saíram. À mão: `python manage.py reguas_relacionamento [--schema x]`.
- Cada envio a associado aparece na linha do tempo dele ("E-mail automático: …").

## API

```
GET   /api/newsletter/reguas/                    {reguas, email_entregue, hora, limite_por_dia}
PATCH /api/newsletter/reguas/{tipo}/             ativa, assunto, corpo, dias (inativos 1–24; demais 1–90)
GET   /api/newsletter/reguas/{tipo}/previa/      total e amostra de quem receberia hoje
POST  /api/newsletter/reguas/{tipo}/teste/       {email?} (padrão: e-mail do usuário)
POST  /api/newsletter/reguas/{tipo}/restaurar/   volta assunto, texto e prazo ao padrão
GET   /api/newsletter/reguas/envios/?tipo=       últimos 200 envios
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

- Painel `/app/newsletter` — abas campanhas, **réguas automáticas** e descadastros; `/app/newsletter/nova` e
  `/app/newsletter/:id` com editor, público, prévia do e-mail, acompanhamento do envio e lista de envios.
- Réguas (`components/newsletter/ReguasPanel.tsx`): ativar/desligar (ao ativar, confirma quantas pessoas
  receberiam), editar assunto/texto/prazo, "Quem receberia hoje", teste para o próprio e-mail, texto padrão,
  aviso quando o servidor não entrega e-mail e histórico dos últimos envios.
- Site `/site/descadastrar?schema=&t=` — confirmação do descadastro (funciona sem site publicado).

Testes: `newsletter/tests.py`, `newsletter/test_reguas.py`.
