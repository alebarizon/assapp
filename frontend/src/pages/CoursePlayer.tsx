import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Award, CheckCircle2, ChevronLeft, ChevronRight, Circle, Lock } from "lucide-react";
import LessonContent from "@/components/courses/LessonContent";
import LessonDiscussion from "@/components/courses/LessonDiscussion";
import LessonQuiz from "@/components/courses/LessonQuiz";
import {
  apiErrorMessage,
  completeMyLesson,
  downloadMyCertificate,
  getMyCourse,
  getMyLesson,
  submitMyQuiz,
} from "@/services/courses";
import type { PortalEnrollment, PortalLesson } from "@/types/courses";
import "@/components/courses/Courses.css";

export default function CoursePlayer() {
  const { enrollmentId = "", lessonId = "" } = useParams();
  const navigate = useNavigate();
  const [enrollment, setEnrollment] = useState<PortalEnrollment | null>(null);
  const [lesson, setLesson] = useState<PortalLesson | null>(null);
  const [erro, setErro] = useState("");
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    getMyCourse(enrollmentId)
      .then(setEnrollment)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar o curso.")));
  }, [enrollmentId]);

  useEffect(() => {
    setLesson(null);
    setErro("");
    getMyLesson(enrollmentId, lessonId)
      .then(setLesson)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar a aula.")));
    window.scrollTo(0, 0);
  }, [enrollmentId, lessonId]);

  const goTo = (id: string | null | undefined) => {
    if (id) navigate(`/app/portal/cursos/${enrollmentId}/lessons/${id}`);
  };

  const concluir = async () => {
    if (!lesson) return;
    setCompleting(true);
    try {
      const result = await completeMyLesson(enrollmentId, lesson.id);
      setLesson(result.lesson);
      setEnrollment(result.enrollment);
      if (result.lesson.next_lesson_id) goTo(result.lesson.next_lesson_id);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao concluir a aula."));
    } finally {
      setCompleting(false);
    }
  };

  const enviarQuiz = async (answers: Record<string, string[]>) => {
    if (!lesson) return;
    try {
      const result = await submitMyQuiz(enrollmentId, lesson.id, answers);
      setLesson(result.lesson);
      setEnrollment(result.enrollment);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar o quiz."));
    }
  };

  const baixarCertificado = async () => {
    if (!enrollment) return;
    try {
      await downloadMyCertificate(enrollment.id, enrollment.course.slug);
    } catch (err) {
      setErro(apiErrorMessage(err, "Certificado indisponível."));
    }
  };

  return (
    <div className="dashboard-page">
      <Link to="/app/portal/cursos" className="course-muted" style={{ display: "inline-flex", gap: "0.25rem" }}>
        <ArrowLeft size={14} /> Meus cursos
      </Link>

      {enrollment && (
        <div className="dashboard-header dashboard-header-row" style={{ marginTop: "0.5rem" }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <h1 className="dashboard-title">{enrollment.course.title}</h1>
            <div className="course-progress" style={{ maxWidth: 360 }}>
              <div
                className="course-progress-bar"
                style={{ width: `${enrollment.progress.percent_complete}%` }}
              />
            </div>
            <span className="course-muted">
              {enrollment.progress.completed_lessons} de {enrollment.progress.total_lessons} aulas concluídas
            </span>
          </div>
          {enrollment.certificate_available && (
            <div className="dashboard-header-actions">
              <button type="button" className="dashboard-btn-new" onClick={baixarCertificado}>
                <Award size={16} /> Baixar certificado
              </button>
            </div>
          )}
        </div>
      )}

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      <div className="course-player">
        <aside className="course-outline">
          {enrollment?.course.sections?.map((section) => (
            <div key={section.id}>
              <div className="course-outline-section">{section.title}</div>
              {section.lessons.map((l) => (
                <button
                  key={l.id}
                  type="button"
                  className={`course-outline-lesson${l.id === lessonId ? " active" : ""}`}
                  disabled={l.locked}
                  title={l.locked ? "Conclua as aulas anteriores" : undefined}
                  onClick={() => goTo(l.id)}
                >
                  {l.completed ? (
                    <CheckCircle2 size={15} color="#027a48" />
                  ) : l.locked ? (
                    <Lock size={15} />
                  ) : (
                    <Circle size={15} />
                  )}
                  <span style={{ flex: 1 }}>{l.title}</span>
                  {l.duration_minutes ? <span className="course-muted">{l.duration_minutes} min</span> : null}
                </button>
              ))}
            </div>
          ))}
        </aside>

        <section className="page-form-container" style={{ marginBottom: 0 }}>
          {!lesson ? (
            !erro && (
              <div className="dashboard-loading">
                <div className="loading-spinner" />
              </div>
            )
          ) : (
            <>
              <h2 style={{ margin: "0 0 1rem", fontSize: "1.35rem" }}>{lesson.title}</h2>
              <LessonContent lesson={lesson} />

              {lesson.lesson_type === "quiz" ? (
                <LessonQuiz key={lesson.id} lesson={lesson} onSubmit={enviarQuiz} />
              ) : (
                <div style={{ marginTop: "1.5rem" }}>
                  {lesson.completed ? (
                    <span className="status-badge status-badge-ativo">
                      <CheckCircle2 size={13} /> Aula concluída
                    </span>
                  ) : (
                    <button type="button" className="dashboard-btn-new" disabled={completing} onClick={concluir}>
                      {completing ? "Salvando..." : "Marcar como concluída"}
                    </button>
                  )}
                </div>
              )}

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "1.5rem",
                  paddingTop: "1rem",
                  borderTop: "1px solid #efede7",
                }}
              >
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  disabled={!lesson.previous_lesson_id}
                  onClick={() => goTo(lesson.previous_lesson_id)}
                >
                  <ChevronLeft size={15} /> Anterior
                </button>
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  disabled={!lesson.next_lesson_id || (enrollment?.course.progression_mode === "sequential" && !lesson.completed)}
                  onClick={() => goTo(lesson.next_lesson_id)}
                >
                  Próxima <ChevronRight size={15} />
                </button>
              </div>

              <LessonDiscussion enrollmentId={enrollmentId} lessonId={lesson.id} />
            </>
          )}
        </section>
      </div>
    </div>
  );
}
