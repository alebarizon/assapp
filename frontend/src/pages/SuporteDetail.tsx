import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Paperclip } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { alterarStatusChamado, getChamado, responderChamado } from "@/services/support";
import { apiErrorMessage } from "@/utils/apiError";
import { PRIORIDADES, STATUS_BADGE, STATUS_CHAMADO, type Chamado, type MensagemChamado } from "@/types/support";
import "@/components/support/Suporte.css";

function quando(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function tamanho(bytes: number) {
  return bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

const ehSistema = (m: MensagemChamado) => m.texto.startsWith("Status alterado:");

export default function SuporteDetail() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const equipe = user?.role === "superadmin";
  const [chamado, setChamado] = useState<Chamado | null>(null);
  const [erro, setErro] = useState("");
  const [texto, setTexto] = useState("");
  const [anexos, setAnexos] = useState<File[]>([]);
  const [interna, setInterna] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [inputKey, setInputKey] = useState(0);

  const load = useCallback(async () => {
    try {
      setChamado(await getChamado(id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Chamado não encontrado."));
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!texto.trim()) return;
    setEnviando(true);
    setErro("");
    try {
      setChamado(await responderChamado(id, texto, anexos, interna));
      setTexto("");
      setAnexos([]);
      setInterna(false);
      setInputKey((k) => k + 1);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar."));
    } finally {
      setEnviando(false);
    }
  };

  const mudar = async (payload: { status?: string; prioridade?: string }) => {
    setErro("");
    try {
      setChamado(await alterarStatusChamado(id, payload));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao atualizar."));
    }
  };

  if (!chamado) {
    return (
      <div className="dashboard-page">
        {erro ? <div className="alert-banner alert-banner-error">{erro}</div> : <div className="dashboard-loading"><div className="loading-spinner" /></div>}
      </div>
    );
  }

  const encerrado = chamado.status === "resolvido" || chamado.status === "fechado";

  return (
    <div className="dashboard-page">
      <Link to="/app/suporte" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Suporte
      </Link>
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title" style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            #{chamado.id} · {chamado.assunto}
            <span className={`status-badge status-badge-${STATUS_BADGE[chamado.status]}`}>{chamado.status_display}</span>
          </h1>
          <p className="dashboard-subtitle">
            {equipe ? `${chamado.associacao} · ` : ""}
            {chamado.categoria_display} · aberto em {quando(chamado.created_at)}
          </p>
        </div>
        {!equipe && (
          <div className="dashboard-header-actions">
            {chamado.status === "fechado" ? (
              <button type="button" className="dashboard-btn-secondary" onClick={() => void mudar({ status: "aberto" })}>
                Reabrir chamado
              </button>
            ) : (
              <button
                type="button"
                className="dashboard-btn-secondary"
                onClick={() => window.confirm("Fechar este chamado? Você pode reabri-lo depois.") && void mudar({ status: "fechado" })}
              >
                Fechar chamado
              </button>
            )}
          </div>
        )}
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      <div className="chamado-side">
        <div>
          <div className="chamado-thread">
            {chamado.mensagens.map((m) =>
              ehSistema(m) ? (
                <div key={m.id} className="chamado-msg chamado-msg-sistema">
                  {m.texto} · {quando(m.created_at)}
                </div>
              ) : (
                <div
                  key={m.id}
                  className={`chamado-msg ${m.interna ? "chamado-msg-interna" : m.da_equipe ? "chamado-msg-equipe" : ""}`}
                >
                  <div className="chamado-msg-meta">
                    <strong>{m.autor_nome}</strong>
                    {m.da_equipe && !m.interna && " · Equipe Gesttora"}
                    {m.interna && " · nota interna (a associação não vê)"} · {quando(m.created_at)}
                  </div>
                  <div className="chamado-msg-texto">{m.texto}</div>
                  {m.anexos.length > 0 && (
                    <div className="chamado-anexos">
                      {m.anexos.map((a) => (
                        <a key={a.id} className="chamado-anexo" href={a.url} target="_blank" rel="noopener noreferrer">
                          <Paperclip size={12} /> {a.nome} ({tamanho(a.tamanho)})
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
          </div>

          <div className="page-form-container">
            <form className="page-form" onSubmit={enviar}>
              {encerrado && !equipe && (
                <p className="form-help-text" style={{ marginTop: 0 }}>
                  Este chamado está {chamado.status_display.toLowerCase()}. Enviar uma mensagem o reabre.
                </p>
              )}
              <textarea
                className="form-input"
                rows={4}
                value={texto}
                placeholder={equipe ? "Responder à associação..." : "Escreva sua mensagem..."}
                onChange={(e) => setTexto(e.target.value)}
              />
              <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap", marginTop: "0.5rem" }}>
                <input
                  key={inputKey}
                  type="file"
                  multiple
                  accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.csv,.xlsx,.xls,.docx,.doc"
                  onChange={(e) => setAnexos(Array.from(e.target.files || []).slice(0, 5))}
                />
                {equipe && (
                  <label className="inline-check">
                    <input type="checkbox" checked={interna} onChange={(e) => setInterna(e.target.checked)} />
                    Nota interna
                  </label>
                )}
                <button type="submit" className="dashboard-btn-new" disabled={enviando || !texto.trim()} style={{ marginLeft: "auto" }}>
                  {enviando ? "Enviando..." : interna ? "Salvar nota" : "Enviar"}
                </button>
              </div>
            </form>
          </div>
        </div>

        <dl className="chamado-info">
          <div>
            <dt>Aberto por</dt>
            <dd>
              {chamado.autor_nome}
              <br />
              <a href={`mailto:${chamado.autor_email}`}>{chamado.autor_email}</a>
            </dd>
          </div>
          {equipe ? (
            <>
              <div>
                <dt>Status</dt>
                <dd>
                  <select className="form-select" value={chamado.status} onChange={(e) => void mudar({ status: e.target.value })} style={{ width: "100%" }}>
                    {STATUS_CHAMADO.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </dd>
              </div>
              <div>
                <dt>Prioridade</dt>
                <dd>
                  <select
                    className="form-select"
                    value={chamado.prioridade}
                    onChange={(e) => void mudar({ prioridade: e.target.value })}
                    style={{ width: "100%" }}
                  >
                    {PRIORIDADES.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </dd>
              </div>
            </>
          ) : (
            <div>
              <dt>Como funciona</dt>
              <dd style={{ color: "#667085" }}>
                Você recebe um e-mail quando a equipe responder. Respostas aparecem aqui com fundo verde.
              </dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
}
