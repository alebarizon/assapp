# Usuários e perfis de acesso

Controle de quem acessa o painel da associação e o que cada pessoa pode fazer.
Modelo inspirado no módulo de equipe da clínica do WellSaaS (`business/clinic_access.py`):
perfil → módulos permitidos, checado numa permissão única do DRF.

## Conceitos

- `User.role` continua separando **equipe** (`association_admin`, `board_member`), **associado**
  (`member`), **parecerista** (`reviewer`) e **superadmin**.
- `User.perfis` (lista, acumulável) define o acesso da equipe:

| Perfil | Para quem |
|---|---|
| `gestor` | Permissão máxima, inclusive usuários, setup e configurações |
| `diretoria` | Todos os módulos operacionais; financeiro e loja só consulta |
| `administrativo` | Secretaria: associados, eventos, cursos, formulários, contatos, mensagens, site, documentos |
| `financeiro` | Tesouraria: financeiro, loja, anuidades, documentos; associados só consulta |

Com vários perfis, vale o **maior nível** concedido por qualquer um deles (`total` > `leitura`).
Superadmin é tratado como gestor. Contas sem `perfis` (anteriores à feature) caem em
`association_admin → gestor` e `board_member → diretoria`; a migration `accounts.0002` já preenche isso.

## Matriz

Fonte de verdade: `backend/accounts/access.py` (`MATRIZ`). A tela de usuários exibe a matriz
via `GET /api/auth/equipe/perfis/`.

| Módulo | Gestor | Diretoria | Administrativo | Financeiro |
|---|---|---|---|---|
| usuarios, configuracoes, integracoes | total | — | — | — |
| memoria, mandatos, onboarding | total | total | leitura | — |
| membros | total | total | total | leitura |
| eventos, cursos, formularios, contatos, mensagens, website | total | total | total | — |
| documentos | total | total | total | total |
| financeiro, loja | total | leitura | — | total |
| suporte | total | total | total | total |

Anuidades (`AnuidadeViewSet`) aceitam `membros` **ou** `financeiro`.

## Backend

- Cada view do painel declara `modulo = "<chave>"` (ou tupla). `mandatos.permissions.IsBoardOrAdmin`
  verifica `pode_acessar(user, modulo, method)`; `leitura` libera só métodos seguros.
  Views sem `modulo` exigem gestor ou diretoria.
- `GET /api/auth/me/` e o login devolvem `perfis` e `modulos` (`{modulo: "total"|"leitura"}`).
- `POST /api/auth/setup/` exige gestor. Diretores cadastrados no setup recebem o perfil sugerido
  pelo cargo e um convite por e-mail.

### Endpoints (`/api/auth/`)

| Método | Rota | Uso |
|---|---|---|
| GET | `equipe/` | Lista a equipe (gestor) |
| POST | `equipe/` | Convida `{email, first_name, last_name, perfis}` |
| PATCH | `equipe/{id}/` | `perfis`, `is_active`, nome |
| POST | `equipe/{id}/reenviar-convite/` | Reenvia o link |
| GET | `equipe/perfis/` | Perfis, módulos, matriz e sugestão por cargo |
| POST | `senha/esqueci/` | `{email, schema?}` — sempre 200 |
| GET/POST | `senha/definir/` | Valida o link / define a senha e autentica |

Regras:
- Sempre deve existir ao menos um gestor ativo (não dá para remover o perfil nem desativar o último).
- Ninguém desativa o próprio acesso.
- Convidar um e-mail de associado/parecerista promove a conta para a equipe mantendo a senha.
- Link de senha usa `default_token_generator` (uso único; expira em `PASSWORD_RESET_TIMEOUT`).
  Formato: `{FRONTEND_URL}/definir-senha?schema=&uid=&token=`.
- Sugestão por cargo (`SUGESTAO_POR_CARGO`): presidente → gestor, secretário → administrativo,
  tesoureiro/conselho fiscal → financeiro, demais → diretoria. É só sugestão; o gestor decide.

## Frontend

- `/app/usuarios` — `pages/Usuarios.tsx`: convite, edição de perfis (com sugestão do cargo),
  reenviar convite, desativar/reativar, tabela "O que cada perfil acessa".
- `/esqueci-senha`, `/definir-senha` — telas públicas (`components/auth/AuthShell.tsx`).
- `utils/modulos.ts`: `BOARD_NAV` com o módulo de cada item; `moduloDaRota`.
- `utils/roles.ts`: `podeVer`, `podeEditar`, `isGestor`, `homePathForUser`.
- `AppLayout` filtra o menu, bloqueia rotas sem acesso e mostra aviso de "somente leitura".

## Pendente

- Esconder botões de criação/edição nas páginas em modo leitura (hoje o backend recusa com 403).
