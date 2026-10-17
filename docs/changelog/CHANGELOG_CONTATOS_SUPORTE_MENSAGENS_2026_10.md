# Changelog — Contatos, Suporte, Mensagens e pendências (2026-10-16)

## Novos módulos

- **Contatos** (`contatos/`, TENANT): formulário de contato no site, funil, etiquetas, histórico,
  conversão em associado. Ver [`CONTATOS.md`](../modulos/CONTATOS.md).
- **Suporte** (`support/`, SHARED/public): chamados associação → equipe Gesttora com anexos, notas internas
  e avisos por e-mail. Ver [`SUPORTE.md`](../modulos/SUPORTE.md).
- **Mensagens** (`mensagens/`, TENANT): conversas diretoria ↔ associado, envio para vários/todos os ativos.
  Ver [`MENSAGENS.md`](../modulos/MENSAGENS.md).

## Pendências resolvidas

### Certificados de evento
- `EventoAcademico`: `certificado_habilitado`, `carga_horaria`.
- `InscricaoEvento`: `presente`, `certificado_codigo` (único), `certificado_emitido_em`.
- `POST /api/eventos/eventos/{id}/presencas/` (lote) e `POST .../emitir-certificados/` (gera códigos para
  presentes e envia e-mail); `GET /api/eventos/inscricoes/{id}/certificado/` (PDF).
- `InscricaoEventoSerializer` preenche nome/e-mail a partir do associado e bloqueia e-mail duplicado no evento.
- Frontend: aba **Inscrições e certificados** no `EventoDetail` (`components/eventos/InscricoesCertificados.tsx`).

### Verificação pública unificada + QR code
- `core/certificados_views.py`: `GET /api/certificados/{codigo}/?schema=` (cursos e eventos) e
  `GET /api/certificados/{codigo}/pdf/?schema=` (download). Limite `certificados_public` 30/min.
- `core/certificates.py`: parâmetro `verify_url` desenha QR code no PDF; `certificate_verify_url()`.
- Certificados de curso também passam a ter QR. `/site/certificados` mostra cursos e eventos e oferece
  “Baixar certificado (PDF)”. O endpoint antigo `/api/courses/public/certificates/` continua ativo.

### E-mails transacionais
- `core/emails.py`: `enviar_email()` (HTML simples + botão, falha só registra log), `frontend_url()`,
  `nome_associacao()`. Novas settings: `FRONTEND_URL`, `SUPPORT_EMAIL`.
- Convites de formulário enviam e-mail com o link pessoal (somente com formulário publicado);
  `reenviar_pendentes` reenvia a quem não respondeu (botão “Reenviar e-mail aos pendentes”).
- Matrícula em curso (criada ou reativada) envia e-mail de boas-vindas após o commit.

### Idioma das mensagens de erro
- `LANGUAGES = [("pt-br", ...)]`: o `LocaleMiddleware` não troca mais para inglês pelo `Accept-Language`.

## Outros
- `utils/download.ts` (`downloadBlob`) compartilhado por cursos, eventos e certificados.
- `.status-badge-interessado` em `index.css`.

## Verificação
- 65 testes de backend ok (`contatos`, `support`, `mensagens`, `core/test_pendencias.py`, `formularios`, `courses`).
- `tsc` + `vite build` ok.
