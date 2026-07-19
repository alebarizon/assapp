import React, { useEffect, useState } from "react";
import type { Anuidade, Membro } from "@/types/membros";
import { getMeuMembro, listMinhasAnuidades } from "@/services/membros";

export default function MeuPerfil() {
  const [membro, setMembro] = useState<Membro | null>(null);
  const [anuidades, setAnuidades] = useState<Anuidade[]>([]);
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
    })();
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

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">{membro.nome_completo}</h1>
        <p className="dashboard-subtitle">{membro.email}</p>
      </div>

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        <div className="form-row-2" style={{ fontSize: "0.9rem" }}>
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
                    Vencimento: {new Date(a.vencimento).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <span className={`status-badge status-badge-${a.status}`}>{a.status_display}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
