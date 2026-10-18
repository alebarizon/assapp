import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BookOpen, FileDown, LogIn } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getPublicPublicacao, publicPublicacaoArquivoUrl } from "@/services/publicacoes";
import type { PublicacaoBase } from "@/types/publicacoes";
import { buildTenantSiteQuery, formatBRL } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";
import "@/components/publicacoes/Publicacoes.css";

export default function TenantSitePublicacao() {
  const { slug = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [pub, setPub] = useState<PublicacaoBase | null>(null);
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    setError("");
    getPublicPublicacao(schema, slug)
      .then(setPub)
      .catch(() => setError("Publicação não encontrada."));
  }, [schema, slug]);

  useEffect(() => {
    if (!pub) return;
    const anterior = document.title;
    document.title = pub.titulo;
    return () => {
      document.title = anterior;
    };
  }, [pub]);

  if (shellError || error) return <div className="tenant-site-empty">{error || "Site não encontrado."}</div>;
  if (!payload || !pub) return <div className="tenant-site-empty">Carregando…</div>;

  const login = `/login?schema=${encodeURIComponent(schema)}&next=${encodeURIComponent("/app/portal/publicacoes")}`;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site/publicacoes${q}`}>← Publicações</Link>
        </p>
        <div className="pub-detalhe">
          <div>
            <div
              className="pub-capa"
              style={{ borderRadius: 10, ...(pub.capa_url ? { backgroundImage: `url(${pub.capa_url})` } : {}) }}
            >
              {!pub.capa_url && <BookOpen size={48} />}
            </div>
            <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {pub.acesso === "publico" ? (
                pub.tem_arquivo && (
                  <a className="tenant-site-btn-primary" href={publicPublicacaoArquivoUrl(schema, slug)}>
                    <FileDown size={16} /> Baixar
                  </a>
                )
              ) : (
                <>
                  <a className="tenant-site-btn-primary" href={login}>
                    <LogIn size={16} /> {pub.acesso === "associados" ? "Acessar no portal" : "Comprar no portal"}
                  </a>
                  <p className="course-muted" style={{ margin: 0, fontSize: "0.85rem" }}>
                    {pub.acesso === "associados" && "Incluída para associados em dia."}
                    {pub.preco && ` ${pub.acesso === "associados" ? "Demais interessados: " : ""}${formatBRL(pub.preco)}`}
                    {pub.preco_socio && ` · sócio ${formatBRL(pub.preco_socio)}`}
                  </p>
                </>
              )}
            </div>
          </div>

          <article>
            <span className="course-muted">
              {pub.tipo_display}
              {pub.edicao ? ` · ${pub.edicao}` : ""}
              {pub.ano ? ` · ${pub.ano}` : ""}
            </span>
            <h1 style={{ margin: "0.25rem 0" }}>{pub.titulo}</h1>
            {pub.subtitulo && <p style={{ fontSize: "1.1rem", marginTop: 0 }}>{pub.subtitulo}</p>}
            {pub.autores.length > 0 && (
              <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1rem" }}>
                {pub.autores.map((a) => (
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
            )}
            {pub.resumo && <p style={{ whiteSpace: "pre-line" }}>{pub.resumo}</p>}
            {pub.palavras_chave.length > 0 && (
              <p>
                <strong>Palavras-chave:</strong> {pub.palavras_chave.join("; ")}
              </p>
            )}
            {(pub.isbn || pub.issn) && (
              <p className="course-muted">
                {[pub.isbn && `ISBN ${pub.isbn}`, pub.issn && `ISSN ${pub.issn}`].filter(Boolean).join(" · ")}
              </p>
            )}
          </article>
        </div>
      </section>
    </SiteShell>
  );
}
