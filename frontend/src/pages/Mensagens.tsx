import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Plus, Search, X } from "lucide-react";
import { iniciarConversas, listConversas } from "@/services/mensagens";
import { listMembros } from "@/services/membros";
import { apiErrorMessage } from "@/utils/apiError";
import type { ConversaResumo } from "@/types/mensagens";
import type { Membro } from "@/types/membros";
import "@/components/mensagens/Mensagens.css";

function quando(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function Mensagens() {
  const navigate = useNavigate();
  const [conversas, setConversas] = useState<ConversaResumo[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [filtro, setFiltro] = useState<"aberta" | "nao_lidas" | "arquivada">("aberta");
  const [busca, setBusca] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [todos, setTodos] = useState(false);
  const [destinatarios, setDestinatarios] = useState<Membro[]>([]);
  const [buscaMembro, setBuscaMembro] = useState("");
  const [sugestoes, setSugestoes] = useState<Membro[]>([]);
  const [assunto, setAssunto] = useState("");
  const [texto, setTexto] = useState("");
  const [notificar, setNotificar] = useState(true);
  const [enviando, setEnviando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      setConversas(
        await listConversas({
          status: filtro === "arquivada" ? "arquivada" : "aberta",
          nao_lidas: filtro === "nao_lidas",
          search: busca || undefined,
        })
      );
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar mensagens."));
    } finally {
      setLoading(false);
    }
  }, [filtro, busca]);

  useEffect(() => {
    const t = setTimeout(() => void load(), busca ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, busca]);

  useEffect(() => {
    if (!buscaMembro.trim()) {
      setSugestoes([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const escolhidos = new Set(destinatarios.map((d) => d.id));
        const found = await listMembros({ q: buscaMembro.trim(), ativo: true });
        setSugestoes(found.filter((m) => !escolhidos.has(m.id)).slice(0, 8));
      } catch {
        setSugestoes([]);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [buscaMembro, destinatarios]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!todos && !destinatarios.length) {
      setErro("Escolha ao menos um associado.");
      return;
    }
    if (todos && !window.confirm("Enviar esta mensagem para todos os associados ativos? Cada um recebe uma conversa individual.")) return;
    setEnviando(true);
    setErro("");
    try {
      const r = await iniciarConversas({
        membros: todos ? undefined : destinatarios.map((d) => d.id),
        todos_ativos: todos,
        assunto: assunto.trim(),
        texto,
        notificar,
      });
      if (r.id) {
        navigate(`/app/mensagens/${r.id}`);
        return;
      }
      setAviso(`${r.criadas} conversa(s) iniciada(s).`);
      setShowForm(false);
      setDestinatarios([]);
      setAssunto("");
      setTexto("");
      setTodos(false);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar."));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Mensagens</h1>
          <p className="dashboard-subtitle">Conversas da diretoria com os associados</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
            <Plus size={16} /> Nova mensagem
          </button>
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}
      {aviso && <div className="alert-banner alert-banner-success">{aviso}</div>}

      {showForm && (
        <div className="page-form-container">
          <form className="page-form" onSubmit={enviar}>
            <div className="form-group">
              <label className="form-label">Para</label>
              <label className="inline-check">
                <input type="checkbox" checked={todos} onChange={(e) => setTodos(e.target.checked)} />
                <span>Todos os associados ativos (uma conversa individual para cada)</span>
              </label>
              {!todos && (
                <>
                  <input
                    className="form-input"
                    value={buscaMembro}
                    placeholder="Buscar associado por nome, e-mail ou CPF"
                    onChange={(e) => setBuscaMembro(e.target.value)}
                  />
                  {sugestoes.length > 0 && (
                    <div className="list-stack" style={{ marginTop: "0.35rem" }}>
                      {sugestoes.map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          className="list-card"
                          style={{ textAlign: "left", cursor: "pointer", font: "inherit" }}
                          onClick={() => {
                            setDestinatarios((d) => [...d, m]);
                            setBuscaMembro("");
                          }}
                        >
                          <span className="list-card-title">{m.nome_completo}</span>{" "}
                          <span className="list-card-meta">{m.email}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {destinatarios.length > 0 && (
                    <div className="destinatarios">
                      {destinatarios.map((d) => (
                        <span key={d.id} className="destinatario-chip">
                          {d.nome_completo}
                          <button
                            type="button"
                            aria-label={`Remover ${d.nome_completo}`}
                            onClick={() => setDestinatarios((lista) => lista.filter((x) => x.id !== d.id))}
                          >
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
            <div className="form-group">
              <label className="form-label">Assunto *</label>
              <input className="form-input" required maxLength={200} value={assunto} onChange={(e) => setAssunto(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Mensagem *</label>
              <textarea className="form-input" required rows={5} value={texto} onChange={(e) => setTexto(e.target.value)} />
            </div>
            <label className="inline-check">
              <input type="checkbox" checked={notificar} onChange={(e) => setNotificar(e.target.checked)} />
              <span>Avisar por e-mail</span>
            </label>
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

      <div className="dashboard-tabs">
        {(
          [
            ["aberta", "Abertas"],
            ["nao_lidas", "Não lidas"],
            ["arquivada", "Arquivadas"],
          ] as const
        ).map(([valor, label]) => (
          <button key={valor} type="button" className={`dashboard-tab${filtro === valor ? " active" : ""}`} onClick={() => setFiltro(valor)}>
            {label}
          </button>
        ))}
      </div>

      <div className="filters-row">
        <div style={{ position: "relative", flex: 1, minWidth: "12rem" }}>
          <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "0.7rem", color: "#a0a0a0" }} />
          <input
            className="form-input"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por assunto ou associado..."
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
      </div>

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      ) : conversas.length === 0 ? (
        <div className="dashboard-empty">Nenhuma conversa nesta visão.</div>
      ) : (
        <div className="list-stack">
          {conversas.map((c) => (
            <Link
              key={c.id}
              to={`/app/mensagens/${c.id}`}
              className={`list-card ${c.nao_lida ? "conversa-unread" : ""}`}
              style={{ display: "block", color: "inherit", textDecoration: "none" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                <div className="list-card-title">
                  {c.nao_lida && <span className="conversa-dot" />}
                  {c.membro_nome} · {c.assunto}
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
