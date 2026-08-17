import type { PublicSitePayload, SitePage, WebsiteConfig } from "@/types/website";
import { api } from "./api";

function tenantParams(schema: string) {
  return { schema };
}

export async function getPublicSite(schema: string): Promise<PublicSitePayload> {
  const { data } = await api.get<PublicSitePayload>("/api/website/public/", {
    params: tenantParams(schema),
  });
  return data;
}

export async function getPublicSitePage(
  schema: string,
  slug: string
): Promise<{ page: SitePage; config: WebsiteConfig | null }> {
  const { data } = await api.get<{ page: SitePage; config: WebsiteConfig | null }>(
    `/api/website/public/pages/${slug}/`,
    { params: tenantParams(schema) }
  );
  return data;
}

export async function getWebsiteConfig(): Promise<WebsiteConfig> {
  const { data } = await api.get<WebsiteConfig>("/api/website/config/");
  return data;
}

export async function updateWebsiteConfig(payload: Partial<WebsiteConfig>): Promise<WebsiteConfig> {
  const { data } = await api.patch<WebsiteConfig>("/api/website/config/", payload);
  return data;
}

export async function listSitePages(params?: { page_type?: string }): Promise<SitePage[]> {
  const { data } = await api.get<{ results?: SitePage[] } | SitePage[]>("/api/website/pages/", {
    params,
  });
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createSitePage(payload: Partial<SitePage>): Promise<SitePage> {
  const { data } = await api.post<SitePage>("/api/website/pages/", payload);
  return data;
}

export async function updateSitePage(slug: string, payload: Partial<SitePage>): Promise<SitePage> {
  const { data } = await api.patch<SitePage>(`/api/website/pages/${slug}/`, payload);
  return data;
}

export async function deleteSitePage(slug: string): Promise<void> {
  await api.delete(`/api/website/pages/${slug}/`);
}
