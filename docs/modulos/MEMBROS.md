# Módulo Membros — Documentação Técnica

> **Sprint 4** — Gestão de associados, filiações e anuidades  
> **Compliance:** LGPD (consentimento obrigatório), CPF validado

---

## Modelos

| Modelo | Descrição |
|--------|-----------|
| `Membro` | Dados do associado (nome, email, CPF, Lattes, ORCID) |
| `Filiacao` | Histórico de filiação vinculado a mandato |
| `Anuidade` | Cobrança anual por filiação |
| `LembreteAnuidade` | Registro de cada lembrete de cobrança enviado (único por anuidade + etapa) |

## Valores padrão de anuidade

| Tipo | Valor |
|------|-------|
| Efetivo | R$ 80,00 |
| Estudante | R$ 40,00 |
| Honorário | Isento |
| Institucional | R$ 200,00 |

## API REST

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/membros/membros/resumo/` | KPIs do quadro |
| `GET/POST /api/membros/membros/` | Lista / cria membro + filiação |
| `GET /api/membros/membros/{id}/` | Detalhe com histórico |
| `POST /api/membros/anuidades/gerar_lote/` | Gera anuidades do ano |
| `POST /api/membros/anuidades/atualizar_vencidas/` | Marca inadimplentes |
| `POST /api/membros/anuidades/{id}/registrar_pagamento/` | Registra pagamento (idempotente) |
| `POST /api/membros/anuidades/enviar_lembretes/` | Marca vencidas e dispara a régua agora |
| `GET /api/membros/membros/{id}/timeline/` | Linha do tempo do associado |

## Automação

1. **Gerar lote** — cria anuidades para todas filiações ativas/inadimplentes sem cobrança no ano
2. **Atualizar vencidas** — anuidades pendentes após vencimento → `vencida`; filiação → `inadimplente`
3. **Registrar pagamento** — anuidade `paga`; reativa filiação inadimplente
4. **Régua de cobrança** — e-mails 30 e 15 dias antes, no dia e 15 dias após o vencimento
   (`membros/services.py::enviar_lembretes_anuidade`). Envia só a etapa mais recente ainda não enviada
   (nunca uma anterior depois de uma posterior), ignora anuidades pagas, isentas, de inativos ou vencidas
   há mais de 45 dias, e só registra `LembreteAnuidade` quando o e-mail sai — falha é retentada no dia seguinte.
5. **Pagamento online** — o associado paga pelo portal (Pix, cartão, boleto via Asaas); a confirmação do
   gateway quita a anuidade e lança no financeiro. Ver [`PAGAMENTOS.md`](PAGAMENTOS.md).

### Execução diária (serviço `agendador`)

Em staging e produção o serviço `agendador` do compose roda `regua_anuidades` uma vez por dia, a partir
de `REGUA_HORA` (padrão 8h, Brasília). Se a primeira tentativa do dia falhar, repete no minuto seguinte.
Enquanto o `EMAIL_BACKEND` não entrega de fato (console, locmem, arquivo), roda com `--sem-email`: só marca
vencidas/inadimplentes, sem registrar lembretes que não saíram. À mão:

```bash
docker compose exec -T backend python manage.py regua_anuidades            # todos os tenants
docker compose exec -T backend python manage.py regua_anuidades --schema x # um tenant
docker compose exec -T backend python manage.py regua_anuidades --sem-email # só marca vencidas
```

Roda `atualizar_anuidades_vencidas` + régua em cada tenant ativo. É idempotente: pode rodar mais de uma vez por dia.

## Linha do tempo do associado

`membros/timeline.py::timeline_membro` junta, do mais recente ao mais antigo: filiações, anuidades
(pagas/vencidas), lembretes, cobranças online, pedidos, inscrições e certificados de eventos, submissões,
cursos, conversas, respostas de formulários e contatos do CRM. Exibida em `MembroDetail.tsx`.

## Carteirinha digital

`membros/carteirinha.py` (migration `membros/0004`: `Membro.matricula`, `Membro.carteirinha_codigo`).

- Matrícula sequencial e código do QR atribuídos na primeira emissão (`garantir_carteirinha`).
- Situação: **em dia** (`membro_adimplente`), **pendente** (filiação ativa com anuidade em atraso) ou **inativa**
  (membro inativo, filiação cancelada/suspensa ou inexistente).
- Validade: fim do último ano pago/isento, ou o vencimento da próxima anuidade ainda não vencida; honorário não
  expira. Sem anuidade registrada, aparece "—".
- O QR aponta para `/site/carteirinha/:codigo?schema=`, que consulta a situação **no momento da leitura** — por isso o
  PDF impresso não traz a situação, só a validade. A verificação mostra nome, matrícula, categoria, situação e
  validade; nunca e-mail, CPF ou contato.
- "Gerar novo QR" (diretoria) troca o código; o anterior passa a responder 404.
- Apple/Google Wallet ficam para depois.

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/membros/meu/carteirinha/[pdf/]` | Associado logado: dados + QR (SVG data URI) / PDF 85,6 × 54 mm |
| `GET /api/membros/membros/{id}/carteirinha/[pdf/]` | Diretoria |
| `POST /api/membros/membros/{id}/carteirinha/renovar/` | Novo QR (invalida o anterior) |
| `GET /api/membros/public/carteirinha/{codigo}/?schema=` | Verificação pública |

