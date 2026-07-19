# Módulo Documents

> Documentos institucionais (extrato do WellSaaS `business.Document`).

## Modelo

`Document`: `title`, `file` (`documents/%Y/%m/%d/`), `file_type`, `description`, `uploaded_by`, FK opcional `membro`, `audience` (`geral`|`diretoria`|`membro`).

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /api/documents/` | CRUD (board/admin) |
| `GET /api/documents/{id}/download/` | Download autenticado |
| `GET /api/documents/meus/` | Gerais + diretoria (se board) + docs do próprio membro |
| `GET /api/documents/meus/{id}/download/` | Download portal |

Multipart + Form parsers; limite ~10MB.

## Frontend

| Rota | Público |
|------|---------|
| `/app/documents` | Diretoria — CRUD |
| `/app/portal/documentos` | Associado — `meus/` read-only |

---

**Última atualização:** 2026-07-15
