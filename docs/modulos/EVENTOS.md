# Módulo Eventos — Documentação Técnica

> **Hipótese H3** — Integração nativa membros + eventos + CFP + anais

---

## Fluxo Integrado

```
EventoAcademico
  → abrir_cfp
  → SubmissaoTrabalho (vinculada a Membro)
  → atribuir_parecerista
  → concluir_parecer
  → gerar_anais (trabalhos aceitos)
```

## API REST

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/eventos/eventos/resumo/` | KPIs |
| `GET/POST /api/eventos/eventos/` | Lista / cria eventos |
| `POST /api/eventos/eventos/{id}/abrir_cfp/` | Abre Call for Papers |
| `GET /api/eventos/eventos/{id}/submissoes/` | Submissões do evento |
| `POST /api/eventos/eventos/{id}/gerar_anais/` | Publica anais |
| `POST /api/eventos/submissoes/` | Nova submissão |
| `POST /api/eventos/submissoes/{id}/submeter/` | Submete trabalho |
| `POST /api/eventos/submissoes/{id}/atribuir_parecerista/` | Atribui parecer |
| `POST /api/eventos/pareceres/{id}/concluir/` | Conclui parecer |

## Frontend

| Página | Rota |
|--------|------|
| `Eventos.tsx` | `/app/eventos` |
| `EventoDetail.tsx` | `/app/eventos/:id` |

UI: padrão WellSaaS — [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

## Status do Evento

`rascunho` → `cfp_aberto` → `em_avaliacao` → `anais_publicados`

---

**Última atualização:** 2026-07-14