## Diretório público

`membros/diretorio.py` (migrations `membros/0005` e `website/0003`).

- O associado edita no portal (`PATCH /api/membros/meu/`) instituição, área, Lattes, ORCID, telefone,
  minibiografia e o opt-in `diretorio_publico`; `diretorio_aceito_em` registra quando autorizou. A
  diretoria só vê a autorização, não a altera.
- A associação liga o diretório em Website (`WebsiteConfig.diretorio_ativo`, exige site publicado); o
  menu do site ganha o link **Associados**.
- Aparece quem autorizou e tem filiação ativa ou honorária. Exibe nome, categoria, ano de entrada,
  instituição, área, minibiografia, Lattes e ORCID — nunca e-mail, telefone ou CPF.
- Busca por nome, instituição, área ou tema, filtro por instituição, 24 por página.

| Endpoint | Descrição |
|----------|-----------|
| `GET/PATCH /api/membros/meu/` | Perfil do associado (PATCH: campos acadêmicos e opt-in) |
| `GET /api/membros/public/diretorio/?schema=&q=&instituicao=&pagina=` | Diretório (404 se desligado) |

## Frontend

| Página | Rota |
|--------|------|
| `Membros.tsx` | `/app/membros` |
| `MembroDetail.tsx` | `/app/membros/:id` (painel Carteirinha) |
| `MinhaCarteirinha.tsx` | `/app/portal/carteirinha` |
| `TenantSiteCarteirinha.tsx` | `/site/carteirinha/:codigo` |
| `MeuPerfil.tsx` (`PerfilPublicoForm`) | `/app/portal/perfil` |
| `TenantSiteDiretorio.tsx` | `/site/associados` |

UI: padrão WellSaaS (`dashboard-*`, KPIs `stats-grid`) — [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

## Pendente

- Lembretes por WhatsApp (hoje só e-mail)
- Cobrança recorrente / assinatura no cartão
- Convite SMTP para associados (User criado a partir do Membro)

## Ponte User ↔ Membro

| Campo / API | Descrição |
|-------------|-----------|
| `Membro.user` | OneToOne opcional → `User` |
| `POST /api/membros/membros/{id}/vincular_user/` | `{ user_id }` ou `{ email }` |
| `POST /api/membros/membros/{id}/desvincular_user/` | Remove vínculo |
| `GET /api/auth/me/` | `membro_id`, `membro_nome` |
| `GET /api/membros/meu/` | Perfil do associado autenticado |
| `GET /api/membros/meu/anuidades/` | Anuidades próprias (read-only) |

### Portal associado (FE)

| Rota | Função |
|------|--------|
| `/app/portal` | Home do associado |
| `/app/portal/perfil` | Perfil + anuidades |
| `/app/portal/documentos` | Docs `meus/` |

Demo: `ana.silva@usp.br` / `associado123`.

Documentos `meus/` e submissões H3 resolvem o associado via FK (com fallback por e-mail).

Ver: [`CHANGELOG_USER_MEMBRO_2026_07.md`](../changelog/CHANGELOG_USER_MEMBRO_2026_07.md) · [`CHANGELOG_PORTAL_ASSOCIADO_2026_07.md`](../changelog/CHANGELOG_PORTAL_ASSOCIADO_2026_07.md)

---

**Última atualização:** 2026-10-17
