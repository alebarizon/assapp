import { api } from "./api";

export interface TenantResolvePayload {
  schema: string;
  slug: string;
  name: string;
}

export async function resolveTenantByHost(host?: string): Promise<TenantResolvePayload | null> {
  try {
    const { data } = await api.get<TenantResolvePayload>("/api/tenants/public/resolve/", {
      params: host ? { host } : undefined,
    });
    return data;
  } catch {
    return null;
  }
}
