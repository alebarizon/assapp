import type { CatalogItem } from "@/types/ecommerce";

type CatalogPriceLike = Pick<CatalogItem, "price" | "currency">;

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

export function formatBRL(raw: string | number, currency = "BRL"): string {
  const value = Number(raw);
  if (Number.isNaN(value)) return String(raw);
  return value.toLocaleString("pt-BR", { style: "currency", currency: currency || "BRL" });
}

export function formatCatalogPrice(item: CatalogPriceLike): string {
  return formatBRL(item.price, item.currency);
}

/** Preço de sócio só conta quando é menor que o cheio. */
export function temPrecoSocio(item: Pick<CatalogItem, "price" | "member_price">): boolean {
  return item.member_price != null && Number(item.member_price) < Number(item.price);
}
