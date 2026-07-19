import type { ContextoHistorico, TimelineEvento, TipoContexto } from "@/types/memoria";
import { api } from "./api";

function unwrapList<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function listContextos(params?: {
  mandato?: string;
  tipo?: string;
  q?: string;
  incluir_arquivados?: boolean;
}): Promise<ContextoHistorico[]> {
  const { data } = await api.get("/api/memoria/contextos/", { params });
  return unwrapList(data);
}

export async function getContexto(id: string): Promise<ContextoHistorico> {
  const { data } = await api.get<ContextoHistorico>(`/api/memoria/contextos/${id}/`);
  return data;
}

export async function createContexto(payload: {
  mandato: string;
  tipo: TipoContexto;
  titulo: string;
  conteudo: string;
  decisao?: string;
  motivo?: string;
  tags?: string[];
}): Promise<ContextoHistorico> {
  const { data } = await api.post<ContextoHistorico>("/api/memoria/contextos/", payload);
  return data;
}

export async function arquivarContexto(id: string): Promise<ContextoHistorico> {
  const { data } = await api.post<ContextoHistorico>(
    `/api/memoria/contextos/${id}/arquivar/`,
    {}
  );
  return data;
}

export async function listTimeline(mandatoId?: string): Promise<TimelineEvento[]> {
  const { data } = await api.get("/api/memoria/timeline/", {
    params: mandatoId ? { mandato: mandatoId } : undefined,
  });
  return unwrapList(data);
}

export async function getTimelineMandatoAtivo(): Promise<TimelineEvento[]> {
  const { data } = await api.get<TimelineEvento[]>(
    "/api/memoria/timeline/por_mandato_ativo/"
  );
  return data;
}
