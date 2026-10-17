# Changelog — Usuários e perfis de acesso (2026-10-16)

Gestão da equipe da associação com perfis acumuláveis: **gestor** (permissão máxima), **diretoria**,
**administrativo** e **financeiro**. Modelo inspirado na equipe da clínica do WellSaaS
(`business/clinic_access.py`). Detalhes em [`USUARIOS_PERFIS.md`](../modulos/USUARIOS_PERFIS.md).

## Decisões
- Matriz de módulos por perfil aprovada como proposta (ver doc do módulo).
- Um usuário pode ter **vários perfis**; vale o maior nível (`total` > `leitura`).
- Cargo no mandato **só sugere** perfil (presidente → gestor, secretário → administrativo,
  tesoureiro/conselho fiscal → financeiro, demais → diretoria); o gestor decide.
- Entrada de usuários por **convite por e-mail** com link para definir senha; também “esqueci a senha”.

## Backend
- `accounts/access.py`: perfis, módulos, `MATRIZ`, `SUGESTAO_POR_CARGO`, `perfis_do_user`,
  `nivel_acesso`, `modulos_do_user`, `pode_acessar`, `is_gestor`.
- `User.perfis` (ArrayField). Migration `accounts.0002_user_perfis` preenche contas existentes:
  `association_admin → ["gestor"]`, `board_member → ["diretoria"]` (fallback igual em runtime).
- `mandatos.permissions.IsBoardOrAdmin` passou a checar `view.modulo` (str ou tupla); `leitura`
  libera só métodos seguros; views sem `modulo` exigem gestor ou diretoria.
- `modulo = "..."` declarado em todas as views do painel (membros, documents, website, formularios,
  mensagens, ecommerce, finance, mandatos, contatos, eventos, courses, memoria, support).
  `AnuidadeViewSet` aceita `("membros", "financeiro")`.
- `accounts/equipe.py` + `accounts/equipe_views.py`:
  - `GET/POST /api/auth/equipe/`, `PATCH /api/auth/equipe/{id}/`,
    `POST .../reenviar-convite/`, `GET /api/auth/equipe/perfis/` (só gestor; sem paginação).
  - `POST /api/auth/senha/esqueci/` (sempre 200) e `GET/POST /api/auth/senha/definir/`
    (valida link / define senha e já autentica). Limite `senha_public` 10/hora.
  - Link: `{FRONTEND_URL}/definir-senha?schema=&uid=&token=` (`default_token_generator`, uso único).
  - Regras: sempre ao menos um gestor ativo; ninguém desativa o próprio acesso; e-mail de
    associado/parecerista é promovido à equipe mantendo a senha.
- `UserSerializer` (login e `/me`) expõe `perfis` e `modulos`.
- Signup cria o dono com `perfis=["gestor"]`. `POST /api/auth/setup/` exige gestor; diretores
  cadastrados no setup recebem perfil sugerido pelo cargo, senha inutilizável e convite por e-mail
  (antes recebiam senha aleatória e não conseguiam entrar).

## Frontend
- Tipos `PerfilAcesso`, `NivelAcesso`, `ModuloPainel` em `types/index.ts`; `types/equipe.ts`;
  `services/equipe.ts`.
- `utils/roles.ts`: `podeVer`, `podeEditar`, `isGestor`, `homePathForUser` (substitui
  `homePathForRole`; leva cada perfil à primeira tela permitida).
- `utils/modulos.ts`: `BOARD_NAV` com módulo por item, `moduloDaRota`, rótulos/descrições dos perfis.
- `AppLayout`: menu filtrado pelo perfil, item **Usuários e perfis**, tela “Seu perfil não tem
  acesso a este módulo” em rota proibida, aviso de somente leitura, cabeçalho mostra os perfis.
- `pages/Usuarios.tsx` (`/app/usuarios`) + `components/usuarios/Usuarios.css`: convite, edição de
  perfis com sugestão do cargo, reenviar convite, desativar/reativar, tabela “O que cada perfil acessa”.
- `pages/EsqueciSenha.tsx`, `pages/DefinirSenha.tsx` + `components/auth/AuthShell.tsx`;
  link “Esqueci a senha” no login.

## Verificação
- 81 testes de backend ok (16 novos em `accounts/test_equipe.py`: matriz, permissões por módulo,
  convite + definição de senha, promoção de associado, último gestor, desativação, esqueci a senha).
- `tsc` + `vite build` ok.
- Navegador:
  - perfil financeiro vê só Membros, Financeiro, Loja, Documentos e Suporte;
  - aviso de leitura em Membros e bloqueio de Contatos/Usuários;
  - link de senha recusado na segunda vez;
  - gestor vê a matriz correta e é barrado ao remover o último gestor;
  - convite pela tela funciona.
- Corrigido após o teste: erro de perfil aparecia atrás do modal; botões do rodapé sem estilo.

## Dados de teste no tenant `demo`
- `fernanda.tesouraria@example.org` (perfil financeiro). Senha definida pelo teste automatizado;
  para entrar, use “Esqueci a senha” e copie o link do log do backend (e-mail no console em dev).

## Pendente
- Esconder botões de criar/editar nas páginas em modo leitura (hoje o backend recusa com 403).
- Convidar um parecerista para a equipe troca o `role` e ele perde o acesso de parecerista.
