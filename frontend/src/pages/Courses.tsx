import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Copy, GraduationCap, MessageCircle, Plus, Search, Trash2, Users } from "lucide-react";
import CourseSettingsForm from "@/components/courses/CourseSettingsForm";
import QuestionsInbox from "@/components/courses/QuestionsInbox";
import { apiErrorMessage, deleteCourse, duplicateCourse, listCourses } from "@/services/courses";
import type { CourseStatus, CourseSummary } from "@/types/courses";
import { COURSE_STATUS_BADGE } from "@/types/courses";
import { formatCatalogPrice } from "@/utils/tenantSite";
import "@/components/courses/Courses.css";

export default function Courses() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"cursos" | "perguntas">("cursos");
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [status, setStatus] = useState<CourseStatus | "">("");
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      setCourses(await listCourses({ search: busca || undefined, status: status || undefined }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar cursos."));
    } finally {
      setLoading(false);
    }
  }, [busca, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const pendentes = courses.reduce((acc, c) => acc + c.unanswered_questions_count, 0);

  const handleDuplicate = async (course: CourseSummary) => {
    try {
      const copy = await duplicateCourse(course.id);
      navigate(`/app/courses/${copy.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao duplicar."));
    }
  };

  const handleDelete = async (course: CourseSummary) => {
    const aviso = course.students_count
      ? `"${course.title}" tem ${course.students_count} aluno(s). Excluir mesmo assim? Prefira arquivar.`
      : `Excluir o curso "${course.title}"?`;
    if (!window.confirm(aviso)) return;
    try {
      await deleteCourse(course.id);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Cursos</h1>
          <p className="dashboard-subtitle">Cursos online com aulas, quizzes, certificados e venda pela loja</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
            <Plus size={16} /> Novo curso
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <button
          type="button"
          className={`dashboard-tab${tab === "cursos" ? " active" : ""}`}
          onClick={() => setTab("cursos")}
        >
          Cursos
        </button>
        <button
          type="button"
          className={`dashboard-tab${tab === "perguntas" ? " active" : ""}`}
          onClick={() => setTab("perguntas")}
        >
          Perguntas dos alunos{pendentes > 0 ? ` (${pendentes})` : ""}
        </button>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      {showForm && (
        <CourseSettingsForm course={null} onSaved={(created) => navigate(`/app/courses/${created.id}`)} />
      )}

      {tab === "perguntas" ? (
        <QuestionsInbox onChanged={load} />
      ) : (
        <>
          <div className="filters-row">
            <div style={{ position: "relative", flex: 1, minWidth: "12rem" }}>
              <Search
                size={16}
                style={{ position: "absolute", left: "0.75rem", top: "0.7rem", color: "#a0a0a0" }}
              />
              <input
                className="form-input"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar curso..."
                style={{ paddingLeft: "2.25rem", width: "100%" }}
              />
            </div>
            <select
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value as CourseStatus | "")}
            >
              <option value="">Todos os status</option>
              <option value="draft">Rascunho</option>
              <option value="published">Publicado</option>
              <option value="archived">Arquivado</option>
            </select>
          </div>

          {loading ? (
            <div className="dashboard-loading">
              <div className="loading-spinner" />
              <p>Carregando...</p>
            </div>
          ) : courses.length === 0 ? (
            <div className="dashboard-empty">Nenhum curso ainda. Clique em “Novo curso” para começar.</div>
          ) : (
            <div className="list-stack">
              {courses.map((c) => (
                <div key={c.id} className="list-card" style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                  <div
                    className="course-card-cover"
                    style={{
                      width: 120,
                      flexShrink: 0,
                      borderRadius: 8,
                      backgroundImage: c.cover_image_url ? `url(${c.cover_image_url})` : undefined,
                    }}
                  />
                  <Link to={`/app/courses/${c.id}`} style={{ flex: 1, color: "inherit", textDecoration: "none" }}>
                    <div className="list-card-title">{c.title}</div>
                    <div className="list-card-meta" style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                      <span>
                        <GraduationCap size={13} /> {c.lessons_count} aulas
                      </span>
                      <span>
                        <Users size={13} /> {c.students_count} alunos
                      </span>
                      {c.unanswered_questions_count > 0 && (
                        <span>
                          <MessageCircle size={13} /> {c.unanswered_questions_count} sem resposta
                        </span>
                      )}
                      <span>{c.catalog_item_info ? formatCatalogPrice(c.catalog_item_info) : "Sem item na loja"}</span>
                    </div>
                  </Link>
                  <span className={`status-badge status-badge-${COURSE_STATUS_BADGE[c.status]}`}>
                    {c.status_display}
                  </span>
                  <button
                    type="button"
                    className="course-icon-btn"
                    title="Duplicar"
                    onClick={() => handleDuplicate(c)}
                  >
                    <Copy size={16} />
                  </button>
                  <button type="button" className="course-icon-btn" title="Excluir" onClick={() => handleDelete(c)}>
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
