import type { MinhaPublicacao, Publicacao, PublicacaoBase } from "@/types/publicacoes";
import { downloadBlob } from "@/utils/download";
import { api } from "./api";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

export async function listPublicacoes(): Promise<Publicacao[]> {
  const { data } = await api.get<Publicacao[]>("/api/publicacoes/");
  return data;
}

export async function salvarPublicacao(id: string | null, form: FormData): Promise<Publicacao> {
  const { data } = id
    ? await api.patch<Publicacao>(`/api/publicacoes/${id}/`, form, MULTIPART)
    : await api.post<Publicacao>("/api/publicacoes/", form, MULTIPART);
  return data;
}

export async function deletePublicacao(id: string): Promise<void> {
  await api.delete(`/api/publicacoes/${id}/`);
}

export function baixarArquivoPublicacao(id: string) {
  return downloadBlob(`/api/publicacoes/${id}/arquivo/`, "");
}

export async function listMinhasPublicacoes(): Promise<MinhaPublicacao[]> {
  const { data } = await api.get<MinhaPublicacao[]>("/api/publicacoes/minhas/");
  return data;
}

export function baixarMinhaPublicacao(id: string) {
  return downloadBlob(`/api/publicacoes/minhas/${id}/arquivo/`, "");
}

export async function listPublicPublicacoes(schema: string): Promise<PublicacaoBase[]> {
  const { data } = await api.get<PublicacaoBase[]>("/api/publicacoes/public/", { params: { schema } });
  return data;
}

export async function getPublicPublicacao(schema: string, slug: string): Promise<PublicacaoBase> {
  const { data } = await api.get<PublicacaoBase>(`/api/publicacoes/public/${slug}/`, { params: { schema } });
  return data;
}

export function publicPublicacaoArquivoUrl(schema: string, slug: string): string {
  const base = import.meta.env.VITE_API_URL ?? "";
  return `${base}/api/publicacoes/public/${slug}/arquivo/?schema=${encodeURIComponent(schema)}`;
}
