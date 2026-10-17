import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertCircle, ArrowDown, ArrowLeft, ArrowUp, Eye, Pencil, Plus, Trash2 } from "lucide-react";
import CourseSettingsForm from "@/components/courses/CourseSettingsForm";
import CourseStudents from "@/components/courses/CourseStudents";
import LessonEditorModal from "@/components/courses/LessonEditorModal";
import QuestionsInbox from "@/components/courses/QuestionsInbox";
import {
  apiErrorMessage,
  createSection,
  deleteLesson,
  deleteSection,
  getCourse,
  reorderCourse,
  updateCourse,
  updateSection,
} from "@/services/courses";
import { useAuth } from "@/contexts/AuthContext";
import type { Course, CourseStatus, Lesson } from "@/types/courses";
import { COURSE_STATUS_BADGE, LESSON_TYPE_LABELS } from "@/types/courses";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/courses/Courses.css";

type Tab = "conteudo" | "config" | "alunos" | "perguntas";

export default function CourseDetail() {
  const { id = "" } = useParams();
  const { tenantSchema } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [tab, setTab] = useState<Tab>("conteudo");
  const [erro, setErro] = useState("");
  const [novaSecao, setNovaSecao] = useState("");
  const [editor, setEditor] = useState<{ sectionId: string; lesson: Lesson | null } | null>(null);

  const load = useCallback(async () => {
    try {
      setCourse(await getCourse(id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar o curso."));
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!course) {
    return (
      <div className="dashboard-page">
        {erro ? (
          <div className="alert-banner alert-banner-error">{erro}</div>
        ) : (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
            <p>Carregando...</p>
          </div>
        )}
      </div>
    );
  }

  const totalLessons = course.sections.reduce((acc, s) => acc + s.lessons.length, 0);

  const changeStatus = async (status: CourseStatus) => {
    setErro("");
    if (status === "published" && totalLessons === 0) {
      setErro("Adicione ao menos uma aula antes de publicar.");
      return;
    }
    try {
      setCourse(await updateCourse(course.id, { status }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao alterar o status."));
    }
  };

  const addSection = async () => {
    if (!novaSecao.trim()) return;
    try {
      await createSection(course.id, novaSecao.trim());
      setNovaSecao("");
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar o módulo."));
    }
  };

  const renameSection = async (sectionId: string, current: string) => {
    const title = window.prompt("Nome do módulo", current);
    if (!title || title.trim() === current) return;
    try {
      await updateSection(sectionId, title.trim());
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao renomear."));
    }
  };

  const removeSection = async (sectionId: string, title: string) => {
    if (!window.confirm(`Excluir o módulo "${title}" e todas as suas aulas?`)) return;
    try {
      await deleteSection(sectionId);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir o módulo."));
    }
  };

  const removeLesson = async (lesson: Lesson) => {
    if (!window.confirm(`Excluir a aula "${lesson.title}"?`)) return;
    try {
      await deleteLesson(lesson.id);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir a aula."));
    }
  };

  const persistOrder = async (sections: Course["sections"]) => {
    try {
      setCourse(
        await reorderCourse(
          course.id,
          sections.map((s) => ({ id: s.id, lesson_ids: s.lessons.map((l) => l.id) }))
        )
      );
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao reordenar."));
    }
  };

  const moveSection = (index: number, delta: number) => {
    const sections = [...course.sections];
    const target = index + delta;
    if (target < 0 || target >= sections.length) return;
    [sections[index], sections[target]] = [sections[target], sections[index]];
    void persistOrder(sections);
  };

  const moveLesson = (sectionIndex: number, lessonIndex: number, delta: number) => {
    const sections = course.sections.map((s) => ({ ...s, lessons: [...s.lessons] }));
    const lessons = sections[sectionIndex].lessons;
    const target = lessonIndex + delta;
    if (target < 0 || target >= lessons.length) return;
    [lessons[lessonIndex], lessons[target]] = [lessons[target], lessons[lessonIndex]];
    void persistOrder(sections);
  };

  const siteUrl = `/site/cursos/${course.slug}${buildTenantSiteQuery(tenantSchema || "")}`;

  return (
    <div className="dashboard-page">
      <Link to="/app/courses" className="course-muted" style={{ display: "inline-flex", gap: "0.25rem" }}>
        <ArrowLeft size={14} /> Cursos
      </Link>

      <div className="dashboard-header dashboard-header-row" style={{ marginTop: "0.5rem" }}>
        <div>
          <h1 className="dashboard-title">
            {course.title}{" "}
            <span className={`status-badge status-badge-${COURSE_STATUS_BADGE[course.status]}`}>
              {course.status_display}
            </span>
          </h1>
          <p className="dashboard-subtitle">
            {totalLessons} aulas ·{" "}
            {course.catalog_item_info ? `Vendido na loja: ${course.catalog_item_info.name}` : "Sem item na loja"}
          </p>
        </div>
        <div className="dashboard-header-actions">
          {course.status === "published" && (
            <a href={siteUrl} target="_blank" rel="noopener noreferrer" className="dashboard-btn-secondary">
              <Eye size={16} /> Ver no site
            </a>
          )}
          {course.status !== "published" && (
            <button type="button" className="dashboard-btn-new" onClick={() => changeStatus("published")}>
              Publicar
            </button>
          )}
          {course.status === "published" && (
            <button type="button" className="dashboard-btn-secondary" onClick={() => changeStatus("draft")}>
              Voltar a rascunho
            </button>
          )}
          {course.status !== "archived" && (
            <button type="button" className="dashboard-btn-secondary" onClick={() => changeStatus("archived")}>
              Arquivar
            </button>
          )}
        </div>
      </div>

      {course.status === "published" && !course.catalog_item && (
        <div className="highlight-banner" style={{ marginBottom: "1rem" }}>
          <div className="highlight-banner-label">Atenção</div>
          <div className="highlight-banner-meta">
            O curso está publicado mas não tem item na loja: os associados só entram por matrícula manual.
            Vincule ou crie um item em Configurações.
          </div>
        </div>
      )}

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      <div className="dashboard-tabs">
        {(
          [
            ["conteudo", "Conteúdo"],
            ["config", "Configurações"],
            ["alunos", "Alunos"],
            ["perguntas", "Perguntas"],
          ] as [Tab, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`dashboard-tab${tab === key ? " active" : ""}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "conteudo" && (
        <div>
          {course.sections.length === 0 && (
            <div className="dashboard-empty" style={{ marginBottom: "1rem" }}>
              Comece criando um módulo (ex.: “Introdução”) e adicione aulas a ele.
            </div>
          )}
          {course.sections.map((section, sIndex) => (
            <div key={section.id} className="course-section-card">
              <div className="course-section-header">
                <span className="course-section-title">
                  {sIndex + 1}. {section.title}
                </span>
                <button
                  type="button"
                  className="course-icon-btn"
                  title="Subir"
                  disabled={sIndex === 0}
                  onClick={() => moveSection(sIndex, -1)}
                >
                  <ArrowUp size={15} />
                </button>
                <button
                  type="button"
                  className="course-icon-btn"
                  title="Descer"
                  disabled={sIndex === course.sections.length - 1}
                  onClick={() => moveSection(sIndex, 1)}
                >
                  <ArrowDown size={15} />
                </button>
                <button
                  type="button"
                  className="course-icon-btn"
                  title="Renomear"
                  onClick={() => renameSection(section.id, section.title)}
                >
                  <Pencil size={15} />
                </button>
                <button
                  type="button"
                  className="course-icon-btn"
                  title="Excluir módulo"
                  onClick={() => removeSection(section.id, section.title)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
              {section.lessons.map((lesson, lIndex) => (
                <div key={lesson.id} className="course-lesson-row">
                  <button
                    type="button"
                    className="course-lesson-title"
                    onClick={() => setEditor({ sectionId: section.id, lesson })}
                  >
                    {lesson.title}
                  </button>
                  <span className="course-muted">
                    {LESSON_TYPE_LABELS[lesson.lesson_type]}
                    {lesson.duration_minutes ? ` · ${lesson.duration_minutes} min` : ""}
                    {lesson.is_preview ? " · amostra" : ""}
                  </span>
                  <button
                    type="button"
                    className="course-icon-btn"
                    title="Subir"
                    disabled={lIndex === 0}
                    onClick={() => moveLesson(sIndex, lIndex, -1)}
                  >
                    <ArrowUp size={14} />
                  </button>
                  <button
                    type="button"
                    className="course-icon-btn"
                    title="Descer"
                    disabled={lIndex === section.lessons.length - 1}
                    onClick={() => moveLesson(sIndex, lIndex, 1)}
                  >
                    <ArrowDown size={14} />
                  </button>
                  <button
                    type="button"
                    className="course-icon-btn"
                    title="Excluir aula"
                    onClick={() => removeLesson(lesson)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              <div className="course-lesson-row">
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  onClick={() => setEditor({ sectionId: section.id, lesson: null })}
                >
                  <Plus size={14} /> Nova aula
                </button>
              </div>
            </div>
          ))}

          <div className="page-form" style={{ flexDirection: "row", gap: "0.5rem" }}>
            <input
              className="form-input"
              value={novaSecao}
              placeholder="Nome do novo módulo"
              onChange={(e) => setNovaSecao(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSection()}
            />
            <button type="button" className="dashboard-btn-secondary" onClick={addSection}>
              <Plus size={14} /> Adicionar módulo
            </button>
          </div>
        </div>
      )}

      {tab === "config" && <CourseSettingsForm key={course.id} course={course} onSaved={setCourse} />}
      {tab === "alunos" && <CourseStudents courseId={course.id} />}
      {tab === "perguntas" && <QuestionsInbox courseId={course.id} />}

      {editor && (
        <LessonEditorModal
          sectionId={editor.sectionId}
          lesson={editor.lesson}
          onClose={() => setEditor(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}
