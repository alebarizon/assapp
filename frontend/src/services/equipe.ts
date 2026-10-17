import type { LoginResponse, PerfilAcesso } from "@/types";
import type { ConvitePayload, PerfisInfo, UsuarioEquipe } from "@/types/equipe";
import { api } from "./api";

const BASE = "/api/auth/equipe/";

export async function listEquipe(): Promise<UsuarioEquipe[]> {
  const { data } = await api.get<UsuarioEquipe[]>(BASE);
  return data;
}

export async function getPerfisInfo(): Promise<PerfisInfo> {
  const { data } = await api.get<PerfisInfo>(`${BASE}perfis/`);
  return data;
}

export async function convidarUsuario(payload: ConvitePayload): Promise<UsuarioEquipe> {
  const { data } = await api.post<UsuarioEquipe>(BASE, payload);
  return data;
}

export async function atualizarUsuario(
  id: string,
  payload: Partial<{ perfis: PerfilAcesso[]; is_active: boolean; first_name: string; last_name: string }>
): Promise<UsuarioEquipe> {
  const { data } = await api.patch<UsuarioEquipe>(`${BASE}${id}/`, payload);
  return data;
}

export async function reenviarConvite(id: string): Promise<{ email_enviado: boolean }> {
  const { data } = await api.post<{ email_enviado: boolean }>(`${BASE}${id}/reenviar-convite/`);
  return data;
}

export async function esqueciSenha(email: string, schema?: string | null): Promise<string> {
  const { data } = await api.post<{ detail: string }>("/api/auth/senha/esqueci/", {
    email,
    ...(schema ? { schema } : {}),
  });
  return data.detail;
}

export interface LinkSenha {
  schema: string;
  uid: string;
  token: string;
}

export async function validarLinkSenha(link: LinkSenha): Promise<{ email: string; first_name: string }> {
  const { data } = await api.get<{ email: string; first_name: string }>("/api/auth/senha/definir/", {
    params: link,
  });
  return data;
}

export async function definirSenha(link: LinkSenha, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/api/auth/senha/definir/", { ...link, password });
  return data;
}
