import type {
  Assembleia,
  MinhaAssembleia,
  MinhaVotacao,
  Participacao,
  Presenca,
  Quorum,
  Votacao,
} from "@/types/governanca";
import { downloadBlob } from "@/utils/download";
import { api } from "./api";

const A = "/api/governanca/assembleias";
const V = "/api/governanca/votacoes";

export async function listAssembleias(): Promise<Assembleia[]> {
  return (await api.get<Assembleia[]>(`${A}/`)).data;
}

export async function getAssembleia(id: string): Promise<Assembleia> {
  return (await api.get<Assembleia>(`${A}/${id}/`)).data;
}

export async function salvarAssembleia(id: string | null, payload: Partial<Assembleia>): Promise<Assembleia> {
  return id ? (await api.patch<Assembleia>(`${A}/${id}/`, payload)).data : (await api.post<Assembleia>(`${A}/`, payload)).data;
}

export async function deleteAssembleia(id: string): Promise<void> {
  await api.delete(`${A}/${id}/`);
}

export type AcaoAssembleia = "convocar" | "iniciar" | "encerrar" | "cancelar" | "gerar-ata" | "publicar-ata";

export async function acaoAssembleia(
  id: string,
  acao: AcaoAssembleia,
  payload?: Record<string, unknown>,
): Promise<Assembleia & { emails_enviados?: number }> {
  return (await api.post(`${A}/${id}/${acao}/`, payload ?? {})).data;
}

export interface ListaPresenca {
  presencas: Presenca[];
  quorum: Quorum;
}

export async function getPresencas(id: string): Promise<ListaPresenca> {
  return (await api.get<ListaPresenca>(`${A}/${id}/presencas/`)).data;
}

export async function addPresenca(id: string, membro: string, forma: string): Promise<ListaPresenca> {
  return (await api.post<ListaPresenca>(`${A}/${id}/presencas/`, { membro, forma })).data;
}

export async function removePresenca(id: string, membro: string): Promise<ListaPresenca> {
  return (await api.delete<ListaPresenca>(`${A}/${id}/presencas/`, { params: { membro } })).data;
}

export function baixarAta(id: string) {
  return downloadBlob(`${A}/${id}/ata-pdf/`, "");
}

export async function listVotacoes(params?: { assembleia?: string }): Promise<Votacao[]> {
  return (await api.get<Votacao[]>(`${V}/`, { params })).data;
}

export async function getVotacao(id: string): Promise<Votacao> {
  return (await api.get<Votacao>(`${V}/${id}/`)).data;
}

export async function salvarVotacao(id: string | null, payload: Partial<Votacao>): Promise<Votacao> {
  return id ? (await api.patch<Votacao>(`${V}/${id}/`, payload)).data : (await api.post<Votacao>(`${V}/`, payload)).data;
}

export async function deleteVotacao(id: string): Promise<void> {
  await api.delete(`${V}/${id}/`);
}

export async function acaoVotacao(id: string, acao: "abrir" | "encerrar" | "cancelar"): Promise<Votacao & { eleitores?: number }> {
  return (await api.post(`${V}/${id}/${acao}/`)).data;
}

export async function getParticipacao(id: string): Promise<Participacao> {
  return (await api.get<Participacao>(`${V}/${id}/participacao/`)).data;
}

export async function getMinhaGovernanca(): Promise<{ assembleias: MinhaAssembleia[]; votacoes: MinhaVotacao[] }> {
  return (await api.get("/api/governanca/minhas/")).data;
}

export async function votar(id: string, opcoes: number[]): Promise<{ comprovante: string }> {
  return (await api.post(`/api/governanca/minhas/votacoes/${id}/votar/`, { opcoes })).data;
}

export async function marcarPresenca(id: string): Promise<void> {
  await api.post(`/api/governanca/minhas/assembleias/${id}/presenca/`);
}

export function baixarMinhaAta(id: string) {
  return downloadBlob(`/api/governanca/minhas/assembleias/${id}/ata-pdf/`, "");
}
