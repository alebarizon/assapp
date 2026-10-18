import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { listPublicEventos } from "@/services/eventos";
import type { PublicEvento } from "@/types/eventos";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import { periodoEvento } from "@/utils/programacao";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

export default function TenantSiteEventos() {
  const schema = useTenantSchema();
  const { payload, error } = useSiteShell(schema);
  const [eventos, setEventos] = useState<PublicEvento[] | null>(null);
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    listPublicEventos(schema)
      .then(setEventos)
      .catch(() => setEventos([]));
  }, [schema]);

  if (error) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  const agora = Date.now();
  const proximos = (eventos ?? []).filter((e) => new Date(e.data_fim).getTime() >= agora).reverse();
  const anteriores = (eventos ?? []).filter((e) => new Date(e.data_fim).getTime() < agora);

  const grade = (lista: PublicEvento[]) => (
    <div className="course-card-grid" style={{ marginTop: "1rem" }}>
      {lista.map((e) => (
        <Link key={e.id} to={`/site/eventos/${e.slug}${q}`} className="course-card">
          <div
            className="course-card-cover"
            style={{ backgroundImage: e.capa_url ? `url(${e.capa_url})` : undefined }}
          />
          <div className="course-card-body">
            <h3 className="course-card-title">{e.titulo}</h3>
            {e.resumo && <span className="course-muted">{e.resumo}</span>}
            <span className="course-muted">
              {periodoEvento(e.data_inicio, e.data_fim)} · {e.local || e.modalidade_display}
            </span>
            {e.inscricao.aberta && <strong style={{ marginTop: "auto" }}>Inscrições abertas</strong>}
          </div>
        </Link>
      ))}
    </div>
  );

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <h1>Eventos</h1>
        <p style={{ color: "var(--ts-muted)" }}>Congressos, encontros e seminários da associação.</p>

        {eventos === null ? (
          <p>Carregando…</p>
        ) : eventos.length === 0 ? (
          <p style={{ color: "var(--ts-muted)" }}>Nenhum evento publicado no momento.</p>
        ) : (
          <>
            {proximos.length > 0 && grade(proximos)}
            {anteriores.length > 0 && (
              <>
                <h2 style={{ marginTop: "2.5rem" }}>Edições anteriores</h2>
                {grade(anteriores)}
              </>
            )}
          </>
        )}
      </section>
    </SiteShell>
  );
}
