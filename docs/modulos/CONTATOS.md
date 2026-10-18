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
GET        /api/contatos/{id}/ficha/         ficha 360: resumo + linha do tempo
CRUD       /api/contatos/etiquetas/
POST       /api/contatos/public/?schema=     formulário do site (sem login)
```

## Frontend

- `/app/contatos` — funil (cartões por etapa), filtros, cadastro manual, gestão de etiquetas.
- `/app/contatos/:id` — etapa, responsável (“Assumir atendimento”), dados, etiquetas, histórico/anotações,
  converter em associado e **Ficha 360**.
- Site público: formulário na seção **Contato** da home (`ContatoSiteForm`).

## Ficha 360

`contatos/ficha.py` junta tudo o que a associação sabe da pessoa:

- Contatos com o mesmo e-mail (outras mensagens do site, com link).
- Se o contato está vinculado a um associado: a linha do tempo do membro (`membros/timeline.py`) e a
  situação da carteirinha (em dia / pendente / inativo), além de compras pagas.
- Se não está: inscrições em eventos, trabalhos submetidos e formulários respondidos com o mesmo e-mail,
  e o aviso de que já existe um associado com esse e-mail (para vincular pelo “Converter em associado”).

Testes: `contatos/tests.py`, `contatos/test_ficha.py`.
