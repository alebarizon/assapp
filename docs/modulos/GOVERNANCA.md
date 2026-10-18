# Módulo Governança (assembleias e votações)

Convocação de assembleias, lista de presença com quórum, eleições de chapa e deliberações com cédula
digital, apuração e ata com hash. App TENANT `governanca`; módulo de acesso `governanca` (gestor e
diretoria com acesso total, administrativo em leitura).

## Modelo

- `Assembleia`: título, tipo (ordinária/extraordinária), data e hora, modalidade (presencial/online/
  híbrida), local, link, convocação, pauta (`[str]`), quórum mínimo (%), mandato, status
  `rascunho → convocada → em_andamento → encerrada` (ou `cancelada`), ata, `ata_publicada_em`, `ata_hash`.
- `PresencaAssembleia`: uma por associado, forma presencial ou online.
- `Votacao`: tipo `eleicao` (chapas/candidatos) ou `deliberacao` (Aprovo/Rejeito/Abstenção criadas ao
  abrir), censo (`adimplentes` ou `ativos`), secreta, `max_escolhas`, `permite_branco`, `fecha_em`,
  status `rascunho → aberta → encerrada` (ou `cancelada`), `resultado` congelado na apuração.
- `OpcaoVotacao`: título, descrição, integrantes (`[{nome, cargo}]`), ordem.
- `Eleitor`: censo congelado na abertura; `votou_em` marca quem já votou.
- `Cedula`: id UUID e só a data; no voto secreto não guarda o eleitor, e o comprovante é o próprio id.

## Regras (`governanca/services.py`)

- Abrir exige ao menos duas opções e congela o censo; depois de aberta só descrição e prazo mudam.
- Votar é atômico (`select_for_update` no eleitor), respeita `max_escolhas`, branco e o prazo.
- O resultado fica oculto enquanto a votação está aberta; a apuração aponta vencedora ou empate e
  registra uma decisão na memória institucional.
- Convocar envia um e-mail por associado ativo com link para o portal.
- Quórum: presentes aptos (associados em dia) sobre o total de aptos. Presença de quem não está em dia
  é registrada, mas não conta para o quórum.
- A ata pode ser gerada a partir da pauta, presença e resultados; publicar grava o SHA-256, registra na
  memória e bloqueia a edição. PDF via reportlab.

## API

```
CRUD  /api/governanca/assembleias/
POST  /api/governanca/assembleias/{id}/convocar|iniciar|encerrar|cancelar/
GET/POST/DELETE /api/governanca/assembleias/{id}/presencas/   (DELETE ?membro=)
POST  /api/governanca/assembleias/{id}/gerar-ata|publicar-ata/
GET   /api/governanca/assembleias/{id}/ata-pdf/
CRUD  /api/governanca/votacoes/                    opções aninhadas
POST  /api/governanca/votacoes/{id}/abrir|encerrar|cancelar/
GET   /api/governanca/votacoes/{id}/participacao/
GET   /api/governanca/minhas/                      portal: votações e assembleias
POST  /api/governanca/minhas/votacoes/{id}/votar/  {opcoes: [id]}  ([] = branco)
POST  /api/governanca/minhas/assembleias/{id}/presenca/
GET   /api/governanca/minhas/assembleias/{id}/ata-pdf/
```

## Frontend

- Painel `/app/governanca` — listas de assembleias e votações; detalhes em
  `/app/governanca/assembleias/:id` (presença, quórum, ata) e `/app/governanca/votacoes/:id`
  (opções, participação, resultado).
- Portal `/app/portal/governanca` — cédula com confirmação e comprovante, presença online e atas.

Testes: `governanca/tests.py`.
