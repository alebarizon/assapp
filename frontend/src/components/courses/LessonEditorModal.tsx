import { useEffect, useState } from "react";
import { FileText, Plus, Trash2, Upload, X } from "lucide-react";
import RichTextEditor from "./RichTextEditor";
import {
  apiErrorMessage,
  createLesson,
  deleteAttachment,
  updateLesson,
  uploadAttachment,
} from "@/services/courses";
import type {
  Lesson,
  LessonAttachment,
  LessonPayload,
  LessonType,
  QuestionType,
  QuizQuestion,
} from "@/types/courses";

interface LessonEditorModalProps {
  sectionId: string;
  lesson: Lesson | null;
  onClose: () => void;
  onSaved: () => void;
}

const TRUE_FALSE = () => [
  { text: "Verdadeiro", is_correct: true },
  { text: "Falso", is_correct: false },
];

export default function LessonEditorModal({ sectionId, lesson, onClose, onSaved }: LessonEditorModalProps) {
  const [current, setCurrent] = useState<Lesson | null>(lesson);
  const [title, setTitle] = useState(lesson?.title || "");
  const [lessonType, setLessonType] = useState<LessonType>(lesson?.lesson_type || "text");
  const [content, setContent] = useState(lesson?.content || "");
  const [videoUrl, setVideoUrl] = useState(lesson?.video_url || "");
  const [duration, setDuration] = useState(lesson?.duration_minutes ? String(lesson.duration_minutes) : "");
  const [isPreview, setIsPreview] = useState(lesson?.is_preview || false);
  const [questions, setQuestions] = useState<QuizQuestion[]>(
    lesson?.questions ? JSON.parse(JSON.stringify(lesson.questions)) : []
  );
  const [attachments, setAttachments] = useState<LessonAttachment[]>(lesson?.attachments || []);
  const [attachmentTitle, setAttachmentTitle] = useState("");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const updateQuestion = (index: number, patch: Partial<QuizQuestion>) => {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  };

  const changeQuestionType = (index: number, type: QuestionType) => {
    const question = questions[index];
    if (type === "true_false") {
      updateQuestion(index, { question_type: type, options: TRUE_FALSE() });
      return;
    }
    let options = question.options;
    if (type === "single") {
      let found = false;
      options = options.map((o) => {
        const keep = !!o.is_correct && !found;
        if (keep) found = true;
        return { ...o, is_correct: keep };
      });
    }
    updateQuestion(index, { question_type: type, options });
  };

  const toggleCorrect = (qIndex: number, oIndex: number) => {
    const question = questions[qIndex];
    const options = question.options.map((o, i) => {
      if (question.question_type === "multiple") return i === oIndex ? { ...o, is_correct: !o.is_correct } : o;
      return { ...o, is_correct: i === oIndex };
    });
    updateQuestion(qIndex, { options });
  };

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      {
        prompt: "",
        question_type: "single",
        explanation: "",
        options: [
          { text: "", is_correct: true },
          { text: "", is_correct: false },
        ],
      },
    ]);
  };

  const handleSave = async () => {
    setErro("");
    if (!title.trim()) {
      setErro("Informe o título da aula.");
      return;
    }
    if (lessonType === "quiz" && questions.length === 0) {
      setErro("Adicione ao menos uma questão ao quiz.");
      return;
    }
    const payload: LessonPayload = {
      title: title.trim(),
      lesson_type: lessonType,
      content,
      video_url: lessonType === "video" ? videoUrl.trim() : "",
      duration_minutes: duration ? Number(duration) : null,
      is_preview: lessonType === "quiz" ? false : isPreview,
    };
    if (lessonType === "quiz") {
      payload.questions = questions.map((q) => ({ ...q, options: q.options.filter((o) => o.text.trim()) }));
    } else if (current?.questions?.length) {
      payload.questions = [];
    }
    setSaving(true);
    try {
      if (current) {
        await updateLesson(current.id, payload);
        onSaved();
        onClose();
      } else {
        // Mantém o modal aberto para permitir anexar arquivos à aula recém-criada.
        const created = await createLesson({ ...payload, section: sectionId });
        setCurrent(created);
        setQuestions(created.questions || []);
        onSaved();
      }
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar a aula."));
    } finally {
      setSaving(false);
    }
  };

  const handleUpload = async () => {
    if (!current || !attachmentFile) return;
    setUploading(true);
    setErro("");
    try {
      const created = await uploadAttachment(current.id, attachmentFile, attachmentTitle.trim() || attachmentFile.name);
      setAttachments((prev) => [...prev, created]);
      setAttachmentFile(null);
      setAttachmentTitle("");
      onSaved();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar o anexo."));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAttachment = async (attachment: LessonAttachment) => {
    try {
      await deleteAttachment(attachment.id);
      setAttachments((prev) => prev.filter((a) => a.id !== attachment.id));
      onSaved();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao remover o anexo."));
    }
  };

  return (
    <div className="dashboard-modal-overlay" onClick={onClose}>
      <div className="dashboard-modal course-modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="dashboard-modal-header">
          <h2 className="dashboard-modal-title">{current ? "Editar aula" : "Nova aula"}</h2>
          <button type="button" className="dashboard-modal-close" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <div className="dashboard-modal-content page-form">
          {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

          <div className="form-row-2">
            <div className="form-group">
              <label className="form-label">Título *</label>
              <input className="form-input" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Tipo</label>
              <select
                className="form-select"
                value={lessonType}
                onChange={(e) => setLessonType(e.target.value as LessonType)}
              >
                <option value="text">Texto</option>
                <option value="video">Vídeo (YouTube)</option>
                <option value="quiz">Quiz</option>
              </select>
            </div>
          </div>

          {lessonType === "video" && (
            <div className="form-group">
              <label className="form-label">Link do vídeo no YouTube *</label>
              <input
                className="form-input"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
              />
              <p className="course-muted">Vídeos não listados também funcionam.</p>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">{lessonType === "quiz" ? "Instruções do quiz" : "Conteúdo"}</label>
            <RichTextEditor value={content} onChange={setContent} onUploadError={setErro} />
          </div>

          <div className="form-row-2">
            <div className="form-group">
              <label className="form-label">Duração (minutos)</label>
              <input
                className="form-input"
                type="number"
                min="0"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
            {lessonType !== "quiz" && (
              <div className="form-group" style={{ display: "flex", alignItems: "flex-end" }}>
                <label className="inline-check">
                  <input type="checkbox" checked={isPreview} onChange={(e) => setIsPreview(e.target.checked)} />
                  <span>Aula de amostra (aberta no site, sem matrícula)</span>
                </label>
              </div>
            )}
          </div>

          {lessonType === "quiz" && (
            <div className="form-group">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label className="form-label" style={{ margin: 0 }}>
                  Questões
                </label>
                <button type="button" className="dashboard-btn-secondary" onClick={addQuestion}>
                  <Plus size={14} /> Adicionar questão
                </button>
              </div>
              {questions.length === 0 && <p className="course-muted">Nenhuma questão ainda.</p>}
              {questions.map((question, qIndex) => (
                <div key={question.id || `new-${qIndex}`} className="course-quiz-question" style={{ marginTop: "0.75rem" }}>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
                    <strong style={{ paddingTop: "0.5rem" }}>{qIndex + 1}.</strong>
                    <textarea
                      className="form-input"
                      rows={2}
                      value={question.prompt}
                      placeholder="Enunciado"
                      onChange={(e) => updateQuestion(qIndex, { prompt: e.target.value })}
                    />
                    <button
                      type="button"
                      className="course-icon-btn"
                      aria-label="Remover questão"
                      onClick={() => setQuestions((prev) => prev.filter((_, i) => i !== qIndex))}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <select
                    className="form-select"
                    style={{ margin: "0.5rem 0", maxWidth: 260 }}
                    value={question.question_type}
                    onChange={(e) => changeQuestionType(qIndex, e.target.value as QuestionType)}
                  >
                    <option value="single">Escolha única</option>
                    <option value="multiple">Múltipla escolha</option>
                    <option value="true_false">Verdadeiro / Falso</option>
                  </select>
                  <p className="course-muted">Marque a(s) alternativa(s) correta(s).</p>
                  {question.options.map((option, oIndex) => (
                    <div key={option.id || `opt-${oIndex}`} className="course-quiz-option">
                      <input
                        type={question.question_type === "multiple" ? "checkbox" : "radio"}
                        name={`q-${qIndex}`}
                        checked={!!option.is_correct}
                        onChange={() => toggleCorrect(qIndex, oIndex)}
                      />
                      <input
                        className="form-input"
                        value={option.text}
                        disabled={question.question_type === "true_false"}
                        placeholder={`Alternativa ${oIndex + 1}`}
                        onChange={(e) =>
                          updateQuestion(qIndex, {
                            options: question.options.map((o, i) =>
                              i === oIndex ? { ...o, text: e.target.value } : o
                            ),
                          })
                        }
                      />
                      {question.question_type !== "true_false" && question.options.length > 2 && (
                        <button
                          type="button"
                          className="course-icon-btn"
                          aria-label="Remover alternativa"
                          onClick={() =>
                            updateQuestion(qIndex, { options: question.options.filter((_, i) => i !== oIndex) })
                          }
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                  {question.question_type !== "true_false" && (
                    <button
                      type="button"
                      className="dashboard-btn-secondary"
                      style={{ marginTop: "0.25rem" }}
                      onClick={() =>
                        updateQuestion(qIndex, { options: [...question.options, { text: "", is_correct: false }] })
                      }
                    >
                      <Plus size={14} /> Alternativa
                    </button>
                  )}
                  <textarea
                    className="form-input"
                    rows={2}
                    style={{ marginTop: "0.5rem" }}
                    value={question.explanation || ""}
                    placeholder="Explicação exibida após a resposta (opcional)"
                    onChange={(e) => updateQuestion(qIndex, { explanation: e.target.value })}
                  />
                </div>
              ))}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Anexos</label>
            {!current ? (
              <p className="course-muted">Salve a aula para anexar materiais (até 20 MB por arquivo).</p>
            ) : (
              <>
                {attachments.map((attachment) => (
                  <div key={attachment.id} className="course-lesson-row" style={{ padding: "0.4rem 0" }}>
                    <FileText size={15} />
                    <a href={attachment.file_url || "#"} target="_blank" rel="noopener noreferrer" style={{ flex: 1 }}>
                      {attachment.title}
                    </a>
                    <span className="course-muted">{attachment.file_type.toUpperCase()}</span>
                    <button
                      type="button"
                      className="course-icon-btn"
                      aria-label="Remover anexo"
                      onClick={() => handleDeleteAttachment(attachment)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                  <input
                    className="form-input"
                    style={{ flex: 1, minWidth: 160 }}
                    value={attachmentTitle}
                    placeholder="Título do anexo"
                    onChange={(e) => setAttachmentTitle(e.target.value)}
                  />
                  <input type="file" onChange={(e) => setAttachmentFile(e.target.files?.[0] || null)} />
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    disabled={!attachmentFile || uploading}
                    onClick={handleUpload}
                  >
                    <Upload size={14} /> {uploading ? "Enviando..." : "Enviar"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="dashboard-modal-footer">
          <button type="button" className="dashboard-btn-secondary" onClick={onClose}>
            Fechar
          </button>
          <button type="button" className="dashboard-btn-new" disabled={saving} onClick={handleSave}>
            {saving ? "Salvando..." : "Salvar aula"}
          </button>
        </div>
      </div>
    </div>
  );
}
