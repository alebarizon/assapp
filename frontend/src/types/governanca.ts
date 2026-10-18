export type AssembleiaStatus = "rascunho" | "convocada" | "em_andamento" | "encerrada" | "cancelada";
export type VotacaoStatus = "rascunho" | "aberta" | "encerrada" | "cancelada";
export type TipoAssembleia = "ordinaria" | "extraordinaria";
export type Modalidade = "presencial" | "online" | "hibrida";
export type TipoVotacao = "eleicao" | "deliberacao";
export type CensoVotacao = "adimplentes" | "ativos";

export interface Assembleia {
  id: string;
  titulo: string;
  tipo: TipoAssembleia;
  tipo_display: string;
  data_hora: string;
  modalidade: Modalidade;
  modalidade_display: string;
  local: string;
  link_online: string;
  convocacao: string;
  pauta: string[];
  quorum_minimo: number | null;
  status: AssembleiaStatus;
  status_display: string;
  mandato: string | null;
  convocada_em: string | null;
  encerrada_em: string | null;
  ata: string;
  ata_publicada_em: string | null;
  ata_hash: string;
  presentes: number;
  votacoes: { id: string; titulo: string; status: VotacaoStatus; status_display: string }[];
  created_at: string;
}

export interface Integrante {
  nome: string;
  cargo?: string;
}

export interface OpcaoVotacao {
  id?: number;
  titulo: string;
  descricao?: string;
  integrantes?: Integrante[];
  ordem?: number;
}

export interface ResultadoVotacao {
  eleitores: number;
  votantes: number;
  participacao_pct: number;
  cedulas: number;
  brancos: number;
  opcoes: { id: number; titulo: string; votos: number; pct_validos: number }[];
  vencedora: number | null;
  empate: boolean;
}

export interface Votacao {
  id: string;
  assembleia: string | null;
  assembleia_titulo: string | null;
  mandato: string | null;
  titulo: string;
  descricao: string;
  tipo: TipoVotacao;
  tipo_display: string;
  status: VotacaoStatus;
  status_display: string;
  censo: CensoVotacao;
  censo_display: string;
  secreta: boolean;
  max_escolhas: number;
  permite_branco: boolean;
  fecha_em: string | null;
  aberta_em: string | null;
  encerrada_em: string | null;
  resultado: ResultadoVotacao | null;
  opcoes: OpcaoVotacao[];
  created_at: string;
}

export interface Quorum {
  aptos: number;
  presentes: number;
  presentes_aptos: number;
  pct: number;
  minimo: number | null;
  atingido: boolean | null;
}

export interface Presenca {
  id: number;
  membro: string;
  membro_nome: string;
  forma: "presencial" | "online";
  forma_display: string;
  registrada_em: string;
}

export interface Participacao {
  eleitores: number;
  votantes: number;
  participacao_pct: number;
  eleitores_lista: { membro: string; nome: string; votou: boolean }[];
}

export interface MinhaAssembleia extends Assembleia {
  presente: boolean;
  pode_marcar_presenca: boolean;
}

export interface MinhaVotacao extends Votacao {
  ja_votou: boolean;
  pode_votar: boolean;
}

export const BADGE_STATUS: Record<AssembleiaStatus | VotacaoStatus, string> = {
  rascunho: "rascunho",
  convocada: "pendente",
  em_andamento: "ativa",
  aberta: "ativa",
  encerrada: "encerrado",
  cancelada: "rejeitado",
};

export function dataHora(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}
