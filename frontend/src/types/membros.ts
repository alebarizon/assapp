export type FiliacaoStatus = "ativa" | "inadimplente" | "suspensa" | "cancelada" | "honoraria";
export type AnuidadeStatus = "pendente" | "paga" | "vencida" | "isenta" | "cancelada";
export type TipoFiliacao = "efetivo" | "estudante" | "honorario" | "institucional";

export interface Anuidade {
  id: string;
  filiacao: string;
  membro_nome?: string;
  ano_referencia: number;
  valor: string;
  vencimento: string;
  status: AnuidadeStatus;
  status_display: string;
  pago_em?: string;
  nf_numero?: string;
  ultimo_lembrete?: { etapa: string; enviado_em: string } | null;
}

export type CategoriaTimeline =
  | "filiacao"
  | "anuidade"
  | "lembrete"
  | "pagamento"
  | "pedido"
  | "evento"
  | "curso"
  | "mensagem"
  | "formulario"
  | "contato";

export interface TimelineItem {
  quando: string;
  categoria: CategoriaTimeline;
  titulo: string;
  detalhe: string;
  link: string;
}

export interface Filiacao {
  id: string;
  membro: string;
  membro_nome?: string;
  mandato?: string;
  tipo: TipoFiliacao;
  tipo_display: string;
  status: FiliacaoStatus;
  status_display: string;
  data_inicio: string;
  data_fim?: string;
  observacoes?: string;
  anuidades?: Anuidade[];
}

export interface Membro {
  id: string;
  nome_completo: string;
  email: string;
  cpf?: string;
  cnpj?: string;
  telefone?: string;
  instituicao?: string;
  area_atuacao?: string;
  lattes_url?: string;
  orcid?: string;
  ativo: boolean;
  consentimento_lgpd: boolean;
  consentimento_em?: string;
  filiacao_status?: string;
  filiacao_tipo?: string;
  filiacoes?: Filiacao[];
  user?: string | null;
  user_email?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ResumoMembros {
  total_membros: number;
  filiacoes_ativas: number;
  filiacoes_inadimplentes: number;
  anuidades_pendentes: number;
  anuidades_vencidas: number;
}

export const TIPOS_FILIACAO: { value: TipoFiliacao; label: string }[] = [
  { value: "efetivo", label: "Efetivo" },
  { value: "estudante", label: "Estudante" },
  { value: "honorario", label: "Honorário" },
  { value: "institucional", label: "Institucional" },
];

export const STATUS_FILIACAO: Record<FiliacaoStatus, string> = {
  ativa: "Ativa",
  inadimplente: "Inadimplente",
  suspensa: "Suspensa",
  cancelada: "Cancelada",
  honoraria: "Honorária",
};

export type SituacaoCarteirinha = "em_dia" | "pendente" | "inativo";

interface SituacaoAssociado {
  situacao: SituacaoCarteirinha;
  situacao_display: string;
  valida_ate: string | null;
  honoraria: boolean;
  tipo: string;
  membro_desde: string | null;
}

export interface Carteirinha extends SituacaoAssociado {
  nome: string;
  matricula: string;
  instituicao: string;
  associacao: string;
  codigo: string;
  url_verificacao: string;
  qr: string;
}

export interface VerificacaoCarteirinha extends SituacaoAssociado {
  nome: string;
  matricula: string;
  associacao: string;
  verificado_em: string;
}
