export type MetodoPagamento = "pix" | "cartao" | "boleto";
export type ProvedorPagamento = "asaas" | "pagbank" | "mercadopago";
export type StatusCobranca = "pendente" | "paga" | "cancelada" | "falhou";

export interface Cobranca {
  id: string;
  anuidade: string | null;
  pedido: string | null;
  descricao: string;
  valor: string;
  metodo: MetodoPagamento;
  metodo_display: string;
  provedor: ProvedorPagamento | "simulado";
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
  provedor: ProvedorPagamento;
  ativo: boolean;
  sandbox: boolean;
  tem_api_key: boolean;
  api_key_final: string;
  webhook_url: string;
  webhook_token: string;
  /** Site em HTTPS: PagBank e Mercado Pago avisam o pagamento na hora */
  notificacao_automatica: boolean;
  aceita_pix: boolean;
  aceita_cartao: boolean;
  aceita_boleto: boolean;
  updated_at: string;
}

export const PROVEDOR_INFO: Record<
  ProvedorPagamento,
  { nome: string; placeholder: string; ondeChave: string; sandbox: boolean }
> = {
  asaas: {
    nome: "Asaas",
    placeholder: "$aact_...",
    ondeChave: "No Asaas: Integrações → Chave de API.",
    sandbox: true,
  },
  pagbank: {
    nome: "PagBank",
    placeholder: "Token do PagBank",
    ondeChave:
      "No PagBank: Minha conta → Venda online → Integrações → Gerar token. O Pix exige uma chave Pix cadastrada na conta.",
    sandbox: true,
  },
  mercadopago: {
    nome: "Mercado Pago",
    placeholder: "APP_USR-...",
    ondeChave:
      "No Mercado Pago Developers: Suas integrações → aplicação → Credenciais → Access Token. Para testar, use as credenciais da aba Teste.",
    sandbox: false,
  },
};

export const METODO_LABEL: Record<MetodoPagamento, string> = {
  pix: "Pix",
  cartao: "Cartão de crédito",
  boleto: "Boleto",
};
