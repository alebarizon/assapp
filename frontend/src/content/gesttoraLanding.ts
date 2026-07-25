/**
 * Copy estático da landing SaaS Gesttora (gesttora.online).
 * Frontend-only — sem adminpanel / API nesta rodada.
 */

export const gesttoraLanding = {
  brand: "Gesttora",
  domain: "gesttora.vertent.com.br",

  nav: {
    links: [
      { href: "#home", label: "Início" },
      { href: "#about", label: "Sobre" },
      { href: "#features", label: "Funcionalidades" },
      { href: "#benefits", label: "Benefícios" },
      { href: "#contact", label: "Contato" },
    ],
    loginLabel: "Entrar",
    signupLabel: "Começar",
    loginUrl: "/login",
    signupUrl: "/signup",
  },

  hero: {
    brand: "Gesttora",
    headline: "Conhecimento que passa de mandato a mandato",
    subtitle:
      "Plataforma multi-tenant para associações científicas preservarem memória institucional, onboarding de diretorias e fluxos acadêmicos.",
    primaryCta: { label: "Criar conta da associação", url: "/signup" },
    secondaryCta: { label: "Já tenho conta", url: "/login" },
    /** Atmosfera: reunião acadêmica / auditorium */
    backgroundImage:
      "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1920&q=80",
  },

  about: {
    title: "Feita para a transição de gestão",
    description:
      "Associações científicas perdem contexto a cada ciclo de diretoria: planilhas dispersas, decisões sem motivo registrado, onboarding lento. A Gesttora estrutura mandatos, memória e eventos no mesmo lugar — para a próxima gestão começar com o que a anterior deixou pronto.",
    points: [
      "Snapshot auditável do mandato (integridade do histórico)",
      "Onboarding adaptativo conforme o perfil da diretoria",
      "Eventos, membros e documentos no mesmo tenant",
    ],
  },

  features: {
    eyebrow: "Funcionalidades",
    title: "Benefícios para as Associações",
    description:
      "Menos tempo perdido em planilhas e e-mails — mais continuidade entre gestões, memória acessível e operação acadêmica no mesmo lugar.",
    items: [
      {
        icon: "RefreshCw" as const,
        title: "Mandatos e onboarding",
        description:
          "Ciclos de gestão, transição estruturada e wizard de onboarding que se adapta ao perfil técnico da nova diretoria.",
      },
      {
        icon: "BookOpen" as const,
        title: "Memória institucional",
        description:
          "Contexto histórico com decisão e motivo, timeline por mandato e consulta rápida ao que foi decidido — e por quê.",
      },
      {
        icon: "Calendar" as const,
        title: "Eventos e membros",
        description:
          "CFP, pareceres e anais ligados a membros e anuidades — fluxos acadêmicos no mesmo espaço operacional.",
      },
    ],
  },

  benefits: {
    title: "Para a diretoria que precisa continuar, não recomeçar",
    items: [
      {
        icon: "Clock" as const,
        title: "Onboarding mais rápido",
        description:
          "Nova gestão encontra o estado do mandato, documentos e histórico sem caçar pastas e e-mails.",
      },
      {
        icon: "Shield" as const,
        title: "Histórico auditável",
        description:
          "Snapshots e contextos com rastreabilidade — base para pesquisa e prestação de contas interna.",
      },
      {
        icon: "Users" as const,
        title: "Portal do associado",
        description:
          "Perfil, documentos pessoais e visão clara do que a associação oferece a cada filiado.",
      },
      {
        icon: "Building2" as const,
        title: "Multi-tenant por associação",
        description:
          "Cada associação no seu schema — isolamento de dados e operação independente.",
      },
    ],
  },

  contact: {
    eyebrow: "Contato",
    title: "Fale com a equipe Gesttora",
    email: "contato@gesttora.vertent.com.br",
    address: "São Paulo, Brasil",
    phone: "+55 (11) 0000-0000",
    formTitle: "Envie uma mensagem",
    successMessage:
      "Mensagem registrada (demo). Em produção, este formulário enviará para a equipe Gesttora.",
  },

  footer: {
    tagline: "Gestão contínua de conhecimento institucional para associações científicas.",
    productLinks: [
      { href: "#features", label: "Funcionalidades" },
      { href: "#benefits", label: "Benefícios" },
      { href: "/signup", label: "Criar conta" },
    ],
    legalLinks: [
      { href: "#", label: "Privacidade" },
      { href: "#", label: "Termos" },
    ],
    copyright: `© ${new Date().getFullYear()} Gesttora · gesttora.vertent.com.br`,
  },
} as const;

export type GesttoraLandingContent = typeof gesttoraLanding;
