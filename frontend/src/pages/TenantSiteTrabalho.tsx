import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Copy, FileDown } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getPublicTrabalho, publicTrabalhoPdfUrl } from "@/services/eventos";
import type { PublicTrabalho } from "@/types/eventos";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

const FORMATOS = [
  { id: "abnt", label: "ABNT" },
  { id: "apa", label: "APA" },
  { id: "bibtex", label: "BibTeX" },
] as const;

/** Metadados Highwire (`citation_*`) lidos por indexadores acadêmicos como o Google Acadêmico. */
function useMetadadosCitacao(t: PublicTrabalho | null, pdfUrl: string) {
  useEffect(() => {
    if (!t) return;
    const tags: [string, string][] = [
      ["citation_title", t.titulo],
      ...t.autores.map((a): [string, string] => ["citation_author", a.nome]),
      ["citation_publication_date", t.publicado_em.slice(0, 10).replace(/-/g, "/")],
      ["citation_conference_title", t.evento.titulo],
      ["citation_inbook_title", t.anais.titulo],
      ["citation_publisher", t.associacao],
      ["citation_abstract_html_url", t.url],
      ["citation_pdf_url", new URL(pdfUrl, window.location.origin).toString()],
      ...t.palavras_chave.map((k): [string, string] => ["citation_keywords", k]),
      ...(t.anais.issn ? [["citation_issn", t.anais.issn] as [string, string]] : []),
      ...(t.anais.isbn ? [["citation_isbn", t.anais.isbn] as [string, string]] : []),
      ...(t.doi ? [["citation_doi", t.doi] as [string, string]] : []),
      ["description", t.resumo.slice(0, 300)],
    ];
    const criadas = tags.map(([name, content]) => {
      const meta = document.createElement("meta");
      meta.name = name;
      meta.content = content;
      meta.dataset.citacao = "1";
      document.head.appendChild(meta);
      return meta;
    });
    const tituloAnterior = document.title;
    document.title = `${t.titulo} — ${t.anais.titulo}`;
    return () => {
      criadas.forEach((m) => m.remove());
      document.title = tituloAnterior;
    };
  }, [t, pdfUrl]);
}

export default function TenantSiteTrabalho() {
  const { slug = "", trabalho: trabalhoSlug = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [trabalho, setTrabalho] = useState<PublicTrabalho | null>(null);
  const [formato, setFormato] = useState<(typeof FORMATOS)[number]["id"]>("abnt");
  const [copiado, setCopiado] = useState(false);
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);
  const pdfUrl = publicTrabalhoPdfUrl(schema, slug, trabalhoSlug);

  useEffect(() => {
    setError("");
    getPublicTrabalho(schema, slug, trabalhoSlug)
      .then(setTrabalho)
      .catch(() => setError("Trabalho não encontrado."));
  }, [schema, slug, trabalhoSlug]);

  useMetadadosCitacao(trabalho, pdfUrl);

  if (shellError || error) return <div className="tenant-site-empty">{error || "Site não encontrado."}</div>;
  if (!payload || !trabalho) return <div className="tenant-site-empty">Carregando…</div>;

  const copiar = async () => {
    await navigator.clipboard.writeText(trabalho.citacoes[formato]);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  const { anais } = trabalho;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site/eventos/${slug}/anais${q}`}>← {anais.titulo}</Link>
        </p>

        <div className="course-player" style={{ gridTemplateColumns: "1fr 300px" }}>
          <article>
            <h1 style={{ marginTop: 0 }}>{trabalho.titulo}</h1>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1rem" }}>
              {trabalho.autores.map((a) => (
                <li key={a.nome}>
                  <strong>{a.nome}</strong>
                  {a.instituicao && <span className="course-muted"> · {a.instituicao}</span>}
                  {a.orcid && (
                    <>
                      {" "}
                      <a href={`https://orcid.org/${a.orcid}`} target="_blank" rel="noreferrer">
                        ORCID
                      </a>
                    </>
                  )}
                </li>
              ))}
            </ul>

            <h2>Resumo</h2>
            <p style={{ whiteSpace: "pre-line" }}>{trabalho.resumo}</p>
            {trabalho.palavras_chave.length > 0 && (
              <p>
                <strong>Palavras-chave:</strong> {trabalho.palavras_chave.join("; ")}
              </p>
            )}
            {trabalho.area_tematica && (
              <p>
                <strong>Área temática:</strong> {trabalho.area_tematica}
              </p>
            )}

            <h2 style={{ marginTop: "2rem" }}>Como citar</h2>
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
              {FORMATOS.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={formato === f.id ? "tenant-site-btn-primary" : "tenant-site-btn-outline"}
                  onClick={() => setFormato(f.id)}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                background: "var(--ts-bg)",
                padding: "1rem",
                borderRadius: 8,
                fontFamily: formato === "bibtex" ? "monospace" : "inherit",
                fontSize: "0.9rem",
              }}
            >
              {trabalho.citacoes[formato]}
            </pre>
            <button type="button" className="tenant-site-btn-outline" onClick={() => void copiar()}>
              <Copy size={14} /> {copiado ? "Copiado!" : "Copiar citação"}
            </button>
          </article>

          <aside className="course-card" style={{ position: "sticky", top: "1rem", alignSelf: "start" }}>
            <a className="tenant-site-btn-primary" href={pdfUrl} target="_blank" rel="noreferrer">
              <FileDown size={16} /> {trabalho.tem_arquivo_final ? "Baixar trabalho (PDF)" : "Baixar resumo (PDF)"}
            </a>
            <dl style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
              <dt className="course-muted">Publicado em</dt>
              <dd style={{ margin: "0 0 0.75rem" }}>
                <Link to={`/site/eventos/${slug}/anais${q}`}>{anais.titulo}</Link>
              </dd>
              <dt className="course-muted">Evento</dt>
              <dd style={{ margin: "0 0 0.75rem" }}>
                <Link to={`/site/eventos/${slug}${q}`}>{trabalho.evento.titulo}</Link>
                {trabalho.evento.local && ` · ${trabalho.evento.local}`}
              </dd>
              {trabalho.doi && (
                <>
                  <dt className="course-muted">DOI</dt>
                  <dd style={{ margin: "0 0 0.75rem" }}>
                    <a href={`https://doi.org/${trabalho.doi}`} target="_blank" rel="noreferrer">
                      {trabalho.doi}
                    </a>
                  </dd>
                </>
              )}
              {(anais.issn || anais.isbn) && (
                <>
                  <dt className="course-muted">Identificadores</dt>
                  <dd style={{ margin: "0 0 0.75rem" }}>
                    {[anais.issn && `ISSN ${anais.issn}`, anais.isbn && `ISBN ${anais.isbn}`].filter(Boolean).join(" · ")}
                  </dd>
                </>
              )}
              <dt className="course-muted">Licença</dt>
              <dd style={{ margin: 0 }}>
                {anais.licenca_url ? (
                  <a href={anais.licenca_url} target="_blank" rel="noreferrer license">
                    {anais.licenca_display}
                  </a>
                ) : (
                  anais.licenca_display
                )}
              </dd>
            </dl>
          </aside>
        </div>
      </section>
    </SiteShell>
  );
}
