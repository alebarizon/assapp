import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Plus } from "lucide-react";
import { iniciarMinhaConversa, listMinhasConversas } from "@/services/mensagens";
import { apiErrorMessage } from "@/utils/apiError";
import type { ConversaResumo } from "@/types/mensagens";
import "@/components/mensagens/Mensagens.css";

function quando(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function MinhasMensagens() {
  const navigate = useNavigate();
  const [conversas, setConversas] = useState<ConversaResumo[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [assunto, setAssunto] = useState("");
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setConversas(await listMinhasConversas());
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar mensagens."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro("");
    try {
      const c = await iniciarMinhaConversa(assunto.trim(), texto);
      navigate(`/app/portal/mensagens/${c.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar."));
      setEnviando(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Mensagens</h1>
          <p className="dashboard-subtitle">Fale com a secretaria e a diretoria da associação</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
            <Plus size={16} /> Escrever à secretaria
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
          <form className="page-form" onSubmit={enviar}>
            <div className="form-group">
              <label className="form-label">Assunto *</label>
              <input
                className="form-input"
                required
                autoFocus
                maxLength={200}
                value={assunto}
                placeholder="Ex.: Declaração de filiação"
                onChange={(e) => setAssunto(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Mensagem *</label>
              <textarea className="form-input" required rows={5} value={texto} onChange={(e) => setTexto(e.target.value)} />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={enviando}>
                {enviando ? "Enviando..." : "Enviar"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      ) : conversas.length === 0 ? (
        <div className="dashboard-empty">Nenhuma mensagem ainda.</div>
      ) : (
        <div className="list-stack">
          {conversas.map((c) => (
            <Link
              key={c.id}
              to={`/app/portal/mensagens/${c.id}`}
              className={`list-card ${c.nao_lida ? "conversa-unread" : ""}`}
              style={{ display: "block", color: "inherit", textDecoration: "none" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                <div className="list-card-title">
                  {c.nao_lida && <span className="conversa-dot" />}
                  {c.assunto}
                </div>
                <span className="list-card-meta" style={{ whiteSpace: "nowrap" }}>
                  {quando(c.ultima_mensagem_em)}
                </span>
              </div>
              <div className="list-card-meta" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {c.previa}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
