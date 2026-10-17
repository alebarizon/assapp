import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { listPublicCourses } from "@/services/courses";
import type { PublicCourse } from "@/types/courses";
import { COURSE_LEVELS } from "@/types/courses";
import { buildTenantSiteQuery, formatCatalogPrice } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

const levelLabel = (value: string) => COURSE_LEVELS.find((l) => l.value === value)?.label ?? value;

export default function TenantSiteCourses() {
  const schema = useTenantSchema();
  const { payload, error } = useSiteShell(schema);
  const [courses, setCourses] = useState<PublicCourse[] | null>(null);
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    listPublicCourses(schema)
      .then(setCourses)
      .catch(() => setCourses([]));
  }, [schema]);

  if (error) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <h1>Cursos</h1>
        <p style={{ color: "var(--ts-muted)" }}>
          Cursos online oferecidos pela associação, com certificado de conclusão.
        </p>

        {courses === null ? (
          <p>Carregando…</p>
        ) : courses.length === 0 ? (
          <p style={{ color: "var(--ts-muted)" }}>Nenhum curso disponível no momento.</p>
        ) : (
          <div className="course-card-grid" style={{ marginTop: "1.25rem" }}>
            {courses.map((c) => (
              <Link key={c.id} to={`/site/cursos/${c.slug}${q}`} className="course-card">
                <div
                  className="course-card-cover"
                  style={{ backgroundImage: c.cover_image_url ? `url(${c.cover_image_url})` : undefined }}
                />
                <div className="course-card-body">
                  <h3 className="course-card-title">{c.title}</h3>
                  {c.short_description && <span className="course-muted">{c.short_description}</span>}
                  <span className="course-muted">
                    {levelLabel(c.level)} · {c.lessons_count} aulas
                    {c.workload_hours ? ` · ${c.workload_hours} h` : ""}
                  </span>
                  <strong style={{ marginTop: "auto" }}>
                    {c.catalog_item_info ? formatCatalogPrice(c.catalog_item_info) : "Exclusivo para associados"}
                  </strong>
                </div>
              </Link>
            ))}
          </div>
        )}

        <p style={{ marginTop: "2rem", fontSize: "0.9rem" }}>
          Recebeu um certificado? <Link to={`/site/certificados${q}`}>Verifique a autenticidade</Link>.
        </p>
      </section>
    </SiteShell>
  );
}
