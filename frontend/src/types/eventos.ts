export type EventoStatus =
  | "rascunho"
  | "inscricoes_abertas"
  | "cfp_aberto"
  | "em_avaliacao"
  | "encerrado"
  | "anais_publicados"
  | "cancelado";

export type SubmissaoStatus =
  | "rascunho"
  | "submetido"
  | "em_parecer"
  | "aceito"
  | "aceito_com_revisoes"
  | "rejeitado"
  | "retirado";

export interface CallForPapers {
  id: string;
  evento: string;
  titulo: string;
  instrucoes: string;
  data_abertura: string;
  data_fechamento: string;
  areas_tematicas: string[];
  max_submissoes_por_autor: number;
  anonimo: boolean;
  submissoes_count?: number;
}

export interface Parecer {
  id: string;
  submissao: string;
  parecerista: string;
  parecerista_email?: string;
  recomendacao?: string;
  recomendacao_display?: string;
  nota?: number;
  comentarios_autor?: string;
  concluido: boolean;
  concluido_em?: string;
}

export interface SubmissaoTrabalho {
  id: string;
  cfp: string;
  autor: string;
  autor_email?: string;
  membro?: string;
  membro_nome?: string;
  titulo: string;
  resumo: string;
  palavras_chave: string[];
  area_tematica?: string;
  status: SubmissaoStatus;
  status_display: string;
  submetido_em?: string;
  pareceres?: Parecer[];
  created_at: string;
}

export interface AnaisPublicacao {
  id: string;
  evento: string;
  titulo: string;
  issn?: string;
  url_publicacao?: string;
  publicado_em?: string;
  metadata?: {
    total_trabalhos: number;
    trabalhos: Array<{ id: string; titulo: string; autor: string }>;
  };
}

export interface EventoAcademico {
  id: string;
  titulo: string;
  slug: string;
  descricao?: string;
  data_inicio: string;
  data_fim: string;
  local?: string;
  modalidade: string;
  status: EventoStatus;
  status_display: string;
  valor_inscricao?: string;
  capacidade_max?: number;
  mandato?: string;
  mandato_titulo?: string;
  tem_cfp?: boolean;
  submissoes_count?: number;
  inscricoes_count?: number;
  call_for_papers?: CallForPapers;
  anais?: AnaisPublicacao;
  created_at: string;
}

export interface ResumoEventos {
  total: number;
  cfp_abertos: number;
  em_avaliacao: number;
  submissoes_pendentes: number;
  pareceres_pendentes: number;
}

export const STATUS_EVENTO: Record<EventoStatus, string> = {
  rascunho: "Rascunho",
  inscricoes_abertas: "Inscrições Abertas",
  cfp_aberto: "CFP Aberto",
  em_avaliacao: "Em Avaliação",
  encerrado: "Encerrado",
  anais_publicados: "Anais Publicados",
  cancelado: "Cancelado",
};
