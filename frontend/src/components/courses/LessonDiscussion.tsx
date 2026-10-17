import { useEffect, useState } from "react";
import {
  apiErrorMessage,
  askLessonQuestion,
  listLessonQuestions,
  replyLessonQuestion,
} from "@/services/courses";
import type { StudentQuestion } from "@/types/courses";

interface LessonDiscussionProps {
  enrollmentId: string;
  lessonId: string;
}

export default function LessonDiscussion({ enrollmentId, lessonId }: LessonDiscussionProps) {
  const [questions, setQuestions] = useState<StudentQuestion[]>([]);
  const [body, setBody] = useState("");
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const [erro, setErro] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    setQuestions([]);
    listLessonQuestions(enrollmentId, lessonId)
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [enrollmentId, lessonId]);

  const perguntar = async () => {
    if (!body.trim()) return;
    setSending(true);
    setErro("");
    try {
      const created = await askLessonQuestion(enrollmentId, lessonId, body.trim());
      setQuestions((prev) => [created, ...prev]);
      setBody("");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar a pergunta."));
    } finally {
      setSending(false);
    }
  };

  const responder = async (question: StudentQuestion) => {
    const text = (replyDrafts[question.id] || "").trim();
    if (!text) return;
    try {
      const updated = await replyLessonQuestion(enrollmentId, question.id, text);
      setQuestions((prev) => prev.map((q) => (q.id === updated.id ? updated : q)));
      setReplyDrafts((prev) => ({ ...prev, [question.id]: "" }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao responder."));
    }
  };

  return (
    <div style={{ marginTop: "2rem" }}>
      <h3 style={{ fontSize: "1.05rem", margin: "0 0 0.75rem" }}>Perguntas sobre a aula</h3>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      <div className="page-form" style={{ gap: "0.5rem", marginBottom: "1rem" }}>
        <textarea
          className="form-input"
          rows={3}
          placeholder="Tem alguma dúvida? Pergunte ao instrutor e aos colegas."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <div>
          <button type="button" className="dashboard-btn-new" disabled={!body.trim() || sending} onClick={perguntar}>
            {sending ? "Enviando..." : "Enviar pergunta"}
          </button>
        </div>
      </div>

      {questions.length === 0 && <p className="course-muted">Nenhuma pergunta ainda.</p>}
      {questions.map((q) => (
        <div key={q.id} className="course-qa-item">
          <div className="course-muted">
            {q.is_mine ? "Você" : q.author_name} · {new Date(q.created_at).toLocaleString("pt-BR")}
          </div>
          <p style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{q.body}</p>
          {q.replies.map((r) => (
            <div key={r.id} className={`course-qa-reply${r.is_instructor ? " instructor" : ""}`}>
              <div className="course-muted">
                {r.author_name}
                {r.is_instructor ? " (instrutor)" : ""}
              </div>
              <div style={{ whiteSpace: "pre-wrap" }}>{r.body}</div>
            </div>
          ))}
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }} className="page-form">
            <input
              className="form-input"
              placeholder="Responder..."
              value={replyDrafts[q.id] || ""}
              onChange={(e) => setReplyDrafts((prev) => ({ ...prev, [q.id]: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && responder(q)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
