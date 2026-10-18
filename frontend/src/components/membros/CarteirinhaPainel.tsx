import { useState } from "react";
import { CreditCard, Download, RefreshCw } from "lucide-react";
import CartaoAssociado, { BADGE_SITUACAO } from "./CartaoAssociado";
import { downloadCarteirinhaMembro, getCarteirinhaMembro, renovarCarteirinha } from "@/services/membros";
import type { Carteirinha } from "@/types/membros";
import { apiErrorMessage } from "@/utils/apiError";

export default function CarteirinhaPainel({ membroId, podeEditar }: { membroId: string; podeEditar: boolean }) {
  const [carteirinha, setCarteirinha] = useState<Carteirinha | null>(null);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  const executar = async (acao: () => Promise<Carteirinha>, sucesso = "") => {
    setErro("");
    try {
      setCarteirinha(await acao());
      setMsg(sucesso);
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível carregar a carteirinha."));
    }
  };

  return (
    <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}
      {!carteirinha ? (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
          <p className="form-label" style={{ margin: 0 }}>Carteirinha digital</p>
          <button type="button" className="dashboard-btn-secondary" onClick={() => void executar(() => getCarteirinhaMembro(membroId))}>
            <CreditCard size={14} /> Ver carteirinha
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", alignItems: "flex-start" }}>
          <CartaoAssociado carteirinha={carteirinha} />
          <div style={{ flex: "1 1 14rem" }}>
            <p style={{ marginTop: 0 }}>
              <span className={`status-badge status-badge-${BADGE_SITUACAO[carteirinha.situacao]}`}>
                {carteirinha.situacao_display}
              </span>
            </p>
            <div className="filters-row" style={{ marginBottom: 0 }}>
              <button type="button" className="dashboard-btn-secondary" onClick={() => void downloadCarteirinhaMembro(membroId)}>
                <Download size={14} /> PDF
              </button>
              {podeEditar && (
                <button
                  type="button"
                  className="dashboard-btn-cancel"
                  onClick={() =>
                    confirm("Gerar novo QR? A carteirinha atual (impressa ou salva) deixa de ser válida.") &&
                    void executar(() => renovarCarteirinha(membroId), "Novo QR gerado. O anterior não valida mais.")
                  }
                >
                  <RefreshCw size={14} /> Gerar novo QR
                </button>
              )}
            </div>
            <p className="list-card-meta">Use "Gerar novo QR" em caso de perda ou uso indevido da carteirinha.</p>
          </div>
        </div>
      )}
    </div>
  );
}
