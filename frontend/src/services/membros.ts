import type { Anuidade, Membro, ResumoMembros, TipoFiliacao } from "@/types/membros";
import { api } from "./api";

function unwrapList<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getResumoMembros(): Promise<ResumoMembros> {
  const { data } = await api.get<ResumoMembros>("/api/membros/membros/resumo/");
  return data;
}

export async function listMembros(params?: {
  q?: string;
  status_filiacao?: string;
  ativo?: boolean;
}): Promise<Membro[]> {
  const { data } = await api.get("/api/membros/membros/", { params });
  return unwrapList(data);
}

export async function getMembro(id: string): Promise<Membro> {
  const { data } = await api.get<Membro>(`/api/membros/membros/${id}/`);
  return data;
}

export async function createMembro(payload: {
  nome_completo: string;
  email: string;
  cpf?: string;
  instituicao?: string;
  area_atuacao?: string;
  consentimento_lgpd: boolean;
  tipo_filiacao?: TipoFiliacao;
}): Promise<Membro> {
  const { data } = await api.post<Membro>("/api/membros/membros/", payload);
  return data;
}

export async function listAnuidades(params?: {
  status?: string;
  ano?: number;
}): Promise<Anuidade[]> {
  const { data } = await api.get("/api/membros/anuidades/", { params });
  return unwrapList(data);
}

export async function gerarAnuidadesLote(ano: number, valor?: number): Promise<{
  ano: number;
  criadas: number;
  ignoradas: number;
}> {
  const { data } = await api.post("/api/membros/anuidades/gerar_lote/", {
    ano,
    ...(valor !== undefined ? { valor } : {}),
  });
  return data;
}

export async function atualizarAnuidadesVencidas(): Promise<{
  anuidades_vencidas: number;
  filiacoes_inadimplentes: number;
}> {
  const { data } = await api.post("/api/membros/anuidades/atualizar_vencidas/", {});
  return data;
}

export async function registrarPagamentoAnuidade(
  id: string,
  nfNumero?: string
): Promise<Anuidade> {
  const { data } = await api.post<Anuidade>(
    `/api/membros/anuidades/${id}/registrar_pagamento/`,
    { nf_numero: nfNumero }
  );
  return data;
}

export async function getMeuMembro(): Promise<Membro> {
  const { data } = await api.get<Membro>("/api/membros/meu/");
  return data;
}

export async function listMinhasAnuidades(): Promise<Anuidade[]> {
  const { data } = await api.get<Anuidade[]>("/api/membros/meu/anuidades/");
  return Array.isArray(data) ? data : [];
}

export async function vincularUserMembro(
  membroId: string,
  payload: { user_id?: string; email?: string }
): Promise<Membro> {
  const { data } = await api.post<Membro>(
    `/api/membros/membros/${membroId}/vincular_user/`,
    payload
  );
  return data;
}

export async function desvincularUserMembro(membroId: string): Promise<Membro> {
  const { data } = await api.post<Membro>(
    `/api/membros/membros/${membroId}/desvincular_user/`,
    {}
  );
  return data;
}
