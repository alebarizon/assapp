import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { resolveTenantByHost } from "@/services/tenants";
import type { PublicCatalogItem, PublicSitePayload } from "@/types/website";
import {
  buildAssocieSeCtaLink,
  buildTenantSiteQuery,
  formatCatalogPrice,
  resolveTenantSchema,
  resolveTenantSchemaFromHost,
} from "@/utils/tenantSite";
import "./TenantSite.css";

export function useTenantSchema(): string {
  const [searchParams] = useSearchParams();
  const [schema, setSchema] = useState(() => resolveTenantSchema(searchParams));

  useEffect(() => {
    const immediate = resolveTenantSchema(searchParams);
    setSchema(immediate);

    const fromHost = resolveTenantSchemaFromHost();
    if (fromHost || searchParams.get("schema")) return;

    void resolveTenantByHost().then((resolved) => {
      if (resolved?.schema) setSchema(resolved.schema);
    });
  }, [searchParams]);

  return schema;
}

export function SiteShell({
  payload,
  schema,
  children,
}: {
  payload: PublicSitePayload;
  schema: string;
  children: React.ReactNode;
}) {
  const q = buildTenantSiteQuery(schema);
  const { config } = payload;

  return (
    <div
      className="tenant-site"
      style={
        {
          "--ts-primary": config.primary_color,
          "--ts-secondary": config.secondary_color,
        } as React.CSSProperties
      }
    >
      <header className="tenant-site-header">
        <div className="tenant-site-header-inner">
          <Link to={`/site${q}`} className="tenant-site-brand">
            {config.site_title}
          </Link>
          <nav className="tenant-site-nav">
            <Link to={`/site${q}#sobre`}>A instituição</Link>
            <Link to={`/site${q}#noticias`}>Notícias</Link>
            <Link to={`/site${q}#associe-se`}>Associe-se</Link>
            <Link to={`/site${q}#contato`}>Contato</Link>
            <Link to={buildAssocieSeCtaLink(schema, config.associe_se_cta_link)}>
              Entrar
            </Link>
          </nav>
        </div>
      </header>
      {children}
      <footer className="tenant-site-footer">
        <p>
          {config.site_title} · Site publicado via{" "}
          <a href="/" style={{ color: "inherit" }}>
            Gesttora
          </a>
        </p>
      </footer>
    </div>
  );
}

export function AssocieSeBox({
  title,
  lead,
  categories,
  catalogItems,
  ctaLabel,
  ctaLink,
  schema,
}: {
  title: string;
  lead: string;
  categories: { label: string; hint?: string }[];
  catalogItems?: PublicCatalogItem[];
  ctaLabel: string;
  ctaLink: string;
  schema: string;
}) {
  const href = buildAssocieSeCtaLink(schema, ctaLink);

  return (
    <section className="tenant-site-section" id="associe-se">
      <div className="tenant-site-associe-se">
        <h2>{title}</h2>
        <p className="tenant-site-prose" style={{ marginBottom: "0.5rem" }}>
          {lead}
        </p>

        {catalogItems && catalogItems.length > 0 ? (
          <div className="tenant-site-categories">
            {catalogItems.map((item) => (
              <div key={item.id} className="tenant-site-category">
                <strong>{item.name}</strong>
                <span>{formatCatalogPrice(item)}</span>
                {item.description && (
                  <span style={{ display: "block", marginTop: "0.25rem" }}>{item.description}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          categories.length > 0 && (
            <div className="tenant-site-categories">
              {categories.map((cat) => (
                <div key={cat.label} className="tenant-site-category">
                  <strong>{cat.label}</strong>
                  {cat.hint && <span>{cat.hint}</span>}
                </div>
              ))}
            </div>
          )
        )}

        <a className="tenant-site-btn" href={href} style={{ marginTop: "0.5rem" }}>
          {ctaLabel}
        </a>
        <p style={{ fontSize: "0.8rem", color: "var(--ts-muted)", marginTop: "0.75rem" }}>
          Após entrar, você será direcionado à loja para concluir a filiação ou renovação.
        </p>
      </div>
    </section>
  );
}
