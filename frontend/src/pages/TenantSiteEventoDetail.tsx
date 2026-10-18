import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Video } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getPublicEvento } from "@/services/eventos";
import type { PublicEvento } from "@/types/eventos";
import { buildAssocieSeCtaLink, buildTenantSiteQuery, formatBRL } from "@/utils/tenantSite";
import { agruparPorDia, hora, periodoEvento } from "@/utils/programacao";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

function BlocoInscricao({ evento, schema }: { evento: PublicEvento; schema: string }) {
  const { inscricao } = evento;
  const gratuito = inscricao.price !== null && Number(inscricao.price) === 0;
  const temSocio =
    inscricao.member_price !== null && inscricao.price !== null && Number(inscricao.member_price) < Number(inscricao.price);

  return (
    <aside className="course-card" style={{ position: "sticky", top: "1rem" }}>
      <div
        className="course-card-cover"
        style={{ backgroundImage: evento.capa_url ? `url(${evento.capa_url})` : undefined }}
      />
      <div className="course-card-body">
        <span className="course-muted">{periodoEvento(evento.data_inicio, evento.data_fim)}</span>
        <span className="course-muted">{evento.local || evento.modalidade_display}</span>
        {inscricao.price !== null && (
          <strong style={{ fontSize: "1.4rem" }}>{gratuito ? "Gratuito" : formatBRL(inscricao.price)}</strong>
        )}
        {temSocio && (
          <span className="course-muted">
            Associado em dia paga{" "}
            {Number(inscricao.member_price) > 0 ? formatBRL(inscricao.member_price!) : "nada"}
          </span>
        )}
        {inscricao.aberta ? (
          <>
            <a className="tenant-site-btn" href={buildAssocieSeCtaLink(schema)}>
              Inscrever-se
            </a>
            <span className="course-muted">
              Entre na área do associado: a inscrição está na loja e é confirmada após o pagamento.
              {inscricao.vagas_restantes !== null && ` Restam ${inscricao.vagas_restantes} vaga(s).`}
            </span>
          </>
        ) : (
          <span className="course-muted">
            {inscricao.esgotada ? "Inscrições esgotadas." : "Inscrições não estão abertas."}
          </span>
        )}
        {evento.certificado_habilitado && (
          <span className="course-muted">
            Certificado de participação{evento.carga_horaria ? ` (${evento.carga_horaria} h)` : ""}.
          </span>
        )}
      </div>
    </aside>
  );
}

export default function TenantSiteEventoDetail() {
  const { slug = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [evento, setEvento] = useState<PublicEvento | null>(null);
  const [error, setError] = useState("");
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    setError("");
    getPublicEvento(schema, slug)
      .then(setEvento)
      .catch(() => setError("Evento não encontrado."));
  }, [schema, slug]);

  if (shellError || error) return <div className="tenant-site-empty">{error || "Site não encontrado."}</div>;
  if (!payload || !evento) return <div className="tenant-site-empty">Carregando…</div>;

  const { chamada } = evento;
  const programacao = evento.programacao ?? [];

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site/eventos${q}`}>← Todos os eventos</Link>
        </p>

        <div className="course-player" style={{ gridTemplateColumns: "1fr 320px" }}>
          <div>
            <h1 style={{ marginTop: 0 }}>{evento.titulo}</h1>
            {evento.resumo && <p style={{ color: "var(--ts-muted)" }}>{evento.resumo}</p>}
            {evento.descricao && <p style={{ whiteSpace: "pre-line" }}>{evento.descricao}</p>}

            {programacao.length > 0 && (
              <>
                <h2 style={{ marginTop: "2rem" }}>Programação</h2>
                {agruparPorDia(programacao).map(([dia, itens]) => (
                  <div key={dia} className="course-section-card">
                    <div className="course-section-header">
                      {dia}
                    </div>
                    {itens.map((a) => (
                      <div key={a.id} className="course-lesson-row" style={{ alignItems: "flex-start" }}>
                        <span className="course-muted" style={{ minWidth: "6.5rem" }}>
                          {hora(a.inicio)}–{hora(a.fim)}
                        </span>
                        <div style={{ flex: 1 }}>
                          <strong>{a.titulo}</strong>
                          <div className="course-muted">
                            {[a.tipo_display, a.sala, a.responsaveis].filter(Boolean).join(" · ")}
                          </div>
                          {a.descricao && <div style={{ marginTop: "0.25rem" }}>{a.descricao}</div>}
                        </div>
                        {a.link_transmissao && (
                          <a href={a.link_transmissao} target="_blank" rel="noreferrer" title="Transmissão">
                            <Video size={16} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </>
            )}

            {chamada && (
              <>
                <h2 style={{ marginTop: "2rem" }}>{chamada.titulo}</h2>
                <p className="course-muted">
                  {chamada.aberta ? "Submissões abertas" : "Submissões encerradas ou ainda não abertas"} ·{" "}
                  {new Date(chamada.data_abertura).toLocaleDateString("pt-BR")} a{" "}
                  {new Date(chamada.data_fechamento).toLocaleDateString("pt-BR")}
                </p>
                <p style={{ whiteSpace: "pre-line" }}>{chamada.instrucoes}</p>
                {chamada.areas_tematicas.length > 0 && (
                  <p>
                    <strong>Áreas temáticas:</strong> {chamada.areas_tematicas.join(" · ")}
                  </p>
                )}
                <p className="course-muted">
                  Até {chamada.max_submissoes_por_autor} trabalho(s) por autor
                  {chamada.anonimo ? " · avaliação duplo-cega" : ""}.
                </p>
                {chamada.aberta && (
                  <a
                    className="tenant-site-btn-primary"
                    href={`/login?schema=${encodeURIComponent(schema)}&next=${encodeURIComponent("/app/portal/trabalhos")}`}
                  >
                    Submeter trabalho pelo portal
                  </a>
                )}
              </>
            )}

            {evento.anais && (
              <>
                <h2 style={{ marginTop: "2rem" }}>Anais</h2>
                <p>
                  {evento.anais.titulo}
                  {evento.anais.issn ? ` · ISSN ${evento.anais.issn}` : ""}
                </p>
                {evento.anais.total_trabalhos > 0 ? (
                  <Link className="tenant-site-btn-primary" to={`/site/eventos/${evento.slug}/anais${q}`}>
                    Ver os {evento.anais.total_trabalhos} trabalhos publicados
                  </Link>
                ) : (
                  evento.anais.url_publicacao && (
                    <a href={evento.anais.url_publicacao} target="_blank" rel="noreferrer">
                      Acessar os anais
                    </a>
                  )
                )}
              </>
            )}
          </div>

          <BlocoInscricao evento={evento} schema={schema} />
        </div>
      </section>
    </SiteShell>
  );
}
