# Changelog — MandatoDetail + H2 deep-links + Snapshot eventos (2026-07)

## Entregue

### Backend
- `Mandato.criar_snapshot` inclui `dados.eventos` (ativos: `inscricoes_abertas`, `cfp_aberto`, `em_avaliacao` + lista resumida)

### Frontend
- `/app/mandatos/:id` — `MandatoDetail.tsx`: cargos, timeline (`/api/memoria/timeline/?mandato=`), snapshots (resumo)
- Links na lista / banner do mandato ativo
- Onboarding H2 deep-links: snapshot → mandato anterior; membros; finance; eventos; memória

## Checklist manual ABCiber

1. Login `diretoria@abciber.org.br` / `abciber123` (host tenant)
2. Mandatos → abrir um card → ver cargos + timeline + snapshots
3. Onboarding (se houver transição): links abrem Membros / Finance / Eventos / Memória / mandato anterior
4. Snapshot (transição ou API `snapshot_manual`) contém chave `eventos`

## Fora de escopo

- Stripe / adminpanel
- Seletor histórico na página Memória
- Botão “snapshot manual” na UI
- Ponte User↔Membro
