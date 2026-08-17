import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPublicSite, getPublicSitePage } from "@/services/website";
import type { SitePage, WebsiteConfig } from "@/types/website";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";

export default function TenantSitePageView() {
  const { slug = "" } = useParams();
  const schema = useTenantSchema();
  const [page, setPage] = useState<SitePage | null>(null);
  const [shell, setShell] = useState<{ config: WebsiteConfig; tenant_name: string } | null>(
    null
  );
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    (async () => {
      try {
        const [pageRes, site] = await Promise.all([
          getPublicSitePage(schema, slug),
          getPublicSite(schema),
        ]);
        setPage(pageRes.page);
        setShell({ config: site.config, tenant_name: site.tenant_name });
      } catch {
        setError("Página não encontrada.");
      }
    })();
  }, [schema, slug]);

  if (error) {
    return <div className="tenant-site-empty">{error}</div>;
  }
  if (!page || !shell) {
    return <div className="tenant-site-empty">Carregando…</div>;
  }

  const payload = {
    schema,
    tenant_name: shell.tenant_name,
    config: shell.config,
    news: [],
    diretoria: null,
  };

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site${q}`}>← Voltar</Link>
        </p>
        <p style={{ fontSize: "0.85rem", color: "var(--ts-muted)" }}>{page.page_type_display}</p>
        <h1 style={{ marginTop: "0.25rem" }}>{page.title}</h1>
        {page.summary && <p style={{ color: "var(--ts-muted)" }}>{page.summary}</p>}
        <div className="tenant-site-prose" style={{ marginTop: "1.25rem" }}>
          {page.content}
        </div>
      </section>
    </SiteShell>
  );
}
