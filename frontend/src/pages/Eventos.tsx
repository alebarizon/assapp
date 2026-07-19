/**
 * Eventos Científicos — H3
 * Lista de eventos com CFP, submissões e anais integrados.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Calendar, FileText, Plus } from "lucide-react";
import type { EventoAcademico, ResumoEventos } from "@/types/eventos";
import { createEvento, getResumoEventos, listEventos } from "@/services/eventos";

export default function Eventos() {
  const [eventos, setEventos] = useState<EventoAcademico[]>([]);
  const [resumo, setResumo] = useState<ResumoEventos | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [salvando, setSalvando] = useState(false);

  const [form, setForm] = useState({
    titulo: "",
    descricao: "",
    data_inicio: "",
    data_fim: "",
    local: "",
    modalidade: "presencial",
  });

  const carregar = useCallback(async () => {
    setLoading(true);
    const [lista, kpis] = await Promise.all([listEventos(), getResumoEventos()]);
    setEventos(lista);
    setResumo(kpis);
    setLoading(false);
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    try {
      await createEvento({
        ...form,
        status: "rascunho",
      });
      setShowForm(false);
      setForm({ titulo: "", descricao: "", data_inicio: "", data_fim: "", local: "", modalidade: "presencial" });
      await carregar();
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Eventos Científicos</h1>
          <p className="dashboard-subtitle">H3 — CFP, submissões, pareceres e anais integrados</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> Novo evento
          </button>
        </div>
      </div>

      {resumo && (
        <div className="stats-grid">
          {[
            { label: "Total", value: resumo.total },
            { label: "CFP abertos", value: resumo.cfp_abertos },
            { label: "Em avaliação", value: resumo.em_avaliacao },
            { label: "Submissões", value: resumo.submissoes_pendentes },
            { label: "Pareceres pendentes", value: resumo.pareceres_pendentes },
          ].map((k) => (
            <div key={k.label} className="stat-widget">
              <div className="stat-content">
                <p className="stat-label">{k.label}</p>
                <p className="stat-value">{k.value}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleSubmit}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              Novo evento científico
            </h3>
            <div className="form-row-2">
              <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                <label className="form-label">Título *</label>
                <input
                  className="form-input"
                  required
                  value={form.titulo}
                  onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Início *</label>
                <input
                  className="form-input"
                  required
                  type="datetime-local"
                  value={form.data_inicio}
                  onChange={(e) => setForm({ ...form, data_inicio: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Fim *</label>
                <input
                  className="form-input"
                  required
                  type="datetime-local"
                  value={form.data_fim}
                  onChange={(e) => setForm({ ...form, data_fim: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Local</label>
                <input
                  className="form-input"
                  value={form.local}
                  onChange={(e) => setForm({ ...form, local: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Modalidade</label>
                <select
                  className="form-select"
                  value={form.modalidade}
                  onChange={(e) => setForm({ ...form, modalidade: e.target.value })}
                >
                  <option value="presencial">Presencial</option>
                  <option value="online">Online</option>
                  <option value="hibrido">Híbrido</option>
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                <label className="form-label">Descrição</label>
                <textarea
                  className="form-input"
                  rows={2}
                  value={form.descricao}
                  onChange={(e) => setForm({ ...form, descricao: e.target.value })}
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Salvando..." : "Criar evento"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-content-panel">
        {loading ? (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
            <p>Carregando...</p>
          </div>
        ) : eventos.length === 0 ? (
          <div className="dashboard-empty">Nenhum evento cadastrado.</div>
        ) : (
          <div className="list-stack">
            {eventos.map((ev) => (
              <Link
                key={ev.id}
                to={`/app/eventos/${ev.id}`}
                className="list-card"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Calendar size={16} style={{ color: "#a0a0a0" }} />
                    <p className="list-card-title">{ev.titulo}</p>
                  </div>
                  <p className="list-card-meta">
                    {new Date(ev.data_inicio).toLocaleDateString("pt-BR")} — {ev.local || ev.modalidade}
                  </p>
                  {ev.tem_cfp && (
                    <p className="list-card-meta" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                      <FileText size={12} />
                      {ev.submissoes_count ?? 0} submissão(ões)
                    </p>
                  )}
                </div>
                <span className={`status-badge status-badge-${ev.status}`}>
                  {ev.status_display}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
