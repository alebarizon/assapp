import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Award } from "lucide-react";
import { apiErrorMessage, downloadMyCertificate, listMyCourses } from "@/services/courses";
import type { PortalEnrollment } from "@/types/courses";
import "@/components/courses/Courses.css";

function lessonLink(enrollment: PortalEnrollment): string | null {
  const lessonId = enrollment.last_lesson || enrollment.progress.next_lesson_id;
  return lessonId ? `/app/portal/cursos/${enrollment.id}/lessons/${lessonId}` : null;
}

export default function MeusCursos() {
  const [enrollments, setEnrollments] = useState<PortalEnrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    listMyCourses()
      .then(setEnrollments)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar seus cursos.")))
      .finally(() => setLoading(false));
  }, []);

  const baixarCertificado = async (enrollment: PortalEnrollment) => {
    try {
      await downloadMyCertificate(enrollment.id, enrollment.course.slug);
    } catch (err) {
      setErro(apiErrorMessage(err, "Certificado indisponível."));
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Meus cursos</h1>
        <p className="dashboard-subtitle">Continue de onde parou e baixe seus certificados</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : enrollments.length === 0 ? (
        <div className="dashboard-empty">
          Você ainda não está matriculado em nenhum curso. Veja os cursos disponíveis na{" "}
          <Link to="/app/portal/loja">loja</Link>.
        </div>
      ) : (
        <div className="course-card-grid">
          {enrollments.map((e) => {
            const link = lessonLink(e);
            const done = e.status === "completed";
            return (
              <div key={e.id} className="course-card">
                <div
                  className="course-card-cover"
                  style={{ backgroundImage: e.course.cover_image_url ? `url(${e.course.cover_image_url})` : undefined }}
                />
                <div className="course-card-body">
                  <h3 className="course-card-title">{e.course.title}</h3>
                  {e.course.instructor_name && <span className="course-muted">{e.course.instructor_name}</span>}
                  <div className="course-progress">
                    <div className="course-progress-bar" style={{ width: `${e.progress.percent_complete}%` }} />
                  </div>
                  <span className="course-muted">
                    {e.progress.completed_lessons} de {e.progress.total_lessons} aulas ·{" "}
                    {e.progress.percent_complete}%
                  </span>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "auto" }}>
                    {link && (
                      <Link to={link} className="dashboard-btn-new">
                        {done ? "Rever aulas" : e.progress.completed_lessons ? "Continuar" : "Começar"}
                      </Link>
                    )}
                    {e.certificate_available && (
                      <button type="button" className="dashboard-btn-secondary" onClick={() => baixarCertificado(e)}>
                        <Award size={15} /> Certificado
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
