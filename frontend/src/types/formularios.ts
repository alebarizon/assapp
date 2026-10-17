export type FormularioStatus = "rascunho" | "publicado" | "encerrado";
export type RespostaStatus = "pendente" | "em_andamento" | "enviada";
export type PerguntaTipo =
  | "texto_curto"
  | "texto_longo"
  | "numero"
  | "email"
  | "data"
  | "escolha_unica"
  | "multipla_escolha"
  | "escala";

export type ValorResposta = string | string[];

export interface Pergunta {
  id?: string;
  texto: string;
  ajuda: string;
  tipo: PerguntaTipo;
  opcoes: string[];
  escala_min: number;
  escala_max: number;
  obrigatoria: boolean;
}

export interface Secao {
  id?: string;
  titulo: string;
  descricao: string;
  perguntas: Pergunta[];
}

export interface FormularioResumo {
  id: string;
  titulo: string;
  status: FormularioStatus;
  status_display: string;
  link_publico_ativo: boolean;
  disponivel_no_portal: boolean;
  evento: string | null;
  evento_titulo: string | null;
  encerra_em: string | null;
  respostas_enviadas: number;
  convites_pendentes: number;
  perguntas_count: number;
  aceitando_respostas: boolean;
  created_at: string;
}

export interface Formulario {
  id: string;
  titulo: string;
  descricao: string;
  status: FormularioStatus;
  status_display: string;
  link_publico_ativo: boolean;
  pedir_identificacao: boolean;
  disponivel_no_portal: boolean;
  public_token: string;
  evento: string | null;
  evento_titulo: string | null;
  encerra_em: string | null;
  mensagem_confirmacao: string;
  aceitando_respostas: boolean;
  tem_respostas: boolean;
  secoes: Secao[];
}

export interface RespostaItem {
  id: string;
  membro: string | null;
  nome: string;
  email: string;
  origem: "link_publico" | "portal" | "convite";
  origem_display: string;
  status: RespostaStatus;
  status_display: string;
  token: string;
  enviada_em: string | null;
  created_at: string;
  valores: Record<string, ValorResposta> | null;
}

export interface ResumoPergunta {
  id: string;
  texto: string;
  tipo: PerguntaTipo;
  secao: string;
  respondidas: number;
  opcoes?: { opcao: string; total: number }[];
  media?: number | null;
  textos?: string[];
}

export interface ResumoFormulario {
  total_respostas: number;
  perguntas: ResumoPergunta[];
}

export type PerguntaPublica = Omit<Pergunta, "id"> & { id: string };

export interface SecaoPublica {
  id: string;
  titulo: string;
  descricao: string;
  perguntas: PerguntaPublica[];
}

/** Formulário como visto por quem responde (público, convite ou portal). */
export interface FormularioParaResponder {
  id: string;
  titulo: string;
  descricao: string;
  aceitando_respostas: boolean;
  pedir_identificacao: boolean;
  mensagem_confirmacao: string;
  evento_titulo: string | null;
  secoes: SecaoPublica[];
  associacao?: string;
  nome?: string;
  situacao?: RespostaStatus;
  valores?: Record<string, ValorResposta>;
}

export interface MeuFormulario {
  id: string;
  titulo: string;
  descricao: string;
  encerra_em: string | null;
  aceitando_respostas: boolean;
  minha_situacao: RespostaStatus;
  enviada_em: string | null;
}

export const PERGUNTA_TIPOS: { value: PerguntaTipo; label: string }[] = [
  { value: "texto_curto", label: "Texto curto" },
  { value: "texto_longo", label: "Texto longo" },
  { value: "escolha_unica", label: "Escolha única" },
  { value: "multipla_escolha", label: "Múltipla escolha" },
  { value: "escala", label: "Escala (nota)" },
  { value: "numero", label: "Número" },
  { value: "email", label: "E-mail" },
  { value: "data", label: "Data" },
];

export const FORMULARIO_STATUS_BADGE: Record<FormularioStatus, string> = {
  rascunho: "rascunho",
  publicado: "ativo",
  encerrado: "arquivado",
};

export const RESPOSTA_STATUS_BADGE: Record<RespostaStatus, string> = {
  pendente: "rascunho",
  em_andamento: "pendente",
  enviada: "ativo",
};

export const novaPergunta = (): Pergunta => ({
  texto: "",
  ajuda: "",
  tipo: "texto_curto",
  opcoes: [],
  escala_min: 1,
  escala_max: 5,
  obrigatoria: false,
});
