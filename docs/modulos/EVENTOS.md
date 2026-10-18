# Módulo Eventos — Documentação Técnica

> Integração nativa membros + eventos + chamada de trabalhos + anais

---

## Fluxo Integrado

```
EventoAcademico
  → abrir_cfp (critérios com peso, nota de corte, duplo-cego, arquivo obrigatório)
  → SubmissaoTrabalho pelo autor no portal (rascunho → submeter; vinculada a Membro pelo e-mail)
  → atribuir_parecerista (bloqueia autor e coautores; e-mail ao parecerista)
  → concluir_parecer (notas 1–5 por critério → nota ponderada)
  → decidir_submissao (comissão; carta de aceite/recusa por e-mail)
  → emitir_certificados_cientificos (autoria + parecerista)
  → gerar_anais (trabalhos aceitos)
```

## API REST

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/eventos/eventos/resumo/` | KPIs |
| `GET/POST /api/eventos/eventos/` | Lista / cria eventos |
| `POST /api/eventos/eventos/{id}/abrir_cfp/` | Abre Call for Papers |
| `GET /api/eventos/eventos/{id}/submissoes/` | Submissões do evento |
| `POST /api/eventos/eventos/{id}/gerar_anais/` | Publica/atualiza anais (um registro por trabalho aceito) |
| `PATCH /api/eventos/eventos/{id}/anais/` | Dados editoriais (ISSN, ISBN, licença, apresentação, editores, cidade) |
| `GET/PATCH /api/eventos/trabalhos-publicados/?evento=` | DOI, ordem e PDF final por trabalho (multipart) |
| `GET /api/eventos/public/{slug}/anais/` | Público: sumário dos anais |
| `GET /api/eventos/public/{slug}/anais/{trabalho}/` | Público: trabalho + citações ABNT/APA/BibTeX |
| `GET /api/eventos/public/{slug}/anais/{trabalho}/pdf/` | Público: PDF final ou folha com resumo |
| `POST /api/eventos/submissoes/` | Nova submissão |
| `POST /api/eventos/submissoes/{id}/submeter/` | Submete trabalho |
| `POST /api/eventos/submissoes/{id}/atribuir_parecerista/` | Atribui parecer |
| `POST /api/eventos/pareceres/{id}/concluir/` | Conclui parecer (registro pela equipe) |
| `DELETE /api/eventos/pareceres/{id}/` | Remove parecerista (só parecer não concluído) |
| `GET /api/eventos/eventos/pareceristas/` | Candidatos a parecerista |
| `POST /api/eventos/submissoes/{id}/decidir/` | Decisão da comissão + carta ao autor |
| `GET /api/eventos/submissoes/{id}/arquivo/` | Baixa o arquivo do trabalho |
| `POST /api/eventos/eventos/{id}/emitir-certificados-cientificos/` | Certificados de autoria e de parecerista |
| `GET /api/eventos/my/chamadas/` | Autor: chamadas recebendo submissões |
| `GET/POST/PATCH/DELETE /api/eventos/my/submissoes/` | Autor: seus trabalhos (multipart; só rascunho é editável) |
| `POST /api/eventos/my/submissoes/{id}/submeter/` | Autor: envia o rascunho |
| `GET /api/eventos/my/pareceres/` | Parecerista: trabalhos atribuídos (anonimizados se duplo-cego) |
| `POST /api/eventos/my/pareceres/{id}/concluir/` | Parecerista: notas por critério + recomendação |

## Frontend

| Página | Rota |
|--------|------|
| `Eventos.tsx` | `/app/eventos` |
| `EventoDetail.tsx` | `/app/eventos/:id` (abas Chamada e Submissões: `ChamadaTrabalhos`, `SubmissoesComissao`) |
| `MeusTrabalhos.tsx` | `/app/portal/trabalhos` |
| `TenantSiteAnais.tsx` | `/site/eventos/:slug/anais` |
| `TenantSiteTrabalho.tsx` | `/site/eventos/:slug/anais/:trabalho` |
| `MeusPareceres.tsx` | `/app/portal/pareceres` (portal) e `/app/pareceres` (equipe) |

UI: padrão WellSaaS — [`UI_PADRAO_WELLSAAS.md`](../guias/UI_PADRAO_WELLSAAS.md).

## Status do Evento

`rascunho` → `cfp_aberto` → `em_avaliacao` → `anais_publicados`

---

## Inscrições, presença e certificados (2026-10)

- `EventoAcademico.certificado_habilitado` e `carga_horaria`; `InscricaoEvento.presente`,
  `certificado_codigo`, `certificado_emitido_em`.
- `POST /api/eventos/eventos/{id}/presencas/` `{inscricoes: [ids], presente}` — marca presença em lote.
- `POST /api/eventos/eventos/{id}/emitir-certificados/` `{notificar}` — gera código para presentes sem
  certificado e envia e-mail com link de download/verificação.
- `GET /api/eventos/inscricoes/{id}/certificado/` — PDF (`core/certificates.py`, com QR code).
- Verificação pública: `/site/certificados?codigo=` → `GET /api/certificados/{codigo}/`.
- Frontend: aba **Inscrições e certificados** em `/app/eventos/:id`.

---

## Hotsite, programação e inscrição pela loja (2026-10)

| Campo / modelo | Descrição |
|----------------|-----------|
| `EventoAcademico.publicado_site`, `resumo`, `capa` | Controlam o hotsite. Rascunho e cancelado nunca aparecem |
| `AtividadeProgramacao` | Grade: título, tipo, início/fim, sala, palestrantes, descrição, link de transmissão |
| Item `inscricao` da loja | Criado/atualizado por `eventos.services.salvar_item_inscricao` (preço cheio + preço de sócio) |

| Endpoint | Quem | Descrição |
|----------|------|-----------|
| `POST/DELETE /api/eventos/eventos/{id}/capa/` | Diretoria | Imagem do hotsite (multipart `capa`) |
| `POST /api/eventos/eventos/{id}/item-loja/` | Diretoria | `{price, member_price, is_active}` |
| `GET/POST/PATCH/DELETE /api/eventos/programacao/?evento=` | Diretoria | Grade |
| `GET /api/eventos/public/?schema=` | Público | Eventos publicados |
| `GET /api/eventos/public/{slug}/?schema=` | Público | Hotsite: programação, chamada de trabalhos, situação da inscrição, anais |

A inscrição fica aberta quando há item ativo na loja, status `inscricoes_abertas`/`cfp_aberto`/`em_avaliacao`,
o evento não terminou e há vagas. O associado compra pela loja; a `InscricaoEvento` é confirmada no pagamento.

Frontend: abas **Programação** e **Site e inscrição** em `EventoDetail.tsx`; páginas públicas
`/site/eventos` e `/site/eventos/:slug` (`TenantSiteEventos.tsx`, `TenantSiteEventoDetail.tsx`).

Pendente: submissão de trabalho pelo próprio autor no portal (hoje a chamada no hotsite é informativa).

---

**Última atualização:** 2026-10-17

## Chamada de trabalhos científicos (2026-10)

Regras em `backend/eventos/cientifico.py`.

- **Autor**: qualquer usuário logado do tenant submete pelo portal enquanto a chamada está aberta. Valida área,
  arquivo (PDF/DOC/DOCX/ODT até 15 MB, quando exigido) e limite por autor (rascunhos e retirados não contam).
- **Parecerista**: candidatos são a equipe, usuários com papel parecerista e associados com login. Conflito de
  interesse bloqueia o autor e coautores (por e-mail). Na chamada duplo-cega a API do parecerista não devolve autoria.
- **Notas**: cada critério recebe 1 a 5; `nota_ponderada = Σ(nota × peso) / Σ(peso)`. Sem critérios configurados,
  vale `CRITERIOS_PADRAO`. A média dos pareceres aparece para a comissão junto da nota de corte.
- **Decisão**: só a comissão muda o status (`aceito`, `aceito_com_revisoes`, `rejeitado`). A carta vai ao autor e
  aos coautores com os "comentários aos autores" dos pareceres, sem identificar pareceristas; comentários internos
  ficam só no painel. Depois da decisão, pareceres não mudam.
- **Certificados** (`CertificadoPapel`): um de autoria por trabalho aceito (com coautores no texto) e um de
  parecerista por evento. Emissão idempotente; verificação em `/site/certificados`.
- **Papel parecerista** (`reviewer`): navega só por `/app/portal/pareceres` e `/app/portal/trabalhos`.

## Anais por trabalho (2026-10)

Regras em `backend/eventos/anais.py`; modelo `TrabalhoPublicado` (migration `eventos/0005`).

- "Gerar anais" cria um `TrabalhoPublicado` por trabalho aceito, copiando título, resumo, palavras-chave e autores
  (instituição e ORCID do associado quando vinculado). Republicar atualiza os textos e **preserva slug, DOI e PDF
  final**; trabalhos que deixaram de ser aceitos saem dos anais. O registro sobrevive à exclusão da submissão.
- O PDF da submissão é copiado se for PDF; a diretoria pode trocar pelo PDF final. Sem arquivo, o site gera uma
  folha com resumo e citação (`build_trabalho_pdf`).
- Página pública só aparece se o evento está publicado no site e os anais têm `publicado_em`.
- Citações geradas no backend (`citacoes`): ABNT (trabalho em evento), APA 7 e BibTeX `@inproceedings`.
  Sobrenomes compostos com Filho/Júnior/Neto são tratados.
- A página do trabalho injeta metadados `citation_*` (Highwire) no `<head>`. Como o site é SPA, indexadores que não
  executam JavaScript não os veem; renderização no servidor fica para a etapa do DOI.
- ISSN/ISBN e DOI são informados manualmente nesta versão; depósito Crossref fica para a Onda 2.
- Anais gerados antes desta versão só têm o JSON `metadata`: clique em "Atualizar anais" para criar as páginas.
