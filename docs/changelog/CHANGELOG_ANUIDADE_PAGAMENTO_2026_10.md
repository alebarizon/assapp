# Changelog — Anuidade que se cobra sozinha (2026-10)

Primeira entrega do roadmap de `nova-funcionalidades.md`: régua de cobrança, pagamento online e linha do tempo do associado.

## Backend

- **`membros.LembreteAnuidade`** (migration `membros/0003`) e `enviar_lembretes_anuidade`: e-mails 30 e 15 dias
  antes, no dia e 15 dias após o vencimento; idempotente.
- **Comando `regua_anuidades`**: marca vencidas + envia lembretes em todos os tenants ativos (`--schema`, `--sem-email`).
- **`POST /api/membros/anuidades/enviar_lembretes/`** e **`GET /api/membros/membros/{id}/timeline/`**.
- `registrar_pagamento` agora é idempotente (não duplica lançamento em `finance`).
- **App `payments` agora é TENANT** (migration `payments/0001`): `ConfiguracaoPagamento`, `Cobranca`, gateway Asaas
  (Pix, cartão, boleto) e simulado, webhook `/api/pagamentos/webhook/asaas/?schema=`.
- Setting `PAGAMENTO_SIMULADO` (padrão = `DEBUG`).
- Testes: `membros/tests.py` e `payments/tests.py`.

## Frontend

- Portal (`MeuPerfil`): botão **Pagar** nas anuidades abertas → `PagarAnuidadeModal` (QR Pix, copia-e-cola, fatura).
- Financeiro: botão **Pagamento online** (só financeiro TOTAL) → `PagamentoOnlineModal`.
- Membros: botão **Enviar lembretes**; detalhe do membro com **Linha do tempo** e "Último lembrete" por anuidade.

## Deploy (staging / produção)

```bash
docker compose exec backend python manage.py migrate_schemas --shared
docker compose exec backend python manage.py migrate_schemas
```

Variável no `.env` do droplet: `PAGAMENTO_SIMULADO=True` em staging/demo, `False` em produção.

A régua roda sozinha uma vez por dia pelo serviço `agendador` do compose (ver "Agendador" abaixo); não há
cron no droplet. O provedor de e-mail precisa estar configurado para os lembretes saírem; envios com falha são
retentados na execução seguinte.

## Desconto de sócio adimplente na loja

- `CatalogItem.member_price` + `OrderItem.list_price` (migration `ecommerce/0003`).
- `membros.services.membro_adimplente`: filiação ativa/honorária e nenhuma anuidade em atraso.
- Vitrine (`preco_final`), carrinho (`total`, `total_cheio`, `adimplente`) e checkout usam o preço de sócio para quem está em dia.
- Frontend: campo "Preço para sócio em dia" no Catálogo e na criação do item de venda do curso; loja e carrinho do
  portal mostram o preço riscado, a economia ou o convite para regularizar a anuidade; site público do curso
  mostra "Associado em dia paga…"; pedidos da diretoria marcam "(preço de sócio)".
- Correção: `GET /api/ecommerce/public/catalog/` quebrava com `NameError` (`CatalogItemType` sem import).
- Testes: `ecommerce/tests.py`.

## Pagamento online dos pedidos da loja

- `payments.Cobranca.pedido` (migration `payments/0002`) e `ecommerce.PaymentMethod.ONLINE` (`ecommerce/0004`).
- `POST /api/pagamentos/pedidos/{id}/cobrar/`; checkout aceita `payment_method: "online"`.
- Confirmação conclui o pedido (inscrição, matrícula) e espelha no financeiro; falha de fulfillment não desfaz o pagamento.
- Carrinho do portal: "Pagar online — Pix, cartão ou boleto" e lista de pedidos aguardando pagamento com botão **Pagar**.
- `PagamentoModal` genérico (anuidade e pedido).
- **Segurança:** checkout `simulated` (pagamento imediato) agora só é aceito com `PAGAMENTO_SIMULADO`;
  antes qualquer associado conseguia concluir pedidos sem pagar em produção. Padrão do checkout passou a `manual`.

## Hotsite do evento

