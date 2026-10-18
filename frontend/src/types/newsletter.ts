export type StatusCampanha = "rascunho" | "enviando" | "enviada" | "cancelada";
export type StatusEnvio = "pendente" | "enviado" | "falha" | "cancelado";
export type SituacaoPublico = "em_dia" | "pendente" | "inativo";
export type TipoFiliacao = "efetivo" | "estudante" | "honorario" | "institucional";

export interface PublicoCampanha {
  associados?: { situacoes: SituacaoPublico[]; tipos: TipoFiliacao[] };
  eventos?: string[];
  etiquetas?: number[];
}

export interface EstatisticasCampanha {
  total: number;
  pendente: number;
  enviado: number;
  falha: number;
  cancelado: number;
  descadastros: number;
}

export interface Campanha {
  id: string;
  assunto: string;
  corpo: string;
  link: string;
  link_label: string;
  publico: PublicoCampanha;
  status: StatusCampanha;
  enviada_em: string | null;
  concluida_em: string | null;
  created_by_nome: string | null;
  created_at: string;
  updated_at: string;
  estatisticas: EstatisticasCampanha | null;
}

export interface ResumoPublico {
  total: number;
  por_origem: { associados: number; eventos: number; contatos: number };
  descadastrados: number;
  amostra: { nome: string; email: string; origem: string }[];
}

export interface OpcoesPublico {
  eventos: { id: string; titulo: string; data_inicio: string }[];
  etiquetas: { id: number; nome: string; cor: string }[];
}

export interface EnvioCampanha {
  id: number;
  email: string;
  nome: string;
  status: StatusEnvio;
  tentativas: number;
  erro: string;
  enviado_em: string | null;
}

export interface Descadastro {
  id: number;
  email: string;
  campanha_assunto: string | null;
  created_at: string;
}

export const STATUS_CAMPANHA: Record<StatusCampanha, { label: string; badge: string }> = {
  rascunho: { label: "Rascunho", badge: "rascunho" },
  enviando: { label: "Enviando", badge: "pendente" },
  enviada: { label: "Enviada", badge: "ativa" },
  cancelada: { label: "Cancelada", badge: "rejeitado" },
};

export const STATUS_ENVIO: Record<StatusEnvio, string> = {
  pendente: "Na fila",
  enviado: "Enviado",
  falha: "Falhou",
  cancelado: "Cancelado",
};

export const SITUACAO_LABEL: Record<SituacaoPublico, string> = {
  em_dia: "Em dia",
  pendente: "Com anuidade em atraso",
  inativo: "Inativos / ex-associados",
};

export const TIPO_LABEL: Record<TipoFiliacao, string> = {
  efetivo: "Efetivo",
  estudante: "Estudante",
  honorario: "Honorário",
  institucional: "Institucional",
};

export function descreverPublico(p: PublicoCampanha, opcoes?: OpcoesPublico): string {
  const partes: string[] = [];
  if (p.associados) {
    const sit = p.associados.situacoes.length
      ? p.associados.situacoes.map((s) => SITUACAO_LABEL[s].toLowerCase()).join(", ")
      : "todas as situações";
    const tipos = p.associados.tipos.length ? ` (${p.associados.tipos.map((t) => TIPO_LABEL[t]).join(", ")})` : "";
    partes.push(`Associados: ${sit}${tipos}`);
  }
  if (p.eventos?.length) {
    const nomes = p.eventos.map((id) => opcoes?.eventos.find((e) => e.id === id)?.titulo ?? "evento");
    partes.push(`Inscritos em ${nomes.join(", ")}`);
  }
  if (p.etiquetas?.length) {
    const nomes = p.etiquetas.map((id) => opcoes?.etiquetas.find((e) => e.id === id)?.nome ?? "etiqueta");
    partes.push(`Contatos: ${nomes.join(", ")}`);
  }
  return partes.join(" · ") || "Nenhum público definido";
}
