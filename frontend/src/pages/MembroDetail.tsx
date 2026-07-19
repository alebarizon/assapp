import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Link2, Link2Off } from "lucide-react";
import type { Membro } from "@/types/membros";
import {
  desvincularUserMembro,
  getMembro,
  registrarPagamentoAnuidade,
  vincularUserMembro,
} from "@/services/membros";

export default function MembroDetail() {
  const { id } = useParams<{ id: string }>();
  const [membro, setMembro] = useState<Membro | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [vinculando, setVinculando] = useState(false);

  const carregar = async () => {
    if (!id) return;
    setLoading(true);
    try {
      setMembro(await getMembro(id));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void carregar();
  }, [id]);

  const handlePagar = async (anuidadeId: string) => {
    const nf = prompt("Número da NF (opcional):");
    await registrarPagamentoAnuidade(anuidadeId, nf || undefined);
    setMsg("Pagamento registrado.");
    await carregar();
  };

  const handleVincular = async () => {
    if (!membro) return;
    const email =
      prompt(
        "E-mail do usuário do sistema a vincular (deve coincidir com o e-mail do membro):",
        membro.email
      )?.trim() || "";
    if (!email) return;
    setVinculando(true);
    setError("");
    try {
      const updated = await vincularUserMembro(membro.id, { email });
      setMembro(updated);
      setMsg(`Vinculado a ${updated.user_email || email}.`);
    } catch {
      setError(
        "Falha ao vincular. Confira se o usuário existe e o e-mail é o mesmo do membro."
      );
    } finally {
      setVinculando(false);
    }
  };

  const handleDesvincular = async () => {
    if (!membro || !confirm("Desvincular usuário deste associado?")) return;
    setError("");
    try {
      const updated = await desvincularUserMembro(membro.id);
      setMembro(updated);
      setMsg("Usuário desvinculado.");
    } catch {
      setError("Falha ao desvincular.");
    }
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  if (!membro) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-error">Membro não encontrado.</div>
      </div>
    );
  }

  const vinculado = Boolean(membro.user);

  return (
    <div className="dashboard-page">
      <Link
        to="/app/membros"
        className="dashboard-btn-secondary"
        style={{
          marginBottom: "1.25rem",
          display: "inline-flex",
          textDecoration: "none",
          width: "fit-content",
        }}
      >
        <ArrowLeft size={16} /> Voltar para lista
      </Link>

      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">{membro.nome_completo}</h1>
          <p className="dashboard-subtitle">{membro.email}</p>
        </div>
      </div>

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <div>
            <p className="form-label" style={{ marginBottom: "0.35rem" }}>
              Usuário do sistema
            </p>
            {vinculado ? (
              <p style={{ margin: 0 }}>
                <span className="status-badge status-badge-ativa">Vinculado</span>{" "}
                {membro.user_email}
              </p>
            ) : (
              <p style={{ margin: 0 }}>
                <span className="status-badge status-badge-pendente">Sem usuário</span>
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {!vinculado ? (
              <button
                type="button"
                className="dashboard-btn-save"
                onClick={handleVincular}
                disabled={vinculando}
              >
                <Link2 size={14} /> Vincular usuário
              </button>
            ) : (
              <button type="button" className="dashboard-btn-secondary" onClick={handleDesvincular}>
                <Link2Off size={14} /> Desvincular
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        <div className="form-row-2" style={{ fontSize: "0.9rem" }}>
          {membro.cpf && (
            <div>
              <span className="form-label">CPF</span>
              <p style={{ margin: 0 }}>{membro.cpf}</p>
            </div>
          )}
          {membro.instituicao && (
            <div>
              <span className="form-label">Instituição</span>
              <p style={{ margin: 0 }}>{membro.instituicao}</p>
            </div>
          )}
          {membro.area_atuacao && (
            <div>
              <span className="form-label">Área</span>
              <p style={{ margin: 0 }}>{membro.area_atuacao}</p>
            </div>
          )}
          {membro.lattes_url && (
            <div>
              <span className="form-label">Lattes</span>
              <p style={{ margin: 0 }}>
                <a href={membro.lattes_url} target="_blank" rel="noreferrer">
                  ver currículo
                </a>
              </p>
            </div>
          )}
        </div>
      </div>

      {msg && (
        <div
          className="alert-banner alert-banner-success"
          style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
        >
          <CheckCircle size={16} /> {msg}
        </div>
      )}
      {error && <div className="alert-banner alert-banner-error">{error}</div>}

      <h2 className="dashboard-title" style={{ fontSize: "1.15rem", marginBottom: "1rem" }}>
        Histórico de filiações
      </h2>

      <div className="list-stack">
        {membro.filiacoes?.map((f) => (
          <div
            key={f.id}
            className="list-card"
            style={{ alignItems: "flex-start", flexDirection: "column" }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                width: "100%",
                gap: "1rem",
                flexWrap: "wrap",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <p className="list-card-title">{f.tipo_display}</p>
                <span className={`status-badge status-badge-${f.status}`}>{f.status_display}</span>
              </div>
              <span className="list-card-meta" style={{ margin: 0 }}>
                desde {new Date(f.data_inicio).toLocaleDateString("pt-BR")}
              </span>
            </div>

            {f.anuidades && f.anuidades.length > 0 && (
              <div className="list-stack" style={{ width: "100%", marginTop: "0.75rem" }}>
                {f.anuidades.map((a) => (
                  <div key={a.id} className="list-card">
                    <div>
                      <p className="list-card-title">
                        {a.ano_referencia} — R$ {parseFloat(a.valor).toFixed(2)}
                      </p>
                      <p className="list-card-meta">
                        Vencimento: {new Date(a.vencimento).toLocaleDateString("pt-BR")}
                      </p>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <span className={`status-badge status-badge-${a.status}`}>
                        {a.status_display}
                      </span>
                      {(a.status === "pendente" || a.status === "vencida") && (
                        <button
                          type="button"
                          className="dashboard-btn-edit"
                          onClick={() => handlePagar(a.id)}
                        >
                          Registrar pagamento
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
