import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, LifeBuoy, Paperclip, Plus, Search } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { abrirChamado, getResumoSuporte, listChamados } from "@/services/support";
import { apiErrorMessage } from "@/utils/apiError";
import {
  CATEGORIAS,
  STATUS_BADGE,
  STATUS_CHAMADO,
  type ChamadoCategoria,
  type ChamadoResumo,
  type ResumoSuporte,
} from "@/types/support";
import "@/components/support/Suporte.css";

function quando(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function Suporte() {
  const { user } = useAuth();
  const equipe = user?.role === "superadmin";
  const navigate = useNavigate();
  const [chamados, setChamados] = useState<ChamadoResumo[]>([]);
  const [resumo, setResumo] = useState<ResumoSuporte | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [status, setStatus] = useState("abertos");
  const [busca, setBusca] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ assunto: "", categoria: "duvida" as ChamadoCategoria, mensagem: "" });
  const [anexos, setAnexos] = useState<File[]>([]);
  const [enviando, setEnviando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const [lista, r] = await Promise.all([listChamados({ status, search: busca || undefined }), getResumoSuporte()]);
      setChamados(lista);
      setResumo(r);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar chamados."));
    } finally {
      setLoading(false);
    }
  }, [status, busca]);

  useEffect(() => {
    const t = setTimeout(() => void load(), busca ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, busca]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro("");
    try {
      const c = await abrirChamado({ ...form, anexos });
      navigate(`/app/suporte/${c.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao abrir chamado."));
      setEnviando(false);
    }
  };

  const abertos = resumo
    ? resumo.por_status.aberto + resumo.por_status.em_andamento + resumo.por_status.aguardando_associacao
    : 0;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">{equipe ? "Suporte — todas as associações" : "Suporte Gesttora"}</h1>
          <p className="dashboard-subtitle">
            {equipe
              ? "Chamados abertos pelas associações"
              : "Fale com a equipe Gesttora: dúvidas de uso, problemas técnicos e assinatura"}
          </p>
        </div>
        {!equipe && (
          <div className="dashboard-header-actions">
            <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
              <Plus size={16} /> Novo chamado
            </button>
          </div>
        )}
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      {showForm && (
        <div className="page-form-container">
          <form className="page-form" onSubmit={enviar}>
            <div className="form-row">
              <div className="form-group" style={{ flex: 2 }}>
                <label className="form-label">Assunto *</label>
                <input
                  className="form-input"
                  required
                  autoFocus
                  maxLength={200}
                  value={form.assunto}
                  placeholder="Ex.: Não consigo gerar as anuidades de 2027"
                  onChange={(e) => setForm({ ...form, assunto: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Categoria</label>
                <select className="form-select" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value as ChamadoCategoria })}>
                  {CATEGORIAS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Descreva o que aconteceu *</label>
              <textarea
                className="form-input"
                required
                rows={6}
                value={form.mensagem}
                placeholder="O que você tentou fazer, o que esperava e o que aconteceu. Se houver mensagem de erro, copie aqui."
                onChange={(e) => setForm({ ...form, mensagem: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                <Paperclip size={14} style={{ verticalAlign: "-2px" }} /> Anexos (prints, PDF, planilhas — até 5 arquivos de 10 MB)
              </label>
              <input
                type="file"
                multiple
                accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.csv,.xlsx,.xls,.docx,.doc"
                onChange={(e) => setAnexos(Array.from(e.target.files || []).slice(0, 5))}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={enviando}>
                {enviando ? "Enviando..." : "Abrir chamado"}
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
            placeholder={equipe ? "Buscar por assunto, associação ou e-mail..." : "Buscar chamado..."}
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
        <select className="form-select" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="abertos">Em aberto ({abertos})</option>
          {STATUS_CHAMADO.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label} ({resumo?.por_status[s.value] ?? 0})
            </option>
          ))}
          <option value="">Todos</option>
        </select>
      </div>

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      ) : chamados.length === 0 ? (
        <div className="dashboard-empty">
          <LifeBuoy size={20} style={{ verticalAlign: "-4px" }} />{" "}
          {equipe ? "Nenhum chamado nesta visão." : "Nenhum chamado. Precisa de ajuda? Clique em “Novo chamado”."}
        </div>
      ) : (
        <div className="list-stack">
          {chamados.map((c) => (
            <Link
              key={c.id}
              to={`/app/suporte/${c.id}`}
              className={`list-card ${c.nao_lido ? "chamado-unread" : ""}`}
              style={{ display: "flex", gap: "1rem", alignItems: "center", color: "inherit", textDecoration: "none" }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="list-card-title">
                  {c.nao_lido && <span className="chamado-dot" title="Nova resposta" />}#{c.id} · {c.assunto}
                </div>
                <div className="list-card-meta" style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                  {equipe && <strong>{c.associacao}</strong>}
                  <span>{c.categoria_display}</span>
                  <span>Por {c.autor_nome}</span>
                  <span>Atualizado {quando(c.ultima_mensagem_em || c.created_at)}</span>
                  {equipe && c.prioridade !== "normal" && <span>Prioridade: {c.prioridade_display}</span>}
                </div>
              </div>
              <span className={`status-badge status-badge-${STATUS_BADGE[c.status]}`}>{c.status_display}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
