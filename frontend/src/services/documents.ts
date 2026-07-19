import { api } from "./api";

export type DocumentAudience = "geral" | "diretoria" | "membro";

export interface DocumentItem {
  id: string;
  title: string;
  file?: string;
  file_url?: string | null;
  file_type?: string | null;
  description?: string | null;
  audience: DocumentAudience;
  audience_display: string;
  membro?: string | null;
  membro_nome?: string | null;
  uploaded_by_email?: string | null;
  created_at: string;
}

export async function listDocuments(params?: {
  audience?: string;
  membro?: string;
}): Promise<DocumentItem[]> {
  const { data } = await api.get<{ results?: DocumentItem[] } | DocumentItem[]>(
    "/api/documents/",
    { params }
  );
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createDocument(form: FormData): Promise<DocumentItem> {
  const { data } = await api.post<DocumentItem>("/api/documents/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/api/documents/${id}/`);
}

export function documentDownloadUrl(id: string): string {
  const base = api.defaults.baseURL || "";
  return `${base}/api/documents/${id}/download/`;
}

export async function listMeusDocumentos(): Promise<DocumentItem[]> {
  const { data } = await api.get<{ results?: DocumentItem[] } | DocumentItem[]>(
    "/api/documents/meus/"
  );
  return Array.isArray(data) ? data : data.results ?? [];
}

export function meuDocumentoDownloadUrl(id: string): string {
  const base = api.defaults.baseURL || "";
  return `${base}/api/documents/meus/${id}/download/`;
}
