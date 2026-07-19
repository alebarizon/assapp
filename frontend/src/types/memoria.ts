export type TipoContexto =
  | "decisao"
  | "processo"
  | "evento"
  | "financeiro"
  | "comunicacao"
  | "filiacao"
  | "evento_academico"
  | "outro";

export interface ContextoHistorico {
  id: string;
  mandato: string;
  mandato_titulo?: string;
  autor?: string;
  autor_email?: string;
  autor_nome?: string;
  tipo: TipoContexto;
  tipo_display: string;
  titulo: string;
  conteudo: string;
  decisao?: string;
  motivo?: string;
  entidade_tipo?: string;
  entidade_id?: string;
  tags: string[];
  visivel_diretoria: boolean;
  arquivado: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvento {
  id: string;
  mandato: string;
  mandato_titulo?: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  data_evento: string;
  metadata?: Record<string, unknown>;
  contexto_id?: string;
}

export const TIPOS_CONTEXTO: { value: TipoContexto; label: string }[] = [
  { value: "decisao", label: "Decisão" },
  { value: "processo", label: "Processo" },
  { value: "evento", label: "Evento" },
  { value: "financeiro", label: "Financeiro" },
  { value: "comunicacao", label: "Comunicação" },
  { value: "filiacao", label: "Filiação" },
  { value: "evento_academico", label: "Evento Acadêmico" },
  { value: "outro", label: "Outro" },
];
