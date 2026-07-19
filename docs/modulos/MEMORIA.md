# Módulo Memória Institucional — Documentação Técnica

> **Hipótese:** H1 — Preservação ativa de conhecimento institucional  
> **App Django:** `backend/memoria/`

---

## Conceito

Cada `ContextoHistorico` responde às perguntas da pesquisa PIPE:

| Campo | Pergunta |
|-------|----------|
| `autor` | Quem registrou/decidiu? |
| `decisao` | O que foi decidido? |
| `motivo` | Por quê? (obrigatório para tipo `decisao`) |
| `mandato` | Em qual gestão? |
| `tags` | Como encontrar depois? |

Ao criar um contexto vinculado a um mandato, um evento é adicionado automaticamente à `TimelineInstitucional`.

---

## API REST

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/memoria/contextos/` | Lista (filtros: `mandato`, `tipo`, `q`, `tags`) |
| POST | `/api/memoria/contextos/` | Cria registro (autor = usuário logado) |
| GET | `/api/memoria/contextos/{id}/` | Detalhe |
| POST | `/api/memoria/contextos/{id}/arquivar/` | Arquiva sem deletar |
| GET | `/api/memoria/contextos/decisoes_recentes/` | Últimas decisões |
| GET | `/api/memoria/timeline/` | Timeline (`?mandato=uuid`) |
| GET | `/api/memoria/timeline/por_mandato_ativo/` | Timeline do mandato ativo |

---

## Arquivamento Automático (H1)

Ao encerrar um mandato (`Mandato.encerrar()`):
1. Snapshot final é criado
2. Todos os contextos não arquivados do mandato são marcados `arquivado=True`
3. Evento na timeline documenta quantos registros foram preservados

Implementação: `memoria/services.py` → `arquivar_contextos_do_mandato()`

---

## Frontend

| Componente | Rota |
|------------|------|
| `MemoriaInstitucional.tsx` | `/app/memoria` (página inicial do app) |

Abas: **Registros** (CRUD + busca) e **Timeline** (cronológica).  
UI: `dashboard-page`, `dashboard-tabs`, `list-card` — [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

> Timeline por mandato na tela **Mandatos** (`MandatoDetail`) ainda **não** existe; vive aqui na aba Timeline.

---

**Última atualização:** 2026-07-14
