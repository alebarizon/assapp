# Changelog — Módulo Formulários (2026-10-16)

Adaptação do QPC do WellSaaS para formulários da associação. Documentação:
[`docs/modulos/FORMULARIOS.md`](../modulos/FORMULARIOS.md).

## Backend

- Novo app TENANT `formularios` (`/api/formularios/`): formulários, seções, perguntas (8 tipos),
  respostas e itens de resposta.
- Três canais: link público (com ou sem identificação), portal do associado e convite individual com link pessoal.
- Resumo consolidado por pergunta e exportação CSV.
- Vínculo opcional com `eventos.EventoAcademico`.
- Limite de requisições nas rotas públicas (`ScopedRateThrottle`, escopo `formularios_public`, 60/min).
- Testes: `formularios/tests.py` (15).

## Frontend

- Diretoria: `/app/formularios` e `/app/formularios/:id` (menu “Formulários”).
- Associado: `/app/portal/formularios` (menu + card no Portal).
- Resposta sem login: `/site/formularios/:token` e `/site/formularios/convite/:token`.
- `EventoDetail`: nova aba **Avaliação**, que cria um formulário de avaliação com perguntas-modelo.
- `apiErrorMessage` movido para `utils/apiError.ts` (reexportado em `services/courses.ts`).

## Verificação

- `tsc` + `vite build` ok; 32 testes de backend (formularios + courses) ok.
- Teste no navegador (demo): criar, montar perguntas, publicar, link público, validação de obrigatória,
  envio, resumo/individuais, aba Avaliação do evento — ok.
