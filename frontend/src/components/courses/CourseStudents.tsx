import { useCallback, useEffect, useState } from "react";
import { listMembros } from "@/services/membros";
import { apiErrorMessage, enrollStudent, listStudents, setStudentStatus } from "@/services/courses";
import type { Membro } from "@/types/membros";
import type { StudentEnrollment } from "@/types/courses";
import { ENROLLMENT_STATUS_BADGE } from "@/types/courses";

interface CourseStudentsProps {
  courseId: string;
}

const formatDate = (value: string | null) => (value ? new Date(value).toLocaleDateString("pt-BR") : "—");

export default function CourseStudents({ courseId }: CourseStudentsProps) {
  const [students, setStudents] = useState<StudentEnrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [resultados, setResultados] = useState<Membro[]>([]);
  const [buscando, setBuscando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setStudents(await listStudents(courseId));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar alunos."));
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    load();
  }, [load]);

  const buscarMembros = async () => {
    if (!busca.trim()) return;
    setBuscando(true);
    try {
      const enrolled = new Set(students.map((s) => s.membro));
      const found = await listMembros({ q: busca.trim(), ativo: true });
      setResultados(found.filter((m) => !enrolled.has(m.id)).slice(0, 10));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao buscar associados."));
    } finally {
      setBuscando(false);
    }
  };

  const matricular = async (membro: Membro) => {
    setErro("");
    try {
      await enrollStudent(courseId, membro.id);
      setResultados((prev) => prev.filter((m) => m.id !== membro.id));
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao matricular."));
    }
  };

  const alterarStatus = async (student: StudentEnrollment) => {
    const next = student.status === "revoked" ? "active" : "revoked";
    if (next === "revoked" && !window.confirm(`Revogar o acesso de ${student.membro_nome}?`)) return;
    try {
      const updated = await setStudentStatus(courseId, student.id, next);
      setStudents((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao alterar o acesso."));
    }
  };

  return (
    <div>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      <div className="page-form-container">
        <div className="page-form">
          <div className="form-group">
            <label className="form-label">Matricular associado manualmente</label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                className="form-input"
                value={busca}
                placeholder="Nome, e-mail ou CPF"
                onChange={(e) => setBusca(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    buscarMembros();
                  }
                }}
              />
              <button type="button" className="dashboard-btn-secondary" disabled={buscando} onClick={buscarMembros}>
                {buscando ? "Buscando..." : "Buscar"}
              </button>
            </div>
            <p className="form-help-text">Matrículas pagas pela loja são criadas automaticamente.</p>
          </div>
          {resultados.length > 0 && (
            <div className="list-stack">
              {resultados.map((m) => (
                <div key={m.id} className="list-card" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <div style={{ flex: 1 }}>
                    <div className="list-card-title">{m.nome_completo}</div>
                    <div className="list-card-meta">{m.email}</div>
                  </div>
                  <button type="button" className="btn-action-confirm" onClick={() => matricular(m)}>
                    Matricular
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="dashboard-loading">Carregando...</div>
      ) : students.length === 0 ? (
        <div className="dashboard-empty">Nenhum aluno matriculado.</div>
      ) : (
        <div className="course-table-wrap">
          <table className="course-table">
            <thead>
              <tr>
                <th>Associado</th>
                <th>Status</th>
                <th>Progresso</th>
                <th>Média nos quizzes</th>
                <th>Matrícula</th>
                <th>Último acesso</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td>
                    <div>{s.membro_nome}</div>
                    <div className="course-muted">{s.membro_email}</div>
                  </td>
                  <td>
                    <span className={`status-badge status-badge-${ENROLLMENT_STATUS_BADGE[s.status]}`}>
                      {s.status_display}
                    </span>
                  </td>
                  <td style={{ minWidth: 140 }}>
                    <div className="course-progress">
                      <div className="course-progress-bar" style={{ width: `${s.progress.percent_complete}%` }} />
                    </div>
                    <span className="course-muted">
                      {s.progress.completed_lessons}/{s.progress.total_lessons} aulas
                    </span>
                  </td>
                  <td>{s.average_quiz_score != null ? `${Math.round(s.average_quiz_score)}%` : "—"}</td>
                  <td>{formatDate(s.enrolled_at)}</td>
                  <td>{formatDate(s.last_accessed_at)}</td>
                  <td>
                    <button
                      type="button"
                      className={s.status === "revoked" ? "btn-action-confirm" : "btn-action-delete"}
                      onClick={() => alterarStatus(s)}
                    >
                      {s.status === "revoked" ? "Restaurar" : "Revogar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
