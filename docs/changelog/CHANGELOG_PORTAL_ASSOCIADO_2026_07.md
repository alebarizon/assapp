# Changelog — Portal mínimo do associado (2026-07)

## Entregue

### Backend
- `GET /api/membros/meu/` — perfil `Membro` do User autenticado
- `GET /api/membros/meu/anuidades/` — anuidades do próprio associado
- Reutiliza `GET /api/documents/meus/` (+ download)

### Frontend
- Rotas `/app/portal`, `/app/portal/perfil`, `/app/portal/documentos`
- Nav e login por role (`member` → portal; board → memoria)
- Member que acessa rotas da diretoria é redirecionado ao portal

### Seed ABCiber
- User `ana.silva@usp.br` / `associado123` (role `member`) vinculado a Ana Silva
- Documento pessoal “Comprovante de filiação (Ana)”

## Fora de escopo
- Stripe, SMTP/convite, upload pelo associado
