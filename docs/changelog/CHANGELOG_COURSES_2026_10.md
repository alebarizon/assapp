# Changelog — Módulo Cursos (2026-10-16)

Port do módulo `courses` do WellSaaS, adaptado ao modelo de associação (aluno = `Membro`)
e à loja (`ecommerce`). Documentação: [`docs/modulos/COURSES.md`](../modulos/COURSES.md).

## Backend

- Novo app TENANT `courses` (`/api/courses/`): cursos, módulos, aulas (texto/vídeo/quiz),
  anexos, matrículas, progresso, tentativas de quiz, perguntas e respostas.
- Integração com `ecommerce`:
  - `fulfill_order_item` (tipo `curso`) matricula o associado nos cursos vinculados ao item.
  - `validate_cart_item_for_membro` bloqueia compra repetida e quantidade > 1.
  - Ação `create-catalog-item` cria o item da loja a partir do curso.
- Gerador de certificado reaproveitável: `core/certificates.py`.
- Rotas públicas por `?schema=`: catálogo, detalhe, aula de amostra e verificação de certificado.
- Testes: `courses/tests.py` (17) + `conftest.py`/`pytest.ini` na raiz do backend.
- Migrations: `courses/0001_initial`; `ecommerce/0002` (apenas renomeação de índices/help_text).

## Frontend

- Diretoria: `/app/courses` e `/app/courses/:id` (menu “Cursos”).
- Associado: `/app/portal/cursos` e player (menu “Meus cursos” + card no Portal).
- Site público: `/site/cursos`, `/site/cursos/:slug`, `/site/certificados` (link “Cursos” no menu do site).
- Editor de conteúdo próprio (`RichTextEditor`), sem novas dependências.

## Verificação

- `tsc` + `vite build` ok.
- Teste no navegador (demo): criar curso, módulo, aula de texto com amostra, quiz, publicar,
  criar item na loja, catálogo público e modal de amostra, página de verificação — ok.
  A matrícula manual não foi exercitada pela interface (busca sem associados na base demo);
  está coberta pelos testes do backend.
