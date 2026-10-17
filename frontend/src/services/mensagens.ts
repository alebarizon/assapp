import type { Conversa, ConversaResumo } from "@/types/mensagens";
import { api } from "./api";

// ---------------------------------------------------------------- Diretoria

export async function listConversas(params: { status?: string; search?: string; nao_lidas?: boolean } = {}) {
  const clean: Record<string, string> = {};
  if (params.status) clean.status = params.status;
  if (params.search) clean.search = params.search;
  if (params.nao_lidas) clean.nao_lidas = "true";
  const { data } = await api.get<ConversaResumo[]>("/api/mensagens/", { params: clean });
  return data;
}

export async function iniciarConversas(payload: {
  membros?: string[];
  todos_ativos?: boolean;
  assunto: string;
  texto: string;
  notificar: boolean;
}): Promise<{ criadas: number; id?: string }> {
  const { data } = await api.post("/api/mensagens/", payload);
  return data;
}

export async function getConversa(id: string): Promise<Conversa> {
  const { data } = await api.get<Conversa>(`/api/mensagens/${id}/`);
  return data;
}

export async function responderConversa(id: string, texto: string): Promise<Conversa> {
  const { data } = await api.post<Conversa>(`/api/mensagens/${id}/responder/`, { texto });
  return data;
}

export async function arquivarConversa(id: string, arquivar: boolean): Promise<void> {
  await api.post(`/api/mensagens/${id}/arquivar/`, { arquivar });
}

// ---------------------------------------------------------------- Portal do associado

export async function listMinhasConversas(): Promise<ConversaResumo[]> {
  const { data } = await api.get<ConversaResumo[]>("/api/mensagens/my/");
  return data;
}

export async function iniciarMinhaConversa(assunto: string, texto: string): Promise<Conversa> {
  const { data } = await api.post<Conversa>("/api/mensagens/my/", { assunto, texto });
  return data;
}

export async function getMinhaConversa(id: string): Promise<Conversa> {
  const { data } = await api.get<Conversa>(`/api/mensagens/my/${id}/`);
  return data;
}

export async function responderMinhaConversa(id: string, texto: string): Promise<Conversa> {
  const { data } = await api.post<Conversa>(`/api/mensagens/my/${id}/responder/`, { texto });
  return data;
}
