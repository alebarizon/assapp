import type { Catalogo, EntregaWebhook, WebhookSaida } from "@/types/integracoes";
import { api } from "./api";

const W = "/api/integracoes/webhooks";

export async function getCatalogo(): Promise<Catalogo> {
  return (await api.get<Catalogo>("/api/integracoes/catalogo/")).data;
}

export async function listWebhooks(): Promise<WebhookSaida[]> {
  return (await api.get<WebhookSaida[]>(`${W}/`)).data;
}

export async function salvarWebhook(id: string | null, payload: Partial<WebhookSaida>): Promise<WebhookSaida> {
  return id
    ? (await api.patch<WebhookSaida>(`${W}/${id}/`, payload)).data
    : (await api.post<WebhookSaida>(`${W}/`, payload)).data;
}

export async function deleteWebhook(id: string): Promise<void> {
  await api.delete(`${W}/${id}/`);
}

export async function testarWebhook(id: string): Promise<EntregaWebhook> {
  return (await api.post<EntregaWebhook>(`${W}/${id}/testar/`)).data;
}

export async function regenerarSegredo(id: string): Promise<WebhookSaida> {
  return (await api.post<WebhookSaida>(`${W}/${id}/regenerar-segredo/`)).data;
}

export async function listEntregas(id: string): Promise<EntregaWebhook[]> {
  return (await api.get<EntregaWebhook[]>(`${W}/${id}/entregas/`)).data;
}
