import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMeusFormularios } from "@/services/formularios";
import { apiErrorMessage } from "@/utils/apiError";
import type { MeuFormulario } from "@/types/formularios";
import { RESPOSTA_STATUS_BADGE } from "@/types/formularios";
import "@/components/formularios/Formularios.css";

const SITUACAO_LABEL = { pendente: "A responder", em_andamento: "Rascunho salvo", enviada: "Respondido" };

export default function MeusFormularios() {
  const [itens, setItens] = useState<MeuFormulario[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    listMeusFormularios()
      .then(setItens)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar formulários.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Formulários</h1>
        <p className="dashboard-subtitle">Pesquisas e consultas da associação para você</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : itens.length === 0 ? (
        <div className="dashboard-empty">Nenhum formulário para você no momento.</div>
      ) : (
        <div className="list-stack">
          {itens.map((f) => (
            <Link
              key={f.id}
              to={`/app/portal/formularios/${f.id}`}
              className="list-card"
              style={{ display: "flex", alignItems: "center", gap: "1rem", textDecoration: "none", color: "inherit" }}
            >
              <div style={{ flex: 1 }}>
                <div className="list-card-title">{f.titulo}</div>
                <div className="list-card-meta">
                  {f.enviada_em
                    ? `Respondido em ${new Date(f.enviada_em).toLocaleDateString("pt-BR")}`
                    : f.encerra_em
                      ? `Responda até ${new Date(f.encerra_em).toLocaleString("pt-BR")}`
                      : f.descricao.slice(0, 140)}
                </div>
              </div>
              <span className={`status-badge status-badge-${RESPOSTA_STATUS_BADGE[f.minha_situacao]}`}>
                {SITUACAO_LABEL[f.minha_situacao]}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