- `EventoAcademico.publicado_site`, `resumo`, `capa` + modelo `AtividadeProgramacao` (migration `eventos/0003`).
- API: capa, item de inscrição na loja (preço cheio e de sócio), programação, endpoints públicos.
- Painel: abas **Programação** e **Site e inscrição** no detalhe do evento.
- Site: `/site/eventos` e `/site/eventos/:slug` (programação por dia, chamada de trabalhos, inscrição, anais) e
  link "Eventos" no menu.
- Testes: `eventos/tests.py`.

## Chamada de trabalhos científicos completa

- Migration `eventos/0004`: critérios com peso, nota de corte e arquivo obrigatório na chamada; coautores e decisão
  na submissão; notas por critério, nota ponderada e prazo no parecer; modelo `CertificadoPapel`.
- Regras em `eventos/cientifico.py`: submissão pelo autor (janela, limite por autor, área, arquivo), conflito de
  interesse (autor e coautores), nota ponderada, decisão da comissão com carta por e-mail e certificados de autoria
  e de parecerista (verificáveis em `/site/certificados`).
- O parecer não decide mais o trabalho: a comissão decide em `POST /api/eventos/submissoes/{id}/decidir/`.
- Portal: **Trabalhos científicos** (`/app/portal/trabalhos`) e **Pareceres** (`/app/portal/pareceres`); equipe vê
  **Meus pareceres** (`/app/pareceres`) quando tem trabalhos atribuídos; papel parecerista entra direto nos pareceres.
- Painel do evento: aba **Chamada** com critérios e pesos; aba **Submissões** com escolha de parecerista e prazo,
  notas, média × nota de corte, decisão e emissão de certificados.
- Hotsite: botão "Submeter trabalho pelo portal" quando a chamada está aberta.
- Correção: o upload da capa do evento enviava JSON em vez de multipart.
- Testes: `eventos/test_cfp.py`.

## Anais públicos por trabalho

- Migration `eventos/0005`: `TrabalhoPublicado` e campos editoriais nos anais (ISBN, licença, apresentação,
  editores, cidade).
- `eventos/anais.py`: publicação idempotente (slug, DOI e PDF preservados), citações ABNT/APA/BibTeX e PDF com resumo.
- Site: `/site/eventos/:slug/anais` (sumário por área com busca) e `/site/eventos/:slug/anais/:trabalho` (resumo,
  autores com ORCID, como citar com botão copiar, PDF, DOI, licença, metadados `citation_*`).
- Painel: aba **Anais** com dados editoriais, DOI e PDF final por trabalho e link para a página pública.
- Botões do site em seções claras ganharam variantes visíveis (`tenant-site-btn-primary` / `-outline`).
- Testes: `eventos/test_anais.py`.
- Após o deploy, eventos com anais já publicados precisam de "Atualizar anais" para ganhar as páginas por trabalho.

## Carteirinha digital

- Migration `membros/0004`: matrícula e código do QR no `Membro`.
- `membros/carteirinha.py`: situação (em dia / pendente / inativa), validade, QR SVG, PDF tamanho cartão.
- Portal: **Carteirinha** (`/app/portal/carteirinha`) com cartão, QR, PDF e aviso para regularizar a anuidade.
- Site: `/site/carteirinha/:codigo` — verificação pública da situação no momento da leitura, sem dados de contato.
- Painel: carteirinha no detalhe do membro, com PDF e "Gerar novo QR" (invalida o anterior).
- Testes: `membros/test_carteirinha.py`.

## Ficha 360 do contato

- `GET /api/contatos/{id}/ficha/` (`contatos/ficha.py`): resumo (associado e situação, contatos, eventos,
  trabalhos, compras pagas, última atividade) e linha do tempo unificada.
- Contato vinculado usa a linha do tempo do associado; não vinculado é cruzado por e-mail com inscrições,
  submissões e respostas de formulário, e sugere o associado com o mesmo e-mail.
- Painel: card **Ficha 360** no detalhe do contato.
- Testes: `contatos/test_ficha.py`.

## Publicações (novo app `publicacoes`)

- Dossiês, e-books, boletins, livros e relatórios com capa, arquivo, autores e ISBN/ISSN.
- Acesso aberto, para associados em dia ou por venda; o preço cria o item digital na loja e o pedido pago
  libera o download no portal.
- Painel `/app/publicacoes`, portal `/app/portal/publicacoes`, site `/site/publicacoes`.
- Novo módulo de acesso `publicacoes` (gestor, diretoria, administrativo).
- Migration `publicacoes/0001`. Testes: `publicacoes/tests.py`.

