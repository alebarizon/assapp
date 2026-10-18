export type MetodoPagamento = "pix" | "cartao" | "boleto";
export type StatusCobranca = "pendente" | "paga" | "cancelada" | "falhou";

export interface Cobranca {
  id: string;
  anuidade: string | null;
  pedido: string | null;
  descricao: string;
  valor: string;
  metodo: MetodoPagamento;
  metodo_display: string;
  provedor: "asaas" | "simulado";
  status: StatusCobranca;
  status_display: string;
  url_pagamento: string;
  pix_copia_cola: string;
  pix_qrcode_base64: string;
  vencimento: string;
  pago_em: string | null;
  created_at: string;
}

export interface DisponibilidadePagamento {
  habilitado: boolean;
  simulado: boolean;
  /** Ambiente de demonstração: permite o checkout "pagamento imediato" */
  demo: boolean;
  metodos: MetodoPagamento[];
}

export interface ConfiguracaoPagamento {
  provedor: "asaas";
  ativo: boolean;
  sandbox: boolean;
  tem_api_key: boolean;
  api_key_final: string;
  webhook_url: string;
  webhook_token: string;
  aceita_pix: boolean;
  aceita_cartao: boolean;
  aceita_boleto: boolean;
  updated_at: string;
}

export const METODO_LABEL: Record<MetodoPagamento, string> = {
  pix: "Pix",
  cartao: "Cartão de crédito",
  boleto: "Boleto",
};
