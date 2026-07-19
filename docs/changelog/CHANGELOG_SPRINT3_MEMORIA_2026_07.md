# Sprint 3 — Memória Institucional (H1)

**Data:** 2026-07-12

## Entregas

### Backend `memoria/`
- API CRUD `ContextoHistorico` com validação H1 (motivo obrigatório em decisões)
- Timeline automática ao criar contexto
- Arquivamento automático ao encerrar mandato
- Filtros: mandato, tipo, busca textual, tags

### Frontend
- `MemoriaInstitucional.tsx` — página principal (nova rota padrão `/app/memoria`)
- Abas Registros + Timeline
- Formulário guiado com campos decisão/motivo

### Demo ABCiber
- 3 registros de exemplo no `init_sistema_tenant.sh`

## Endpoints novos

```
GET/POST  /api/memoria/contextos/
POST      /api/memoria/contextos/{id}/arquivar/
GET       /api/memoria/timeline/?mandato={uuid}
GET       /api/memoria/timeline/por_mandato_ativo/
```

## Nota sobre Onboarding

Mantido no menu mas não é mais a página inicial — foco em Memória Institucional conforme priorização do usuário.
