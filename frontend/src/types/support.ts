export type ChamadoStatus = "aberto" | "em_andamento" | "aguardando_associacao" | "resolvido" | "fechado";
export type ChamadoCategoria = "duvida" | "problema" | "financeiro" | "sugestao" | "cancelamento";
export type ChamadoPrioridade = "baixa" | "normal" | "alta" | "urgente";

export interface AnexoChamado {
  id: number;
  nome: string;
  tamanho: number;
  url: string;
}

export interface MensagemChamado {
  id: number;
  autor_nome: string;
  da_equipe: boolean;
  interna: boolean;
  texto: string;
  anexos: AnexoChamado[];
  created_at: string;
}

export interface ChamadoResumo {
  id: number;
  assunto: string;
  associacao: string;
  categoria: ChamadoCategoria;
  categoria_display: string;
  prioridade: ChamadoPrioridade;
  prioridade_display: string;
  status: ChamadoStatus;
  status_display: string;
  autor_nome: string;
  autor_email: string;
  nao_lido: boolean;
  ultima_mensagem_em: string | null;
  created_at: string;
}

export interface Chamado extends ChamadoResumo {
  pagina: string;
  mensagens: MensagemChamado[];
}

export interface ResumoSuporte {
  por_status: Record<ChamadoStatus, number>;
  nao_lidos: number;
}

export const CATEGORIAS: { value: ChamadoCategoria; label: string }[] = [
  { value: "duvida", label: "Dúvida de uso" },
  { value: "problema", label: "Problema técnico" },
  { value: "financeiro", label: "Assinatura e pagamento" },
  { value: "sugestao", label: "Sugestão" },
  { value: "cancelamento", label: "Cancelamento" },
];

export const STATUS_CHAMADO: { value: ChamadoStatus; label: string; badge: string }[] = [
  { value: "aberto", label: "Aberto", badge: "pendente" },
  { value: "em_andamento", label: "Em andamento", badge: "planejado" },
  { value: "aguardando_associacao", label: "Aguardando a associação", badge: "interessado" },
  { value: "resolvido", label: "Resolvido", badge: "ativo" },
  { value: "fechado", label: "Fechado", badge: "arquivado" },
];

export const STATUS_BADGE = Object.fromEntries(STATUS_CHAMADO.map((s) => [s.value, s.badge])) as Record<ChamadoStatus, string>;

export const PRIORIDADES: { value: ChamadoPrioridade; label: string }[] = [
  { value: "baixa", label: "Baixa" },
  { value: "normal", label: "Normal" },
  { value: "alta", label: "Alta" },
  { value: "urgente", label: "Urgente" },
];
