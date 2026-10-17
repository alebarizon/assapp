import type {
  Formulario,
  FormularioParaResponder,
  FormularioResumo,
  MeuFormulario,
  RespostaItem,
  RespostaStatus,
  ResumoFormulario,
  ValorResposta,
} from "@/types/formularios";
import { api } from "./api";

type Answers = Record<string, ValorResposta>;
type Envio = { situacao: RespostaStatus; mensagem_confirmacao: string };

// ---------------------------------------------------------------- Diretoria

export async function listFormularios(params?: { status?: string; search?: string; evento?: string }): Promise<FormularioResumo[]> {
  const { data } = await api.get<FormularioResumo[]>("/api/formularios/", { params });
  return data;
}

export async function getFormulario(id: string): Promise<Formulario> {
  const { data } = await api.get<Formulario>(`/api/formularios/${id}/`);
  return data;
}

export async function createFormulario(payload: Partial<Formulario>): Promise<Formulario> {
  const { data } = await api.post<Formulario>("/api/formularios/", payload);
  return data;
}

export async function updateFormulario(id: string, payload: Partial<Formulario>): Promise<Formulario> {
  const { data } = await api.patch<Formulario>(`/api/formularios/${id}/`, payload);
  return data;
}

export async function deleteFormulario(id: string): Promise<void> {
  await api.delete(`/api/formularios/${id}/`);
}

export async function duplicarFormulario(id: string): Promise<Formulario> {
  const { data } = await api.post<Formulario>(`/api/formularios/${id}/duplicar/`, {});
  return data;
}

export async function listConvites(id: string): Promise<RespostaItem[]> {
  const { data } = await api.get<RespostaItem[]>(`/api/formularios/${id}/convites/`);
  return data;
}

export async function convidar(
  id: string,
  payload: { membros?: string[]; todos_ativos?: boolean; reenviar_pendentes?: boolean }
): Promise<{ criados: number; existentes: number; emails_enviados: number }> {
  const { data } = await api.post(`/api/formularios/${id}/convites/`, payload);
  return data;
}

export async function listRespostas(id: string): Promise<RespostaItem[]> {
  const { data } = await api.get<RespostaItem[]>(`/api/formularios/${id}/respostas/`);
  return data;
}

export async function excluirResposta(id: string, respostaId: string): Promise<void> {
  await api.delete(`/api/formularios/${id}/respostas/${respostaId}/`);
}

export async function getResumo(id: string): Promise<ResumoFormulario> {
  const { data } = await api.get<ResumoFormulario>(`/api/formularios/${id}/resumo/`);
  return data;
}

export async function exportarCsv(id: string, titulo: string): Promise<void> {
  const response = await api.get(`/api/formularios/${id}/exportar/`, { responseType: "blob" });
  const href = URL.createObjectURL(response.data as Blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `respostas-${titulo.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.csv`;
  link.click();
  URL.revokeObjectURL(href);
}

// ---------------------------------------------------------------- Portal do associado

export async function listMeusFormularios(): Promise<MeuFormulario[]> {
  const { data } = await api.get<MeuFormulario[]>("/api/formularios/my/");
  return data;
}

export async function getMeuFormulario(id: string): Promise<FormularioParaResponder> {
  const { data } = await api.get<FormularioParaResponder>(`/api/formularios/my/${id}/`);
  return data;
}

export async function salvarMeuFormulario(id: string, answers: Answers, enviar: boolean): Promise<Envio> {
  const { data } = await api.post<Envio>(`/api/formularios/my/${id}/${enviar ? "enviar" : "salvar"}/`, { answers });
  return data;
}

// ---------------------------------------------------------------- Público

export async function getFormularioPublico(schema: string, token: string): Promise<FormularioParaResponder> {
  const { data } = await api.get<FormularioParaResponder>(`/api/formularios/public/f/${token}/`, { params: { schema } });
  return data;
}

export async function enviarFormularioPublico(
  schema: string,
  token: string,
  payload: { nome: string; email: string; answers: Answers }
): Promise<Envio> {
  const { data } = await api.post<Envio>(`/api/formularios/public/f/${token}/`, payload, { params: { schema } });
  return data;
}

export async function getConvite(schema: string, token: string): Promise<FormularioParaResponder> {
  const { data } = await api.get<FormularioParaResponder>(`/api/formularios/public/r/${token}/`, { params: { schema } });
  return data;
}

export async function responderConvite(schema: string, token: string, answers: Answers, enviar: boolean): Promise<Envio> {
  const { data } = await api.post<Envio>(`/api/formularios/public/r/${token}/`, { answers, enviar }, { params: { schema } });
  return data;
}
