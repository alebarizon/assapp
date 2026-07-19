# Sprint 5 — Eventos Científicos + CFP (H3)

**Data:** 2026-07-13

## Entregas

### Backend `eventos/`
- API completa: EventoAcademico, CFP, Submissões, Pareceres, Inscrições
- Serviços: `abrir_cfp`, `submeter_trabalho`, `atribuir_parecerista`, `concluir_parecer`, `gerar_anais`
- H3: submissão vinculada a `Membro` automaticamente

### Frontend
- `Eventos.tsx` — lista e KPIs
- `EventoDetail.tsx` — CFP, submissões, pareceres, geração de anais

### Demo
- Encontro ABCiber 2026 no `init_sistema_tenant.sh`

## Fluxo de teste

1. Eventos → ver demo ou criar novo
2. Abrir CFP
3. Nova submissão (vincular membro)
4. Atribuir parecerista → Concluir parecer (aceitar)
5. Gerar anais
