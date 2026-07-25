# Changelog — Landing SaaS Gesttora (2026-07-24)

## Resumo

Landing pública do produto **Gesttora** em `/` (domínio futuro `gesttora.online`). Conteúdo estático fake focado em associações científicas (pilares PIPE H1/H2/H3). **CMS do website da associação (tenant) fica para depois.**

## O que entrou

- Rota pública `/` → `GesttoraLanding`
- Copy em `frontend/src/content/gesttoraLanding.ts`
- Seções: Navbar, Hero, Sobre, Funcionalidades, Benefícios, Contato, Footer
- CTAs → `/signup` e `/login`
- Form de contato demo (sem API)
- Fontes Fraunces + Outfit

## Fora de escopo (adiado)

- `adminpanel` / `LandingPageContent` / API pública de landing
- Stripe / planos na landing
- Website CMS do tenant (`website_cms`)

## Como ver

```bash
# frontend local (porta conforme compose / Vite)
open http://localhost:5174/
```
