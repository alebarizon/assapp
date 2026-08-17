# Changelog — Landing SaaS Gesttora (2026-07-24)

## Resumo

Landing pública do produto **Gesttora** em `/`. Domínio de produção: **`gesttora.vertent.com.br`** (DNS A → droplet). Conteúdo estático em PT-BR. **CMS do website da associação (tenant) fica para depois.**

## O que entrou

- Rota pública `/` → `GesttoraLanding`
- Copy em `frontend/src/content/gesttoraLanding.ts`
- Seções: Navbar, Hero, Sobre, Benefícios para as Associações, Benefícios, Contato, Footer
- CTAs → `/signup` e `/login`
- Form de contato demo (sem API)
- Fontes Fraunces + Outfit
- Login rebranded **Gesttora** (sem PIPE/FAPESP na UI pública)
- Contato: `contato@gesttora.vertent.com.br`

## Ajustes de copy (pós-entrega)

- Título da seção de funcionalidades: **Benefícios para as Associações** (sem referências H1/H2/H3 na landing)
- Rodapé e domínio: `gesttora.vertent.com.br`

## Fora de escopo (adiado)

- `adminpanel` / `LandingPageContent` / API pública de landing
- Stripe / planos na landing
- Website CMS do tenant (`website_cms`)
- HTTPS (Let's Encrypt) — ver [`DEPLOY_DIGITALOCEAN.md`](../guias/DEPLOY_DIGITALOCEAN.md#domínio--https-adiado--retomar-depois)

## Como ver

| Ambiente | URL |
|----------|-----|
| Local | http://localhost:5174/ |
| Produção | http://gesttora.vertent.com.br/ |
| Staging | http://159.203.183.184:8080/ |
