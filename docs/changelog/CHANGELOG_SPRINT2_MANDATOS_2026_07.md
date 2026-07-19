# Sprint 2 — Mandatos + Onboarding (PIPE Fase 1)

**Data:** 2026-07-12

## Entregas

### Infraestrutura
- Docker Compose (`docker-compose.yml` + `docker-compose.dev.yml`)
- Backend Django com `django-tenants`, JWT, middleware multi-tenant
- Ports: backend `8001`, frontend `5174` (evita conflito com WellSaaS)
- Script `./scripts/init_sistema_tenant.sh` — tenants `sistema` + demo `abciber`

### API REST `/api/mandatos/`
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/mandatos/` | GET/POST | Lista / cria mandatos |
| `/mandatos/ativo/` | GET | Mandato ativo |
| `/mandatos/{id}/ativar/` | POST | Ativa mandato |
| `/mandatos/{id}/encerrar/` | POST | H1 — snapshot + encerramento |
| `/mandatos/{id}/transicao/` | POST | H1+H2 — inicia transição + onboarding |
| `/mandatos/{id}/snapshots/` | GET | Snapshots auditáveis |
| `/transicoes/em_andamento/` | GET | Transição ativa (modo Nova Diretoria) |
| `/onboarding/?transicao={id}` | GET | Etapas filtradas por perfil (H2) |
| `/onboarding/{id}/concluir/` | POST | Conclui etapa |

### Frontend
- `OnboardingWizard.tsx` — interface adaptativa H2 (iniciante/intermediário/avançado)
- `Mandatos.tsx` — gestão e início de transição
- `Login.tsx` — autenticação JWT

### Credenciais demo (após init)
| Tenant | Email | Senha |
|--------|-------|-------|
| sistema | admin@assapp.local | admin123 |
| abciber | diretoria@abciber.org.br | abciber123 |

## Como subir

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
./scripts/init_sistema_tenant.sh
# Frontend: docker build -f frontend/Dockerfile.dev -t assapp-frontend-dev:local ./frontend
```

## Validação API (testada)

- Login ABCiber ✅
- GET mandato ativo ✅
- POST transição → 7 etapas onboarding ✅
