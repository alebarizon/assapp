import type { Contato, ContatoPublicoPayload, Etiqueta, FichaContato, NotaContato, ResumoFunil } from "@/types/contatos";
import { api } from "./api";

export interface ContatoFiltros {
  etapa?: string;
  abertos?: boolean;
  origem?: string;
  assunto?: string;
  etiqueta?: number | string;
  search?: string;
}

export async function listContatos(filtros: ContatoFiltros = {}): Promise<Contato[]> {
  const params: Record<string, string> = {};
  Object.entries(filtros).forEach(([k, v]) => {
    if (v !== undefined && v !== "" && v !== false) params[k] = String(v);
  });
  const { data } = await api.get<Contato[]>("/api/contatos/", { params });
  return data;
}

export async function getResumoFunil(): Promise<ResumoFunil> {
  const { data } = await api.get<ResumoFunil>("/api/contatos/resumo/");
  return data;
}

export async function getContato(id: string): Promise<Contato> {
  const { data } = await api.get<Contato>(`/api/contatos/${id}/`);
  return data;
}

export async function getFichaContato(id: string): Promise<FichaContato> {
  const { data } = await api.get<FichaContato>(`/api/contatos/${id}/ficha/`);
  return data;
}

export async function createContato(payload: Partial<Contato>): Promise<Contato> {
  const { data } = await api.post<Contato>("/api/contatos/", payload);
  return data;
}

export async function updateContato(id: string, payload: Partial<Contato>): Promise<Contato> {
  const { data } = await api.patch<Contato>(`/api/contatos/${id}/`, payload);
  return data;
}

export async function deleteContato(id: string): Promise<void> {
  await api.delete(`/api/contatos/${id}/`);
}

export async function listNotas(id: string): Promise<NotaContato[]> {
  const { data } = await api.get<NotaContato[]>(`/api/contatos/${id}/notas/`);
  return data;
}

export async function addNota(id: string, texto: string): Promise<NotaContato> {
  const { data } = await api.post<NotaContato>(`/api/contatos/${id}/notas/`, { texto });
  return data;
}

export async function converterContato(
  id: string,
  tipoFiliacao?: string
): Promise<{ membro_id: string; membro_criado: boolean; contato: Contato }> {
  const { data } = await api.post(`/api/contatos/${id}/converter/`, { tipo_filiacao: tipoFiliacao || null });
  return data;
}

export async function listEtiquetas(): Promise<Etiqueta[]> {
  const { data } = await api.get<Etiqueta[]>("/api/contatos/etiquetas/");
  return data;
}

export async function createEtiqueta(payload: { nome: string; cor?: string }): Promise<Etiqueta> {
  const { data } = await api.post<Etiqueta>("/api/contatos/etiquetas/", payload);
  return data;
}

export async function deleteEtiqueta(id: number): Promise<void> {
  await api.delete(`/api/contatos/etiquetas/${id}/`);
}

export async function enviarContatoPublico(schema: string, payload: ContatoPublicoPayload): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>("/api/contatos/public/", payload, { params: { schema } });
  return data;
}
