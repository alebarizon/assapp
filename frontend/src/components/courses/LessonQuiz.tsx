import { useState } from "react";
import type { PortalLesson } from "@/types/courses";

interface LessonQuizProps {
  lesson: PortalLesson;
  onSubmit: (answers: Record<string, string[]>) => Promise<void>;
}

export default function LessonQuiz({ lesson, onSubmit }: LessonQuizProps) {
  const attempt = lesson.last_attempt;
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [retrying, setRetrying] = useState(!attempt);
  const [sending, setSending] = useState(false);
  const questions = lesson.questions || [];
  const showResult = !!attempt && !retrying;
  const resultFor = (questionId: string) => attempt?.results.find((r) => r.question_id === questionId);

  const toggle = (questionId: string, optionId: string, multiple: boolean) => {
    setAnswers((prev) => {
      const current = prev[questionId] || [];
      if (!multiple) return { ...prev, [questionId]: [optionId] };
      return {
        ...prev,
        [questionId]: current.includes(optionId) ? current.filter((id) => id !== optionId) : [...current, optionId],
      };
    });
  };

  const allAnswered = questions.every((q) => (answers[q.id] || []).length > 0);

  const handleSubmit = async () => {
    setSending(true);
    try {
      await onSubmit(answers);
      setRetrying(false);
      setAnswers({});
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ marginTop: "1.25rem" }}>
      {showResult && attempt && (
        <div className="alert-banner alert-banner-success">
          Quiz concluído — você acertou {attempt.correct_count} de {attempt.total_count} (
          {Math.round(attempt.score_percent)}%). Você pode refazê-lo quando quiser.
        </div>
      )}

      {questions.map((q, index) => {
        const result = showResult ? resultFor(q.id) : undefined;
        const multiple = q.question_type === "multiple";
        return (
          <div key={q.id} className="course-quiz-question">
            <strong>
              {index + 1}. {q.prompt}
            </strong>
            {multiple && <div className="course-muted">Marque todas as corretas.</div>}
            {q.options.map((o) => {
              const selected = result
                ? result.selected_option_ids.includes(o.id)
                : (answers[q.id] || []).includes(o.id);
              let cls = "course-quiz-option";
              if (result && result.correct_option_ids.includes(o.id)) cls += " correct";
              else if (result && selected) cls += " wrong";
              return (
                <label key={o.id} className={cls}>
                  <input
                    type={multiple ? "checkbox" : "radio"}
                    name={`quiz-${q.id}`}
                    checked={selected}
                    disabled={showResult}
                    onChange={() => toggle(q.id, o.id, multiple)}
                  />
                  {o.text}
                </label>
              );
            })}
            {result?.explanation && <p className="course-muted">{result.explanation}</p>}
          </div>
        );
      })}

      {showResult ? (
        <button type="button" className="dashboard-btn-secondary" onClick={() => setRetrying(true)}>
          Refazer quiz
        </button>
      ) : (
        <button
          type="button"
          className="dashboard-btn-new"
          disabled={!allAnswered || sending}
          onClick={handleSubmit}
        >
          {sending ? "Enviando..." : "Enviar respostas"}
        </button>
      )}
    </div>
  );
}
