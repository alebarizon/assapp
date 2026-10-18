import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getPublicAnais } from "@/services/eventos";
import type { PublicAnais, PublicTrabalhoResumo } from "@/types/eventos";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

function agruparPorArea(trabalhos: PublicTrabalhoResumo[]): [string, PublicTrabalhoResumo[]][] {
  const grupos = new Map<string, PublicTrabalhoResumo[]>();
  trabalhos.forEach((t) => {
    const area = t.area_tematica || "Trabalhos";
    grupos.set(area, [...(grupos.get(area) ?? []), t]);
  });
  return [...grupos.entries()];
}

export default function TenantSiteAnais() {
  const { slug = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [anais, setAnais] = useState<PublicAnais | null>(null);
  const [busca, setBusca] = useState("");
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    setError("");
    getPublicAnais(schema, slug)
      .then(setAnais)
      .catch(() => setError("Anais não encontrados."));
  }, [schema, slug]);

  useEffect(() => {
    if (anais) document.title = anais.titulo;
  }, [anais]);

  if (shellError || error) return <div className="tenant-site-empty">{error || "Site não encontrado."}</div>;
  if (!payload || !anais) return <div className="tenant-site-empty">Carregando…</div>;

  const termo = busca.trim().toLowerCase();
  const filtrados = termo
    ? anais.trabalhos.filter((t) =>
        [t.titulo, ...t.autores.map((a) => a.nome), ...t.palavras_chave].join(" ").toLowerCase().includes(termo)
      )
    : anais.trabalhos;
  const identificadores = [anais.issn && `ISSN ${anais.issn}`, anais.isbn && `ISBN ${anais.isbn}`].filter(Boolean);

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site/eventos/${anais.evento.slug}${q}`}>← {anais.evento.titulo}</Link>
        </p>
        <h1 style={{ marginTop: 0 }}>{anais.titulo}</h1>
        <p className="course-muted">
          {[
            anais.editores && `Organização: ${anais.editores}`,
            anais.cidade,
            new Date(anais.publicado_em).getFullYear(),
            ...identificadores,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
        {anais.apresentacao && <p style={{ whiteSpace: "pre-line" }}>{anais.apresentacao}</p>}
        <p className="course-muted">
          {anais.trabalhos.length} trabalho(s) · Licença{" "}
          {anais.licenca_url ? (
            <a href={anais.licenca_url} target="_blank" rel="noreferrer license">
              {anais.licenca_display}
            </a>
          ) : (
            anais.licenca_display
          )}
        </p>

        <input
          className="form-input"
          style={{ maxWidth: "28rem", margin: "1rem 0" }}
          placeholder="Buscar por título, autor ou palavra-chave"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />

        {filtrados.length === 0 ? (
          <p className="course-muted">Nenhum trabalho encontrado.</p>
        ) : (
          agruparPorArea(filtrados).map(([area, itens]) => (
            <div key={area} className="course-section-card">
              <div className="course-section-header">{area}</div>
              {itens.map((t) => (
                <div key={t.slug} className="course-lesson-row" style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <Link to={`/site/eventos/${anais.evento.slug}/anais/${t.slug}${q}`}>
                      <strong>{t.titulo}</strong>
                    </Link>
                    <div className="course-muted">{t.autores.map((a) => a.nome).join("; ")}</div>
                    {t.doi && <div className="course-muted">DOI {t.doi}</div>}
                  </div>
                </div>
              ))}
            </div>
          ))
        )}
      </section>
    </SiteShell>
  );
}
