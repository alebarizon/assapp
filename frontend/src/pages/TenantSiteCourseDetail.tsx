import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Lock, PlayCircle, X } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import LessonContent from "@/components/courses/LessonContent";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { getPublicCourse, getPublicLessonPreview } from "@/services/courses";
import type { PortalLesson, PublicCourse } from "@/types/courses";
import { COURSE_LEVELS, LESSON_TYPE_LABELS } from "@/types/courses";
import { buildAssocieSeCtaLink, buildTenantSiteQuery, formatCatalogPrice } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

export default function TenantSiteCourseDetail() {
  const { slug = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [course, setCourse] = useState<PublicCourse | null>(null);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<PortalLesson | null>(null);
  const q = buildTenantSiteQuery(schema);

  useEffect(() => {
    setError("");
    getPublicCourse(schema, slug)
      .then(setCourse)
      .catch(() => setError("Curso não encontrado."));
  }, [schema, slug]);

  const openPreview = async (lessonId: string) => {
    try {
      setPreview(await getPublicLessonPreview(schema, slug, lessonId));
    } catch {
      setPreview(null);
    }
  };

  if (shellError || error) return <div className="tenant-site-empty">{error || "Site não encontrado."}</div>;
  if (!payload || !course) return <div className="tenant-site-empty">Carregando…</div>;

  const totalHoras = course.workload_hours
    ? `${course.workload_hours} h`
    : course.total_duration_minutes
      ? `${Math.round(course.total_duration_minutes / 60)} h de conteúdo`
      : null;
  const level = COURSE_LEVELS.find((l) => l.value === course.level)?.label;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section">
        <p>
          <Link to={`/site/cursos${q}`}>← Todos os cursos</Link>
        </p>

        <div className="course-player" style={{ gridTemplateColumns: "1fr 320px" }}>
          <div>
            <h1 style={{ marginTop: 0 }}>{course.title}</h1>
            {course.short_description && <p style={{ color: "var(--ts-muted)" }}>{course.short_description}</p>}
            <p className="course-muted">
              {[
                course.instructor_name && `Instrutor(a): ${course.instructor_name}`,
                level,
                `${course.lessons_count} aulas`,
                totalHoras,
                course.certificate_enabled && "Certificado de conclusão",
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
            {course.description && (
              <div className="course-prose" dangerouslySetInnerHTML={{ __html: course.description }} />
            )}

            <h2 style={{ marginTop: "2rem" }}>Conteúdo</h2>
            {course.sections?.map((section) => (
              <div key={section.id} className="course-section-card">
                <div className="course-section-header">{section.title}</div>
                {section.lessons.map((lesson) => (
                  <div key={lesson.id} className="course-lesson-row">
                    {lesson.is_preview ? <PlayCircle size={15} /> : <Lock size={15} color="#a0a0a0" />}
                    {lesson.is_preview ? (
                      <button type="button" className="course-lesson-title" onClick={() => openPreview(lesson.id)}>
                        {lesson.title} <span className="course-muted">(amostra grátis)</span>
                      </button>
                    ) : (
                      <span style={{ flex: 1 }}>{lesson.title}</span>
                    )}
                    <span className="course-muted">
                      {LESSON_TYPE_LABELS[lesson.lesson_type]}
                      {lesson.duration_minutes ? ` · ${lesson.duration_minutes} min` : ""}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>

          <aside className="course-card" style={{ position: "sticky", top: "1rem" }}>
            <div
              className="course-card-cover"
              style={{ backgroundImage: course.cover_image_url ? `url(${course.cover_image_url})` : undefined }}
            />
            <div className="course-card-body">
              <strong style={{ fontSize: "1.4rem" }}>
                {course.catalog_item_info
                  ? Number(course.catalog_item_info.price) > 0
                    ? formatCatalogPrice(course.catalog_item_info)
                    : "Gratuito"
                  : "Exclusivo para associados"}
              </strong>
              <a className="tenant-site-btn" href={buildAssocieSeCtaLink(schema)}>
                {course.catalog_item_info ? "Entrar e matricular-se" : "Área do associado"}
              </a>
              <span className="course-muted">
                Faça login na área do associado; o curso fica disponível na loja e, após a confirmação do
                pagamento, em “Meus cursos”.
              </span>
            </div>
          </aside>
        </div>
      </section>

      {preview && (
        <div className="dashboard-modal-overlay" onClick={() => setPreview(null)}>
          <div className="dashboard-modal course-modal-wide" onClick={(e) => e.stopPropagation()}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">{preview.title}</h2>
              <button type="button" className="dashboard-modal-close" onClick={() => setPreview(null)} aria-label="Fechar">
                <X size={18} />
              </button>
            </div>
            <div className="dashboard-modal-content">
              <LessonContent lesson={preview} />
            </div>
          </div>
        </div>
      )}
    </SiteShell>
  );
}
