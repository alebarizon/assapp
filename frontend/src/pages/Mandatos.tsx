import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRightLeft, Plus } from "lucide-react";
import type { Mandato } from "@/types";
import {
  createMandato,
  getMandatoAtivo,
  iniciarTransicao,
  listMandatos,
} from "@/services/mandatos";

export default function Mandatos() {
  const [mandatos, setMandatos] = useState<Mandato[]>([]);
  const [ativo, setAtivo] = useState<Mandato | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [novoTitulo, setNovoTitulo] = useState("");
  const [transicaoMsg, setTransicaoMsg] = useState("");

  const carregar = async () => {
    setLoading(true);
    const [lista, mandatoAtivo] = await Promise.all([listMandatos(), getMandatoAtivo()]);
    setMandatos(lista);
    setAtivo(mandatoAtivo);
    setLoading(false);
  };

  useEffect(() => {
    carregar();
  }, []);

  const handleCriar = async (e: React.FormEvent) => {
    e.preventDefault();
    const proximoNum = mandatos.length + 1;
    await createMandato({
      titulo: novoTitulo || `Diretoria ${2024 + proximoNum}-${2026 + proximoNum}`,
      numero_sequencial: proximoNum,
      data_inicio: new Date().toISOString().split("T")[0],
      status: "planejado",
    });
    setNovoTitulo("");
    setShowForm(false);
    await carregar();
  };

  const handleIniciarTransicao = async (mandatoNovo: Mandato) => {
    if (!ativo) {
      setTransicaoMsg("Nenhum mandato ativo para transicionar.");
      return;
    }
    if (
      !confirm(
        `Iniciar transição de "${ativo.titulo}" para "${mandatoNovo.titulo}"?\n\nSerá criado snapshot automático e wizard de onboarding (H1+H2).`
      )
    ) {
      return;
    }
    try {
      await iniciarTransicao(ativo.id, mandatoNovo.id);
      setTransicaoMsg("Transição iniciada! Acesse Onboarding para continuar.");
      await carregar();
    } catch {
      setTransicaoMsg("Erro ao iniciar transição.");
    }
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando mandatos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Mandatos</h1>
          <p className="dashboard-subtitle">H1 — Gestão de ciclos de diretoria</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> Novo Mandato
          </button>
        </div>
      </div>

      {ativo && (
        <div className="highlight-banner">
          <p className="highlight-banner-label">Mandato ativo</p>
          <Link
            to={`/app/mandatos/${ativo.id}`}
            className="highlight-banner-title"
            style={{ textDecoration: "none", color: "inherit", display: "block" }}
          >
            {ativo.titulo}
          </Link>
          <p className="highlight-banner-meta">
            {ativo.data_inicio} — {ativo.data_fim || "em exercício"}
          </p>
        </div>
      )}

      {transicaoMsg && <div className="alert-banner alert-banner-info">{transicaoMsg}</div>}

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleCriar}>
            <div className="form-group">
              <label className="form-label">Título</label>
              <input
                className="form-input"
                value={novoTitulo}
                onChange={(e) => setNovoTitulo(e.target.value)}
                placeholder="Ex: Diretoria 2026-2028"
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Criar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-content-panel">
        {mandatos.length === 0 ? (
          <div className="dashboard-empty">Nenhum mandato cadastrado.</div>
        ) : (
          <div className="list-stack">
            {mandatos.map((m) => (
              <div key={m.id} className="list-card">
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Link
                      to={`/app/mandatos/${m.id}`}
                      className="list-card-title"
                      style={{ textDecoration: "none", color: "inherit" }}
                    >
                      {m.titulo}
                    </Link>
                    <span className={`status-badge status-badge-${m.status}`}>
                      {m.status_display}
                    </span>
                  </div>
                  <p className="list-card-meta">
                    #{m.numero_sequencial} · {m.cargos_count ?? 0} cargos
                  </p>
                </div>
                {m.status === "planejado" && ativo && (
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    onClick={() => handleIniciarTransicao(m)}
                  >
                    <ArrowRightLeft size={14} /> Iniciar transição
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
