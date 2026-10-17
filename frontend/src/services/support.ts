import type { Chamado, ChamadoResumo, ResumoSuporte } from "@/types/support";
import { api } from "./api";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

export async function listChamados(params: { status?: string; categoria?: string; search?: string; tenant?: string } = {}) {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v));
  const { data } = await api.get<ChamadoResumo[]>("/api/suporte/", { params: clean });
  return data;
}

export async function getResumoSuporte(): Promise<ResumoSuporte> {
  const { data } = await api.get<ResumoSuporte>("/api/suporte/resumo/");
  return data;
}

export async function getChamado(id: string): Promise<Chamado> {
  const { data } = await api.get<Chamado>(`/api/suporte/${id}/`);
  return data;
}

export async function abrirChamado(payload: {
  assunto: string;
  categoria: string;
  mensagem: string;
  pagina?: string;
  anexos: File[];
}): Promise<Chamado> {
  const form = new FormData();
  form.append("assunto", payload.assunto);
  form.append("categoria", payload.categoria);
  form.append("mensagem", payload.mensagem);
  if (payload.pagina) form.append("pagina", payload.pagina);
  payload.anexos.forEach((f) => form.append("anexos", f));
  const { data } = await api.post<Chamado>("/api/suporte/", form, MULTIPART);
  return data;
}

export async function responderChamado(id: string, texto: string, anexos: File[], interna = false): Promise<Chamado> {
  const form = new FormData();
  form.append("texto", texto);
  if (interna) form.append("interna", "true");
  anexos.forEach((f) => form.append("anexos", f));
  const { data } = await api.post<Chamado>(`/api/suporte/${id}/responder/`, form, MULTIPART);
  return data;
}

export async function alterarStatusChamado(id: string, payload: { status?: string; prioridade?: string }): Promise<Chamado> {
  const { data } = await api.post<Chamado>(`/api/suporte/${id}/status/`, payload);
  return data;
}
