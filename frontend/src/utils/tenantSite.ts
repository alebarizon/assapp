import type { CatalogItem } from "@/types/ecommerce";

/** Padrão dev: demo.localhost → schema demo */
export function resolveTenantSchemaFromHost(
  hostname = typeof window !== "undefined" ? window.location.hostname : ""
): string | null {
  const host = hostname.toLowerCase().replace(/^www\./, "");
  if (host.endsWith(".localhost")) {
    const slug = host.slice(0, -".localhost".length);
    if (slug && slug !== "localhost") return slug;
  }
  return null;
}

/** Link de login com redirect para a loja do portal associado. */
export function buildAssocieSeCtaLink(schema: string, customLink?: string): string {
  if (customLink && customLink !== "auto:loja" && !customLink.startsWith("auto:")) {
    return customLink;
  }
  const next = encodeURIComponent("/app/portal/loja");
  return `/login?schema=${encodeURIComponent(schema)}&next=${next}`;
}

export function buildTenantSiteQuery(schema: string): string {
  const fromHost = resolveTenantSchemaFromHost();
  if (fromHost === schema) return "";
  return `?schema=${encodeURIComponent(schema)}`;
}

export function resolveTenantSchema(searchParams: URLSearchParams): string {
  const fromQuery = searchParams.get("schema");
  if (fromQuery) return fromQuery;
  const fromHost = resolveTenantSchemaFromHost();
  if (fromHost) return fromHost;
  if (typeof window !== "undefined") {
    return localStorage.getItem("assapp_tenant_schema") || "demo";
  }
  return "demo";
}

export function formatCatalogPrice(item: CatalogItem): string {
  const value = Number(item.price);
  if (Number.isNaN(value)) return item.price;
  return value.toLocaleString("pt-BR", { style: "currency", currency: item.currency || "BRL" });
}
