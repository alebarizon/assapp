import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, ClipboardList, Copy, Globe, Plus, Search, Trash2, Users } from "lucide-react";
import { createFormulario, deleteFormulario, duplicarFormulario, listFormularios } from "@/services/formularios";
import { apiErrorMessage } from "@/utils/apiError";
import type { FormularioResumo, FormularioStatus } from "@/types/formularios";
import { FORMULARIO_STATUS_BADGE } from "@/types/formularios";
import "@/components/formularios/Formularios.css";

export default function Formularios() {
  const navigate = useNavigate();
  const [formularios, setFormularios] = useState<FormularioResumo[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [status, setStatus] = useState<FormularioStatus | "">("");
  const [showForm, setShowForm] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [criando, setCriando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      setFormularios(await listFormularios({ search: busca || undefined, status: status || undefined }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar formulários."));
    } finally {
      setLoading(false);
    }
  }, [busca, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const criar = async (e: React.FormEvent) => {
    e.preventDefault();
    setCriando(true);
    try {
      const novo = await createFormulario({ titulo: titulo.trim() });
      navigate(`/app/formularios/${novo.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar."));
      setCriando(false);
    }
  };

  const duplicar = async (f: FormularioResumo) => {
    try {
      const copia = await duplicarFormulario(f.id);
      navigate(`/app/formularios/${copia.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao duplicar."));
    }
  };

  const excluir = async (f: FormularioResumo) => {
    const aviso = f.respostas_enviadas
      ? `"${f.titulo}" tem ${f.respostas_enviadas} resposta(s), que também serão excluídas. Continuar? Prefira encerrar.`
      : `Excluir o formulário "${f.titulo}"?`;
    if (!window.confirm(aviso)) return;
    try {
      await deleteFormulario(f.id);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Formulários</h1>
          <p className="dashboard-subtitle">Pesquisas, avaliações de evento e consultas aos associados</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
            <Plus size={16} /> Novo formulário
          </button>
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      {showForm && (
        <div className="page-form-container">
          <form className="page-form" onSubmit={criar}>
            <div className="form-group">
              <label className="form-label">Título *</label>
              <input
                className="form-input"
                required
                maxLength={200}
                autoFocus
                value={titulo}
                placeholder="Ex.: Avaliação do Congresso 2026"
                onChange={(e) => setTitulo(e.target.value)}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={criando || !titulo.trim()}>
                {criando ? "Criando..." : "Criar e montar perguntas"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="filters-row">
        <div style={{ position: "relative", flex: 1, minWidth: "12rem" }}>
          <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "0.7rem", color: "#a0a0a0" }} />
          <input
            className="form-input"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar formulário..."
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
        <select className="form-select" value={status} onChange={(e) => setStatus(e.target.value as FormularioStatus | "")}>
          <option value="">Todos os status</option>
          <option value="rascunho">Rascunho</option>
          <option value="publicado">Recebendo respostas</option>
          <option value="encerrado">Encerrado</option>
        </select>
      </div>

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : formularios.length === 0 ? (
        <div className="dashboard-empty">Nenhum formulário ainda. Clique em “Novo formulário” para começar.</div>
      ) : (
        <div className="list-stack">
          {formularios.map((f) => (
            <div key={f.id} className="list-card" style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
              <Link to={`/app/formularios/${f.id}`} style={{ flex: 1, color: "inherit", textDecoration: "none" }}>
                <div className="list-card-title">{f.titulo}</div>
                <div className="list-card-meta" style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                  <span>
                    <ClipboardList size={13} /> {f.perguntas_count} perguntas · {f.respostas_enviadas} respostas
                  </span>
                  {f.convites_pendentes > 0 && <span>{f.convites_pendentes} convites pendentes</span>}
                  {f.link_publico_ativo && (
                    <span>
                      <Globe size={13} /> link público
                    </span>
                  )}
                  {f.disponivel_no_portal && (
                    <span>
                      <Users size={13} /> portal
                    </span>
                  )}
                  {f.evento_titulo && <span>Evento: {f.evento_titulo}</span>}
                </div>
              </Link>
              <span className={`status-badge status-badge-${FORMULARIO_STATUS_BADGE[f.status]}`}>{f.status_display}</span>
              <button type="button" className="fb-icon-btn" title="Duplicar" onClick={() => duplicar(f)}>
                <Copy size={16} />
              </button>
              <button type="button" className="fb-icon-btn" title="Excluir" onClick={() => excluir(f)}>
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
