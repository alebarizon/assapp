export type SituacaoConector = "ativo" | "configurado" | "disponivel" | "em_breve";

export interface Conector {
  slug: string;
  nome: string;
  categoria: string;
  categoria_label: string;
  descricao: string;
  situacao: SituacaoConector;
  acao: "pagamento" | "webhooks" | null;
}

export interface Opcao {
  slug: string;
  label: string;
}

export interface Catalogo {
  categorias: Opcao[];
  conectores: Conector[];
  eventos: Opcao[];
  pode_configurar_pagamento: boolean;
}

export interface WebhookSaida {
  id: string;
  url: string;
  descricao: string;
  eventos: string[];
  segredo: string;
  ativo: boolean;
  falhas_seguidas: number;
  ultima_entrega_em: string | null;
  created_at: string;
}

export type StatusEntrega = "pendente" | "entregue" | "desistiu";

export interface EntregaWebhook {
  id: string;
  evento: string;
  dados: Record<string, unknown>;
  status: StatusEntrega;
  tentativas: number;
  proxima_tentativa: string;
  resposta_status: number | null;
  ultimo_erro: string;
  created_at: string;
  entregue_em: string | null;
}

export const SITUACAO_CONECTOR: Record<SituacaoConector, { label: string; badge: string }> = {
  ativo: { label: "Ativo", badge: "ativo" },
  configurado: { label: "Configurado, desligado", badge: "pendente" },
  disponivel: { label: "Disponível", badge: "planejado" },
  em_breve: { label: "Em breve", badge: "arquivado" },
};

export const STATUS_ENTREGA: Record<StatusEntrega, { label: string; badge: string }> = {
  pendente: { label: "Tentando de novo", badge: "pendente" },
  entregue: { label: "Entregue", badge: "ativo" },
  desistiu: { label: "Falhou", badge: "rejeitado" },
};
