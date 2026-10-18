import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { listPublicPublicacoes } from "@/services/publicacoes";
import type { PublicacaoBase } from "@/types/publicacoes";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

export default function TenantSitePublicacoes() {
  const schema = useTenantSchema();
  const { payload, error } = useSiteShell(schema);
  const [itens, setItens] = useState<PublicacaoBase[] | null>(null);
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    listPublicPublicacoes(schema)
      .then(setItens)
      .catch(() => setItens([]));
  }, [schema]);

  if (error) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <h1>Publicações</h1>
        <p style={{ color: "var(--ts-muted)" }}>Dossiês, e-books e boletins da associação.</p>

        {itens === null ? (
          <p>Carregando…</p>
        ) : itens.length === 0 ? (
          <p style={{ color: "var(--ts-muted)" }}>Nenhuma publicação disponível no momento.</p>
        ) : (
          <div className="course-card-grid" style={{ marginTop: "1rem" }}>
            {itens.map((p) => (
              <Link key={p.id} to={`/site/publicacoes/${p.slug}${q}`} className="course-card">
                <div
                  className="course-card-cover"
                  style={{ backgroundImage: p.capa_url ? `url(${p.capa_url})` : undefined }}
                />
                <div className="course-card-body">
                  <span className="course-muted">
                    {p.tipo_display}
                    {p.ano ? ` · ${p.ano}` : ""}
                  </span>
                  <h3 className="course-card-title">{p.titulo}</h3>
                  {p.autores.length > 0 && (
                    <span className="course-muted">{p.autores.map((a) => a.nome).join(", ")}</span>
                  )}
                  <strong style={{ marginTop: "auto" }}>
                    {p.acesso === "publico" ? "Acesso aberto" : p.acesso === "associados" ? "Para associados" : "À venda"}
                  </strong>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </SiteShell>
  );
}
