import React, { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getDiretorio, type ResultadoDiretorio } from "@/services/membros";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

export default function TenantSiteDiretorio() {
  const schema = useTenantSchema();
  const { payload, error } = useSiteShell(schema);
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState({ q: "", instituicao: "", pagina: 1 });
  const [dados, setDados] = useState<ResultadoDiretorio | null>(null);
  const [indisponivel, setIndisponivel] = useState(false);

  useEffect(() => {
    getDiretorio(schema, filtro)
      .then((r) => {
        setDados(r);
        setIndisponivel(false);
      })
      .catch(() => setIndisponivel(true));
  }, [schema, filtro]);

  const buscar = (e: React.FormEvent) => {
    e.preventDefault();
    setFiltro({ ...filtro, q: busca.trim(), pagina: 1 });
  };

  if (error) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <h1>Associados</h1>
        <p style={{ color: "var(--ts-muted)" }}>
          Pesquisadores e profissionais filiados que autorizaram a divulgação do perfil.
        </p>

        {indisponivel ? (
          <p style={{ color: "var(--ts-muted)" }}>O diretório de associados não está disponível.</p>
        ) : (
          <>
            <form onSubmit={buscar} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", margin: "1rem 0" }}>
              <div style={{ position: "relative", flex: "1 1 260px" }}>
                <Search size={16} style={{ position: "absolute", left: 12, top: 12, color: "#98a2b3" }} />
                <input
                  className="form-input"
                  style={{ paddingLeft: 36, width: "100%" }}
                  placeholder="Nome, instituição, área ou tema"
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                />
              </div>
              <select
                className="form-select"
                style={{ flex: "0 1 260px" }}
                value={filtro.instituicao}
                onChange={(e) => setFiltro({ ...filtro, instituicao: e.target.value, pagina: 1 })}
              >
                <option value="">Todas as instituições</option>
                {dados?.instituicoes.map((i) => (
                  <option key={i.nome} value={i.nome}>
                    {i.nome} ({i.total})
                  </option>
                ))}
              </select>
              <button type="submit" className="tenant-site-btn">
                Buscar
              </button>
            </form>

            {!dados ? (
              <p>Carregando…</p>
            ) : dados.resultados.length === 0 ? (
              <p style={{ color: "var(--ts-muted)" }}>Nenhum associado encontrado.</p>
            ) : (
              <>
                <p className="course-muted">{dados.total} associado(s)</p>
                <div className="course-card-grid">
                  {dados.resultados.map((m) => (
                    <article key={m.id} className="course-card">
                      <div className="course-card-body">
                        <span className="course-muted">
                          {m.categoria}
                          {m.membro_desde ? ` · desde ${m.membro_desde}` : ""}
                        </span>
                        <h3 className="course-card-title">{m.nome}</h3>
                        {(m.instituicao || m.area_atuacao) && (
                          <span>{[m.instituicao, m.area_atuacao].filter(Boolean).join(" · ")}</span>
                        )}
                        {m.mini_bio && <p className="course-muted" style={{ margin: "0.5rem 0 0" }}>{m.mini_bio}</p>}
                        {(m.lattes_url || m.orcid) && (
                          <div style={{ display: "flex", gap: "0.75rem", marginTop: "auto", paddingTop: "0.75rem", fontSize: "0.85rem" }}>
                            {m.lattes_url && (
                              <a href={m.lattes_url} target="_blank" rel="noopener noreferrer">
                                Lattes
                              </a>
                            )}
                            {m.orcid && (
                              <a href={`https://orcid.org/${m.orcid}`} target="_blank" rel="noopener noreferrer">
                                ORCID
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
                {dados.paginas > 1 && (
                  <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", marginTop: "1.5rem" }}>
                    <button
                      type="button"
                      className="tenant-site-btn"
                      disabled={dados.pagina <= 1}
                      onClick={() => setFiltro({ ...filtro, pagina: dados.pagina - 1 })}
                    >
                      Anterior
                    </button>
                    <span className="course-muted" style={{ alignSelf: "center" }}>
                      {dados.pagina} de {dados.paginas}
                    </span>
                    <button
                      type="button"
                      className="tenant-site-btn"
                      disabled={dados.pagina >= dados.paginas}
                      onClick={() => setFiltro({ ...filtro, pagina: dados.pagina + 1 })}
                    >
                      Próxima
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </section>
    </SiteShell>
  );
}
