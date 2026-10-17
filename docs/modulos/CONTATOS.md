# Módulo Contatos

CRM leve da associação: mensagens do formulário de contato do site, interessados em filiação,
imprensa e parceiros. Adaptado de `contacts` do WellSaaS.

## Modelo (app TENANT `contatos`)

| Modelo | Campos principais |
|--------|-------------------|
| `Contato` | nome, email, telefone, instituição, assunto, mensagem, **etapa**, **origem**, etiquetas, responsável, membro (vínculo), `consentimento_lgpd`, `ultima_interacao_em` |
| `Etiqueta` | nome (único), cor |
| `Nota` | histórico do contato — `manual` (anotação), `sistema` (mudança de etapa, conversão), `mensagem` (nova mensagem pelo site) |

Etapas do funil: `novo` → `em_atendimento` → `interessado` → `convertido` · `arquivado`.
Origens: site (contato / associe-se), evento, indicação, redes sociais, cadastro manual.

## Regras

- **Deduplicação:** se já existe contato em aberto com o mesmo e-mail, a nova mensagem do site vira nota
  nele (sem duplicar o funil). Contato arquivado ou convertido → novo contato.
- Se o e-mail já pertence a um `Membro`, o contato nasce vinculado a ele.
- **Converter em associado:** vincula ao `Membro` de mesmo e-mail ou cria um novo (opcionalmente com filiação
  inicial via `criar_membro_com_filiacao`) e move para `convertido`.
- Mudança de etapa gera nota de sistema.
- Formulário público: consentimento LGPD obrigatório, campo honeypot (`website`) e limite de 10 envios/hora por IP
  (escopo `contatos_public`).
- Aviso por e-mail para `WebsiteConfig.contact_email` a cada contato/mensagem (reply-to = e-mail do contato).

## API

```
GET/POST   /api/contatos/                    lista (etapa, abertos=true, origem, assunto, etiqueta, search) · cadastro manual
GET/PATCH/DELETE /api/contatos/{id}/
GET        /api/contatos/resumo/             contagem por etapa
GET/POST   /api/contatos/{id}/notas/
POST       /api/contatos/{id}/converter/     {tipo_filiacao?}
CRUD       /api/contatos/etiquetas/
POST       /api/contatos/public/?schema=     formulário do site (sem login)
```

## Frontend

- `/app/contatos` — funil (cartões por etapa), filtros, cadastro manual, gestão de etiquetas.
- `/app/contatos/:id` — etapa, responsável (“Assumir atendimento”), dados, etiquetas, histórico/anotações,
  converter em associado.
- Site público: formulário na seção **Contato** da home (`ContatoSiteForm`).

Testes: `contatos/tests.py`.
