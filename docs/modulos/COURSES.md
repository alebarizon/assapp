# Módulo Cursos — Gesttora

> **Status:** MVP (2026-10) — portado do WellSaaS (`courses/`) e integrado ao `ecommerce`  
> **App Django:** `backend/courses/` (TENANT)

---

## Conceito

Cursos online da associação: módulos → aulas (texto, vídeo do YouTube ou quiz), anexos,
progresso por aluno, perguntas e respostas por aula e certificado em PDF.

- **Aluno = `membros.Membro`** (resolvido a partir do user via `resolver_membro_do_user`).
- **Venda pela loja:** o curso aponta para um `ecommerce.CatalogItem` do tipo `curso`.
  Quando o pedido é pago, `fulfill_order_item` chama `enroll_from_catalog_item` e cria a matrícula.
  Preço zero = curso gratuito (o associado “compra” por R$ 0,00 na loja).
- **Matrícula manual** pela diretoria (aba Alunos), independente da loja.
- A loja recusa adicionar ao carrinho um curso em que o associado já está matriculado.

| Campo / regra | Comportamento |
|---------------|---------------|
| `status` | `draft` (oculto), `published`, `archived` (alunos mantêm acesso; some do site) |
| `visibility` | `public` aparece em `/site/cursos`; `unlisted` só pelo link direto |
| `progression_mode` | `sequential` libera aula a aula; `free` libera tudo |
| `is_preview` | aula de texto/vídeo aberta no site sem matrícula |
| Quiz | concluído ao enviar (qualquer nota); pode refazer; média aparece para a diretoria |
| Certificado | gerado ao concluir todas as aulas (`certificate_code`); PDF com carga horária e instrutor |

Gerador de PDF reaproveitável: `backend/core/certificates.py` (`build_certificate_pdf`) — pensado
também para certificados de `eventos`.

---

## API REST (`/api/courses/`)

### Diretoria (`IsBoardOrAdmin`)

| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /api/courses/` | Lista (`?status=`, `?search=`) / cria (multipart para capa) |
| `GET/PATCH/DELETE /api/courses/{id}/` | Detalhe com módulos e aulas |
| `POST /api/courses/{id}/duplicate/` | Copia o curso como rascunho |
| `POST /api/courses/{id}/create-catalog-item/` | Cria item `curso` na loja (`{price}`) e vincula |
| `POST /api/courses/{id}/reorder/` | `{sections: [{id, lesson_ids}]}` |
| `GET/POST /api/courses/{id}/students/` | Alunos / matrícula manual (`{membro}`) |
| `PATCH /api/courses/{id}/students/{enrollment}/` | `{status: active\|revoked}` |
| `/api/courses/sections/`, `/lessons/`, `/attachments/` | CRUD (anexos até 20 MB) |
| `POST /api/courses/uploads/image/` | Imagem para o editor de conteúdo |
| `GET /api/courses/questions/` | Perguntas (`?course=`, `?answered=`) · `POST {id}/reply/` |

### Associado (`IsAuthenticated` + Membro)

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/courses/my/` | Minhas matrículas com progresso |
| `GET /api/courses/my/{id}/` | Estrutura + aulas concluídas/bloqueadas |
| `GET /api/courses/my/{id}/lessons/{lesson}/` | Conteúdo (respeita a progressão) |
| `POST …/lessons/{lesson}/complete/` | Concluir aula de texto/vídeo |
| `POST …/lessons/{lesson}/quiz/` | `{answers: {question_id: [option_ids]}}` |
| `GET/POST …/lessons/{lesson}/questions/` | Perguntas da aula |
| `POST /api/courses/my/{id}/questions/{q}/replies/` | Responder |
| `GET /api/courses/my/{id}/certificate/` | PDF |

### Público (`?schema=`)

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/courses/public/` | Catálogo (publicados e `public`) |
| `GET /api/courses/public/{slug}/` | Detalhe com ementa |
| `GET /api/courses/public/{slug}/lessons/{lesson}/` | Aula de amostra |
| `GET /api/courses/public/certificates/{code}/` | Verificação de certificado |

---

## Frontend

| Página | Rota | Público |
|--------|------|---------|
| `Courses.tsx` | `/app/courses` | Diretoria (lista + caixa de perguntas) |
| `CourseDetail.tsx` | `/app/courses/:id` | Diretoria (Conteúdo / Configurações / Alunos / Perguntas) |
| `MeusCursos.tsx` | `/app/portal/cursos` | Associado |
| `CoursePlayer.tsx` | `/app/portal/cursos/:enrollmentId/lessons/:lessonId` | Associado |
| `TenantSiteCourses.tsx` | `/site/cursos` | Site público |
| `TenantSiteCourseDetail.tsx` | `/site/cursos/:slug` | Site público |
| `TenantSiteCertificate.tsx` | `/site/certificados?codigo=` | Site público |

Componentes em `frontend/src/components/courses/` — `RichTextEditor` (contentEditable, sem
dependência externa; HTML sanitizado no backend), `LessonEditorModal`, `CourseSettingsForm`,
`CourseStudents`, `QuestionsInbox`, `LessonContent`, `LessonQuiz`, `LessonDiscussion`.
Estilos em `Courses.css`, complementando `Dashboard.css`.

---

## Testes

```bash
docker compose exec -T backend python -m pytest courses/tests.py -q -p no:logging
```

---

## Pendente

- Arrastar e soltar para reordenar (hoje: setas)

Feito em 2026-10-16: QR code de verificação no PDF, verificação unificada em `/api/certificados/{codigo}/`
(cursos e eventos) e e-mail de matrícula — ver
[`CHANGELOG_CONTATOS_SUPORTE_MENSAGENS_2026_10.md`](../changelog/CHANGELOG_CONTATOS_SUPORTE_MENSAGENS_2026_10.md).
