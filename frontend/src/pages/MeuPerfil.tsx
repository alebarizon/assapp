import React, { useCallback, useEffect, useState } from "react";
import type { Anuidade, Membro } from "@/types/membros";
import type { DisponibilidadePagamento } from "@/types/pagamentos";
import { getMeuMembro, listMinhasAnuidades } from "@/services/membros";
import { getDisponibilidadePagamento } from "@/services/pagamentos";
import PagarAnuidadeModal from "@/components/pagamentos/PagarAnuidadeModal";
import PerfilPublicoForm from "@/components/membros/PerfilPublicoForm";

export default function MeuPerfil() {
  const [membro, setMembro] = useState<Membro | null>(null);
  const [anuidades, setAnuidades] = useState<Anuidade[]>([]);
  const [disponibilidade, setDisponibilidade] = useState<DisponibilidadePagamento | null>(null);
  const [pagando, setPagando] = useState<Anuidade | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [m, a] = await Promise.all([getMeuMembro(), listMinhasAnuidades()]);
        setMembro(m);
        setAnuidades(a);
      } catch {
        setError("Perfil não encontrado. Peça à diretoria para vincular seu usuário ao quadro.");
      } finally {
        setLoading(false);
      }
      try {
        setDisponibilidade(await getDisponibilidadePagamento());
      } catch {
        setDisponibilidade(null);
      }
    })();
  }, []);

  const recarregarAnuidades = useCallback(async () => {
    setAnuidades(await listMinhasAnuidades());
  }, []);

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando perfil...</p>
        </div>
      </div>
    );
  }

  if (error || !membro) {
    return (
      <div className="dashboard-page">
        <h1 className="dashboard-title">Meu perfil</h1>
        <div className="alert-banner alert-banner-error">{error || "Sem dados."}</div>
      </div>
    );
  }

  const pagamentoOnline = Boolean(disponibilidade?.habilitado && disponibilidade.metodos.length > 0);
  const emAberto = (a: Anuidade) => (a.status === "pendente" || a.status === "vencida") && parseFloat(a.valor) > 0;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">{membro.nome_completo}</h1>
        <p className="dashboard-subtitle">{membro.email}</p>
      </div>

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        <div className="form-row-2" style={{ fontSize: "0.9rem" }}>
          {membro.filiacao_tipo && (
            <div>
              <span className="form-label">Tipo de filiação</span>
              <p style={{ margin: 0 }}>{membro.filiacao_tipo}</p>
            </div>
          )}
          {membro.filiacao_status && (
            <div>
              <span className="form-label">Status</span>
              <p style={{ margin: 0 }}>{membro.filiacao_status}</p>
            </div>
          )}
        </div>
      </div>

      <PerfilPublicoForm membro={membro} onSalvo={setMembro} />

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
        Anuidades
      </h2>
      <div className="dashboard-content-panel">
        {anuidades.length === 0 ? (
          <div className="dashboard-empty">Nenhuma anuidade registrada.</div>
        ) : (
          <div className="list-stack">
            {anuidades.map((a) => (
              <div key={a.id} className="list-card">
                <div>
                  <p className="list-card-title">
                    {a.ano_referencia} — R$ {parseFloat(a.valor).toFixed(2)}
                  </p>
                  <p className="list-card-meta">
                    Vencimento: {new Date(`${a.vencimento}T00:00:00`).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span className={`status-badge status-badge-${a.status}`}>{a.status_display}</span>
                  {emAberto(a) && pagamentoOnline && (
                    <button type="button" className="dashboard-btn-save" onClick={() => setPagando(a)}>
                      Pagar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {anuidades.some(emAberto) && !pagamentoOnline && (
          <p className="list-card-meta" style={{ marginTop: "1rem" }}>
            Para pagar, fale com a secretaria da associação.
          </p>
        )}
      </div>

      {pagando && disponibilidade && (
        <PagarAnuidadeModal
          anuidade={pagando}
          disponibilidade={disponibilidade}
          onClose={() => setPagando(null)}
          onPago={recarregarAnuidades}
        />
      )}
    </div>
  );
}