## Assembleias e votações (novo app `governanca`)

- Assembleias com convocação por e-mail, pauta, presença (painel e portal), quórum sobre os associados
  em dia, ata gerada a partir da pauta e dos resultados, publicação com hash SHA-256 e PDF.
- Eleições de chapa e deliberações com cédula digital (secreta ou nominal), censo congelado na
  abertura, voto em branco opcional, comprovante, apuração com vencedora/empate e registro na memória.
- Painel `/app/governanca`, portal `/app/portal/governanca`.
- Novo módulo de acesso `governanca` (gestor e diretoria; administrativo em leitura).
- Migration `governanca/0001`. Testes: `governanca/tests.py`.

## Newsletter (novo app `newsletter`)

- Campanhas por e-mail com público combinável: associados por situação e categoria, inscritos em
  eventos e contatos por etiqueta (só com consentimento LGPD); contagem, amostra, prévia e envio de teste.
- Envio por fila (`enviar_newsletters`) com limite por minuto (`NEWSLETTER_POR_MINUTO`), até 3
  tentativas, interrupção e acompanhamento ao vivo.
- Descadastro com link assinado no rodapé, `List-Unsubscribe` one-click e página `/site/descadastrar`.
- A fila é despachada pelo serviço `agendador` (ver abaixo).
- Novo módulo de acesso `newsletter` (gestor, diretoria, administrativo).
- Migration `newsletter/0001`. Testes: `newsletter/tests.py`.

## Diretório público de associados

- O associado passa a editar no portal (`/app/portal/perfil`) instituição, área, Lattes, ORCID,
  telefone e minibiografia, e autoriza (ou retira) a presença no diretório.
- A associação liga o diretório em Website; o site ganha `/site/associados` com busca e filtro por
  instituição. Só aparecem associados com filiação ativa/honorária que autorizaram; nunca e-mail,
  telefone ou CPF.
- Painel: detalhe do associado mostra se e quando ele autorizou.
- Migrations `membros/0005`, `website/0003`. Testes: `membros/test_diretorio.py`.

## Agendador (cobrança automática)

- Comando `agendador` (`core`): a cada minuto um lote da newsletter; uma vez por dia, a partir de
  `REGUA_HORA` (padrão 8h, Brasília), a régua de anuidades. Falha numa tarefa não derruba a outra.
- Sem provedor de e-mail que entregue de fato, a régua roda com `--sem-email` (só marca
  vencidas/inadimplentes), para não registrar lembretes que não saíram.
- O serviço `newsletter` do compose virou `agendador` (`assapp_agendador_prod` / `_staging`);
  `scripts/deploy.sh` remove o container antigo. Variável nova: `REGUA_HORA`.
- Testes: `core/test_agendador.py`.

## Situação em produção (2026-10-18)

- Tudo acima está em produção. Últimos deploys: `5106f5e` (assembleias, newsletter, diretório), `53f9fed`
  (agendador) e `f3d0852` (correção do `deploy.sh`; incidente descrito em
  [`CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md`](CHANGELOG_INFRA_ORBSTACK_DO_2026_07.md), seção 11).
- Diretório público vem desligado: cada associação liga em Website e cada associado autoriza no portal.
- E-mail ainda é console em staging e produção: convocações, newsletter e lembretes só aparecem no log.

### Pendências (decisão do produto)

- Provedor de e-mail por API HTTP (Brevo, Resend ou SES) — a DigitalOcean bloqueia SMTP.
- `PAGAMENTO_SIMULADO=False` + chave Asaas real em produção, ou manter simulado.
- "Atualizar anais" nos eventos com anais já publicados, para gerar as páginas por trabalho.

Docs: [`EVENTOS.md`](../modulos/EVENTOS.md) · [`ECOMMERCE.md`](../modulos/ECOMMERCE.md) · [`PAGAMENTOS.md`](../modulos/PAGAMENTOS.md) · [`MEMBROS.md`](../modulos/MEMBROS.md) · [`CONTATOS.md`](../modulos/CONTATOS.md) · [`PUBLICACOES.md`](../modulos/PUBLICACOES.md) · [`GOVERNANCA.md`](../modulos/GOVERNANCA.md) · [`NEWSLETTER.md`](../modulos/NEWSLETTER.md)
