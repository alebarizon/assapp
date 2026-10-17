export type ContatoEtapa = "novo" | "em_atendimento" | "interessado" | "convertido" | "arquivado";
export type ContatoOrigem = "site_contato" | "site_associe_se" | "evento" | "indicacao" | "redes_sociais" | "manual";
export type ContatoAssunto = "filiacao" | "eventos" | "cursos" | "imprensa" | "parceria" | "outro";

export interface Etiqueta {
  id: number;
  nome: string;
  cor: string;
  contatos_count?: number;
}

export interface Contato {
  id: string;
  nome: string;
  email: string;
  telefone: string;
  instituicao: string;
  assunto: ContatoAssunto;
  mensagem: string;
  etapa: ContatoEtapa;
  origem: ContatoOrigem;
  etiquetas: Etiqueta[];
  etiqueta_ids?: number[];
  responsavel: string | null;
  responsavel_nome: string;
  membro: string | null;
  membro_nome: string | null;
  consentimento_lgpd: boolean;
  ultima_interacao_em: string | null;
  notas_count?: number;
  created_at: string;
  updated_at: string;
}

export interface NotaContato {
  id: string;
  tipo: "manual" | "sistema" | "mensagem";
  texto: string;
  autor_nome: string;
  created_at: string;
}

export type ResumoFunil = Record<ContatoEtapa, number>;

export interface ContatoPublicoPayload {
  nome: string;
  email: string;
  telefone?: string;
  instituicao?: string;
  assunto: ContatoAssunto;
  mensagem: string;
  consentimento_lgpd: boolean;
  origem?: "site_contato" | "site_associe_se";
  website?: string;
}

export const ETAPAS: { value: ContatoEtapa; label: string; badge: string }[] = [
  { value: "novo", label: "Novo", badge: "pendente" },
  { value: "em_atendimento", label: "Em atendimento", badge: "planejado" },
  { value: "interessado", label: "Interessado", badge: "interessado" },
  { value: "convertido", label: "Convertido", badge: "ativo" },
  { value: "arquivado", label: "Arquivado", badge: "arquivado" },
];

export const ETAPA_LABEL = Object.fromEntries(ETAPAS.map((e) => [e.value, e.label])) as Record<ContatoEtapa, string>;
export const ETAPA_BADGE = Object.fromEntries(ETAPAS.map((e) => [e.value, e.badge])) as Record<ContatoEtapa, string>;

export const ORIGEM_LABEL: Record<ContatoOrigem, string> = {
  site_contato: "Site — contato",
  site_associe_se: "Site — associe-se",
  evento: "Evento",
  indicacao: "Indicação",
  redes_sociais: "Redes sociais",
  manual: "Cadastro manual",
};

export const ASSUNTO_LABEL: Record<ContatoAssunto, string> = {
  filiacao: "Quero me associar",
  eventos: "Eventos",
  cursos: "Cursos",
  imprensa: "Imprensa",
  parceria: "Parcerias",
  outro: "Outro assunto",
};
