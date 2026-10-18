import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, ExternalLink } from "lucide-react";
import CartaoAssociado, { BADGE_SITUACAO, dataCurta } from "@/components/membros/CartaoAssociado";
import { downloadMinhaCarteirinha, getMinhaCarteirinha } from "@/services/membros";
import type { Carteirinha } from "@/types/membros";
import { apiErrorMessage } from "@/utils/apiError";

export default function MinhaCarteirinha() {
  const [carteirinha, setCarteirinha] = useState<Carteirinha | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getMinhaCarteirinha()
      .then(setCarteirinha)
      .catch((err) => setErro(apiErrorMessage(err, "Não foi possível carregar a carteirinha.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Carteirinha</h1>
        <p className="dashboard-subtitle">Mostre o QR code para comprovar sua filiação</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : (
        carteirinha && (
          <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap", alignItems: "flex-start" }}>
            <CartaoAssociado carteirinha={carteirinha} />

            <div style={{ flex: "1 1 18rem" }}>
              <p style={{ marginTop: 0 }}>
                <span className={`status-badge status-badge-${BADGE_SITUACAO[carteirinha.situacao]}`}>
                  {carteirinha.situacao_display}
                </span>
              </p>
              {carteirinha.situacao === "pendente" && (
                <div className="highlight-banner" style={{ marginBottom: "0.75rem" }}>
                  Há anuidade em atraso: quem ler o QR verá a filiação como pendente.{" "}
                  <Link to="/app/portal/perfil">Regularizar anuidade</Link>
                </div>
              )}
              {carteirinha.situacao === "inativo" && (
                <div className="alert-banner alert-banner-error">
                  Sua filiação não está ativa. Fale com a secretaria pelo menu Mensagens.
                </div>
              )}
              {carteirinha.membro_desde && (
                <p className="list-card-meta">Associado desde {dataCurta(carteirinha.membro_desde, true)}</p>
              )}
              <p className="list-card-meta">
                Quem escanear o QR vê seu nome, matrícula, categoria e situação atual — sem e-mail, CPF ou contato.
              </p>
              <div className="filters-row" style={{ marginBottom: 0 }}>
                <button type="button" className="dashboard-btn-save" onClick={() => void downloadMinhaCarteirinha()}>
                  <Download size={14} /> Baixar PDF
                </button>
                <a className="dashboard-btn-secondary" href={carteirinha.url_verificacao} target="_blank" rel="noreferrer">
                  <ExternalLink size={14} /> Ver verificação
                </a>
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
}
