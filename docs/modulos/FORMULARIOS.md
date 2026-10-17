# Módulo Formulários — Gesttora

> **Status:** MVP (2026-10) — adaptado do QPC do WellSaaS (`business/qpc_*`)  
> **App Django:** `backend/formularios/` (TENANT)

---

## Conceito

Formulários da associação: pesquisas, avaliação de eventos, consultas aos associados.
Do QPC foram reaproveitados o construtor (seções → perguntas), o fluxo por token e o
salvar rascunho/enviar. Alertas clínicos e importação para anamnese ficaram de fora.

### Distribuição (combináveis)

| Canal | Como funciona | Origem gravada |
|-------|---------------|----------------|
| Link público | `public_token`; qualquer pessoa responde; nome/e-mail opcionais (`pedir_identificacao`) | `link_publico` |
| Portal | `disponivel_no_portal`; todo associado vê em “Formulários”; uma resposta por associado | `portal` |
| Convite | `Resposta` pré-criada por associado; aparece no portal e tem link pessoal (`Resposta.token`) | `convite` |

Convite e portal compartilham a mesma resposta (restrição única `formulario + membro`).

### Regras

- Status: `rascunho` → `publicado` (recebe respostas) → `encerrado`. `encerra_em` encerra automaticamente.
- Publicar exige ao menos uma pergunta.
- Tipos: texto curto/longo, número, e-mail, data, escolha única, múltipla escolha, escala (0/1 até 3–10).
- Validação no backend por tipo (opção existente, faixa da escala, e-mail, data ISO) e obrigatórias só no envio.
- Editar perguntas preserva ids (as respostas continuam ligadas); remover uma pergunta apaga as respostas dela.
- `evento` (opcional) liga o formulário a um `EventoAcademico`; a aba **Avaliação** do evento cria um
  formulário com perguntas-modelo e link público anônimo.
- Rotas públicas com limite de 60 requisições/min por IP (`DEFAULT_THROTTLE_RATES.formularios_public`).

---

## API REST (`/api/formularios/`)

### Diretoria (`IsBoardOrAdmin`)

| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /api/formularios/` | Lista (`?status=`, `?evento=`, `?search=`) / cria |
| `GET/PATCH/DELETE /api/formularios/{id}/` | Detalhe; `PATCH` com `secoes` sincroniza a estrutura |
| `POST /api/formularios/{id}/duplicar/` | Cópia em rascunho |
| `GET/POST /api/formularios/{id}/convites/` | Convites / `{membros: [ids]}` ou `{todos_ativos: true}` |
| `GET /api/formularios/{id}/respostas/` | Respostas enviadas com valores |
| `DELETE /api/formularios/{id}/respostas/{resposta}/` | Excluir resposta |
| `GET /api/formularios/{id}/resumo/` | Consolidação por pergunta (contagem, média, textos) |
| `GET /api/formularios/{id}/exportar/` | CSV (`;`, UTF-8 com BOM para o Excel) |

### Associado

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/formularios/my/` | Formulários do portal + convites, com a situação |
| `GET /api/formularios/my/{id}/` | Estrutura + respostas salvas |
| `POST /api/formularios/my/{id}/salvar/` · `enviar/` | `{answers: {pergunta_id: valor}}` |

### Público (`?schema=`)

| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /api/formularios/public/f/{public_token}/` | Link aberto (`{nome, email, answers}`) |
| `GET/POST /api/formularios/public/r/{token}/` | Convite (`{answers, enviar}`; permite rascunho) |

---

## Frontend

| Página | Rota | Público |
|--------|------|---------|
| `Formularios.tsx` | `/app/formularios` | Diretoria |
| `FormularioDetail.tsx` | `/app/formularios/:id` | Diretoria (Perguntas / Configurações / Distribuição / Respostas) |
| `MeusFormularios.tsx` | `/app/portal/formularios` | Associado |
| `PortalFormulario.tsx` | `/app/portal/formularios/:id` | Associado |
| `PublicFormulario.tsx` | `/site/formularios/:token` e `/site/formularios/convite/:token` | Sem login (não depende do site CMS) |

Componentes em `frontend/src/components/formularios/`: `FormBuilder`, `FormResponder`,
`ResultadosResumo`, `Formularios.css`. Aba **Avaliação** em `EventoDetail.tsx`.

---

## Testes

```bash
docker compose exec -T backend python -m pytest formularios/tests.py -q -p no:logging
```

---

## Pendente

- Envio dos convites por e-mail (hoje: link pessoal copiado pela diretoria + portal)
- Upload de arquivo como tipo de pergunta (existia no QPC; fora do MVP por segurança do link público)
- Lógica condicional entre perguntas
