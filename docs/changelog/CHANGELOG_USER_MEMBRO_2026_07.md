# Changelog — Ponte User ↔ Membro (2026-07)

## Entregue

- `Membro.user` OneToOne → `User` (`related_name=membro_perfil`)
- Services: `vincular_user`, `desvincular_user`, `resolver_membro_do_user` (FK + fallback e-mail com auto-link)
- API: `POST .../vincular_user/`, `POST .../desvincular_user/`
- `GET /api/auth/me/` expõe `membro_id` e `membro_nome`
- Documents `meus/` e eventos `vincular_membro_por_email` usam o resolver
- UI: `MembroDetail` vincular/desvincular
- Seed ABCiber: Membro da diretoria + vínculo

## Fora de escopo

- Convite SMTP / senha
- Auto-criar User ao cadastrar Membro
- Portal associado completo
- Sync automático de roles
