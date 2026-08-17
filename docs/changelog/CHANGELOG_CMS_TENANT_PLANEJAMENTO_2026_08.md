# Changelog — Planejamento CMS do Tenant (2026-08-17)

> Decisão de produto: website público por associação, menu estilo ABCiber, entrega incremental.

---

## Contexto

- Landing **Gesttora** (`/`) continua estática — produto SaaS.
- **Website do tenant** passa a ser especificado para Fase 2+ do produto comercial (além do PIPE).
- Referência: [ABCiber — site](https://abciber.org.br/site/).

---

## Decisões

1. **Menu institucional** com: A Instituição (diretoria atual, outras diretorias, história), Notícias, Eventos, Publicações, Certificados, Anais, Parcerias, Associe-se, Contato.
2. **Home** com seções: notícias, publicações, parcerias (logos), associe-se, contato — além de hero/sobre.
3. **Fase 1:** conteúdo **fake fixo** em React (`/site/*`); **Fase 2+:** CMS (`website_cms` WellSaaS) + APIs públicas + módulos novos.
4. **Integração** com módulos já existentes: `mandatos`, `memoria`, `eventos`, `ecommerce` — não duplicar domínio operacional.
5. **Novos módulos** (backlog): `publicacoes`, `certificados`, `parcerias` (ou subconjunto via CMS).

---

## Documentação criada/atualizada

| Arquivo | Ação |
|---------|------|
| [`docs/modulos/WEBSITE_CMS_TENANT.md`](../modulos/WEBSITE_CMS_TENANT.md) | **Novo** — especificação completa |
| [`cursor-readme.md`](../../cursor-readme.md) | Rotas `/site`, link CMS |
| [`README.md`](../../README.md) | Roadmap CMS detalhado |
| [`docs/referencia/STATUS_SPRINTS_FASE1.md`](../referencia/STATUS_SPRINTS_FASE1.md) | Fase 2 / Sprint CMS |
| [`docs/referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md`](../referencia/FLUXO_ASSINATURA_SETUP_TRANSICAO.md) | Mapa capacidades |
| [`docs/modulos/ECOMMERCE.md`](ECOMMERCE.md) | Link Associe-se ↔ site |

---

## Não implementado neste changelog

- Código frontend `/site`
- App `website_cms` backend
- Módulos `publicacoes`, `certificados`, `parcerias`

**Próximo passo:** implementar Fase 1 (site fake estático).
