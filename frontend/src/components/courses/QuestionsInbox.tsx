import { useCallback, useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import {
  apiErrorMessage,
  deleteInstructorQuestion,
  listInstructorQuestions,
  replyInstructorQuestion,
} from "@/services/courses";
import type { StudentQuestion } from "@/types/courses";

interface QuestionsInboxProps {
  courseId?: string;
  onChanged?: () => void;
}

export default function QuestionsInbox({ courseId, onChanged }: QuestionsInboxProps) {
  const [filtro, setFiltro] = useState<"false" | "true" | "">("false");
  const [questions, setQuestions] = useState<StudentQuestion[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setQuestions(
        await listInstructorQuestions({ course: courseId, answered: filtro || undefined })
      );
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar perguntas."));
    } finally {
      setLoading(false);
    }
  }, [courseId, filtro]);

  useEffect(() => {
    load();
  }, [load]);

  const responder = async (question: StudentQuestion) => {
    const body = (drafts[question.id] || "").trim();
    if (!body) return;
    try {
      const updated = await replyInstructorQuestion(question.id, body);
      setDrafts((prev) => ({ ...prev, [question.id]: "" }));
      setQuestions((prev) =>
        filtro === "false" ? prev.filter((q) => q.id !== updated.id) : prev.map((q) => (q.id === updated.id ? updated : q))
      );
      onChanged?.();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao responder."));
    }
  };

  const excluir = async (question: StudentQuestion) => {
    if (!window.confirm("Excluir esta pergunta e as respostas?")) return;
    try {
      await deleteInstructorQuestion(question.id);
      setQuestions((prev) => prev.filter((q) => q.id !== question.id));
      onChanged?.();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
  };

  return (
    <div>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      <div className="filters-row">
        <select className="form-select" value={filtro} onChange={(e) => setFiltro(e.target.value as typeof filtro)}>
          <option value="false">Sem resposta</option>
          <option value="true">Respondidas</option>
          <option value="">Todas</option>
        </select>
      </div>

      {loading ? (
        <div className="dashboard-loading">Carregando...</div>
      ) : questions.length === 0 ? (
        <div className="dashboard-empty">Nenhuma pergunta encontrada.</div>
      ) : (
        questions.map((q) => (
          <div key={q.id} className="course-qa-item">
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div className="course-muted">
                  {!courseId && <>{q.course_title} · </>}
                  {q.lesson_title} · {q.author_name} · {new Date(q.created_at).toLocaleString("pt-BR")}
                </div>
                <p style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{q.body}</p>
              </div>
              <button type="button" className="course-icon-btn" aria-label="Excluir" onClick={() => excluir(q)}>
                <Trash2 size={15} />
              </button>
            </div>
            {q.replies.map((r) => (
              <div key={r.id} className={`course-qa-reply${r.is_instructor ? " instructor" : ""}`}>
                <div className="course-muted">
                  {r.author_name}
                  {r.is_instructor ? " (instrutor)" : ""} · {new Date(r.created_at).toLocaleString("pt-BR")}
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{r.body}</div>
              </div>
            ))}
            <div className="page-form" style={{ marginTop: "0.75rem", gap: "0.5rem" }}>
              <textarea
                className="form-input"
                rows={2}
                placeholder="Escreva uma resposta..."
                value={drafts[q.id] || ""}
                onChange={(e) => setDrafts((prev) => ({ ...prev, [q.id]: e.target.value }))}
              />
              <div>
                <button
                  type="button"
                  className="dashboard-btn-new"
                  disabled={!(drafts[q.id] || "").trim()}
                  onClick={() => responder(q)}
                >
                  Responder
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
