import type {
  Campanha,
  Descadastro,
  EnvioCampanha,
  EnvioRegua,
  ListaReguas,
  OpcoesPublico,
  PreviaRegua,
  PublicoCampanha,
  Regua,
  ResumoPublico,
  TipoRegua,
} from "@/types/newsletter";
import { api } from "./api";

const C = "/api/newsletter/campanhas";

export async function listCampanhas(): Promise<Campanha[]> {
  return (await api.get<Campanha[]>(`${C}/`)).data;
}

export async function getCampanha(id: string): Promise<Campanha> {
  return (await api.get<Campanha>(`${C}/${id}/`)).data;
}

export async function salvarCampanha(id: string | null, payload: Partial<Campanha>): Promise<Campanha> {
  return id ? (await api.patch<Campanha>(`${C}/${id}/`, payload)).data : (await api.post<Campanha>(`${C}/`, payload)).data;
}

export async function deleteCampanha(id: string): Promise<void> {
  await api.delete(`${C}/${id}/`);
}

export async function previaPublico(publico: PublicoCampanha): Promise<ResumoPublico> {
  return (await api.post<ResumoPublico>(`${C}/publico/`, { publico })).data;
}

export async function getOpcoesPublico(): Promise<OpcoesPublico> {
  return (await api.get<OpcoesPublico>(`${C}/opcoes/`)).data;
}

export async function enviarCampanha(id: string): Promise<Campanha & { enfileirados: number }> {
  return (await api.post(`${C}/${id}/enviar/`)).data;
}

export async function enviarTeste(id: string, email: string): Promise<{ enviado_para: string }> {
  return (await api.post(`${C}/${id}/teste/`, { email })).data;
}

export async function cancelarCampanha(id: string): Promise<Campanha & { cancelados: number }> {
  return (await api.post(`${C}/${id}/cancelar/`)).data;
}

export async function duplicarCampanha(id: string): Promise<Campanha> {
  return (await api.post<Campanha>(`${C}/${id}/duplicar/`)).data;
}

export async function listEnvios(id: string, status?: string): Promise<EnvioCampanha[]> {
  return (await api.get<EnvioCampanha[]>(`${C}/${id}/envios/`, { params: status ? { status } : {} })).data;
}

export async function listDescadastros(): Promise<Descadastro[]> {
  return (await api.get<Descadastro[]>("/api/newsletter/descadastros/")).data;
}

export async function reinscrever(id: number): Promise<void> {
  await api.delete(`/api/newsletter/descadastros/${id}/`);
}

export interface SituacaoDescadastro {
  email: string;
  associacao: string;
  descadastrado: boolean;
}

export async function getDescadastro(schema: string, t: string): Promise<SituacaoDescadastro> {
  return (await api.get<SituacaoDescadastro>("/api/newsletter/public/descadastrar/", { params: { schema, t } })).data;
}

export async function confirmarDescadastro(schema: string, t: string): Promise<SituacaoDescadastro> {
  return (await api.post<SituacaoDescadastro>("/api/newsletter/public/descadastrar/", { t }, { params: { schema } })).data;
}

const R = "/api/newsletter/reguas";

export async function listReguas(): Promise<ListaReguas> {
  return (await api.get<ListaReguas>(`${R}/`)).data;
}

export async function salvarRegua(tipo: TipoRegua, payload: Partial<Regua>): Promise<Regua> {
  return (await api.patch<Regua>(`${R}/${tipo}/`, payload)).data;
}

export async function previaRegua(tipo: TipoRegua): Promise<PreviaRegua> {
  return (await api.get<PreviaRegua>(`${R}/${tipo}/previa/`)).data;
}

export async function testarRegua(tipo: TipoRegua, email?: string): Promise<{ enviado_para: string }> {
  return (await api.post(`${R}/${tipo}/teste/`, email ? { email } : {})).data;
}

export async function restaurarRegua(tipo: TipoRegua): Promise<Regua> {
  return (await api.post<Regua>(`${R}/${tipo}/restaurar/`)).data;
}

export async function listEnviosRegua(tipo?: TipoRegua): Promise<EnvioRegua[]> {
  return (await api.get<EnvioRegua[]>(`${R}/envios/`, { params: tipo ? { tipo } : {} })).data;
}
