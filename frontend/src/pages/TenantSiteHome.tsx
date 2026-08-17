import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPublicSite } from "@/services/website";
import type { PublicSitePayload } from "@/types/website";
import { AssocieSeBox, SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";

export default function TenantSiteHome() {
  const schema = useTenantSchema();
  const [data, setData] = useState<PublicSitePayload | null>(null);
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    (async () => {
      setError("");
      try {
        setData(await getPublicSite(schema));
      } catch {
        setError(
          `Site não disponível para "${schema}". Publique em /app/website ou rode init_demo_tenant.sh.`
        );
      }
    })();
  }, [schema]);

  if (error) {
    return (
      <div className="tenant-site">
        <div className="tenant-site-empty">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="tenant-site">
        <div className="tenant-site-empty">Carregando site…</div>
      </div>
    );
  }

  const { config, news, diretoria } = data;

  return (
    <SiteShell payload={data} schema={schema}>
      <section className="tenant-site-hero">
        <div className="tenant-site-hero-inner">
          <p style={{ opacity: 0.85, margin: "0 0 0.5rem", fontSize: "0.9rem" }}>
            {config.site_tagline}
          </p>
          <h1>{config.hero_title || config.site_title}</h1>
          <p>{config.hero_subtitle}</p>
          {config.hero_cta_label && (
            <a className="tenant-site-btn" href={config.hero_cta_link || "#sobre"}>
              {config.hero_cta_label}
            </a>
          )}
        </div>
      </section>

      <section className="tenant-site-section" id="sobre">
        <h2>{config.about_title}</h2>
        <p className="tenant-site-prose">{config.about_text}</p>
        {diretoria && (
          <div style={{ marginTop: "1.5rem" }}>
            <h3 style={{ fontSize: "1.05rem" }}>Diretoria atual — {diretoria.titulo}</h3>
            <ul className="tenant-site-diretoria-list">
              {(diretoria.cargos ?? []).map((c, i) => (
                <li key={i}>
                  <strong>{c.cargo_display || c.cargo}</strong>
                  {c.usuario_nome ? ` — ${c.usuario_nome}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="tenant-site-section" id="noticias">
        <h2>Notícias</h2>
        {news.length === 0 ? (
          <p style={{ color: "var(--ts-muted)" }}>Nenhuma notícia publicada.</p>
        ) : (
          <div className="tenant-site-grid">
            {news.map((n) => (
              <article key={n.id} className="tenant-site-card">
                <h3>{n.title}</h3>
                <p>{n.summary}</p>
                <p style={{ marginTop: "0.5rem" }}>
                  <Link to={`/site/p/${n.slug}${q}`}>Ler mais</Link>
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      <AssocieSeBox
        title={config.associe_se_title}
        lead={config.associe_se_lead}
        categories={config.associe_se_categories ?? []}
        catalogItems={data.associe_se_items}
        ctaLabel={config.associe_se_cta_label}
        ctaLink={config.associe_se_cta_link}
        schema={schema}
      />

      <section className="tenant-site-section" id="contato">
        <h2>Contato</h2>
        <div className="tenant-site-card" style={{ maxWidth: 480 }}>
          {config.contact_email && <p>E-mail: {config.contact_email}</p>}
          {config.contact_phone && <p>Telefone: {config.contact_phone}</p>}
          {config.contact_address && <p>{config.contact_address}</p>}
        </div>
      </section>
    </SiteShell>
  );
}
