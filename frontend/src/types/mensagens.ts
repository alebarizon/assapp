export interface MensagemConversa {
  id: string;
  autor_nome: string;
  da_diretoria: boolean;
  texto: string;
  created_at: string;
}

export interface ConversaResumo {
  id: string;
  assunto: string;
  membro: string;
  membro_nome: string;
  membro_email: string;
  status: "aberta" | "arquivada";
  iniciada_pela_diretoria: boolean;
  nao_lida: boolean;
  previa: string;
  ultima_mensagem_em: string | null;
  created_at: string;
}

export interface Conversa extends ConversaResumo {
  mensagens: MensagemConversa[];
}
