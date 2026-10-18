import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Copy, CreditCard, ExternalLink, QrCode, Receipt, X } from "lucide-react";
import type { Cobranca, DisponibilidadePagamento, MetodoPagamento } from "@/types/pagamentos";
import { METODO_LABEL } from "@/types/pagamentos";
import { getCobranca, simularPagamento } from "@/services/pagamentos";

const ICONE: Record<MetodoPagamento, React.ReactNode> = {
  pix: <QrCode size={18} />,
  cartao: <CreditCard size={18} />,
  boleto: <Receipt size={18} />,
};

const INTERVALO_CONSULTA_MS = 5000;

function mensagemErro(err: unknown, padrao: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail || padrao;
}

export interface PagamentoModalProps {
  titulo: string;
  mensagemPago: string;
  gerar: (metodo: MetodoPagamento) => Promise<Cobranca>;
  disponibilidade: DisponibilidadePagamento;
  onClose: () => void;
  onPago: () => void;
}

export default function PagamentoModal({
  titulo,
  mensagemPago,
  gerar,
  disponibilidade,
  onClose,
  onPago,
}: PagamentoModalProps) {
  const [cobranca, setCobranca] = useState<Cobranca | null>(null);
  const [gerando, setGerando] = useState(false);
  const [erro, setErro] = useState("");
  const [copiado, setCopiado] = useState(false);

  const paga = cobranca?.status === "paga";

  useEffect(() => {
    if (!cobranca || cobranca.status !== "pendente") return;
    const timer = window.setInterval(async () => {
      try {
        const atual = await getCobranca(cobranca.id);
        setCobranca(atual);
        if (atual.status === "paga") onPago();
      } catch {
        // consulta seguinte tenta de novo
      }
    }, INTERVALO_CONSULTA_MS);
    return () => window.clearInterval(timer);
  }, [cobranca, onPago]);

  const escolher = async (metodo: MetodoPagamento) => {
    setGerando(true);
    setErro("");
    try {
      const nova = await gerar(metodo);
      setCobranca(nova);
      if (nova.metodo !== "pix" && nova.url_pagamento) {
        window.open(nova.url_pagamento, "_blank", "noopener");
      }
    } catch (err) {
      setErro(mensagemErro(err, "Não foi possível gerar a cobrança."));
    } finally {
      setGerando(false);
    }
  };

  const copiar = async () => {
    if (!cobranca?.pix_copia_cola) return;
    await navigator.clipboard.writeText(cobranca.pix_copia_cola);
    setCopiado(true);
    window.setTimeout(() => setCopiado(false), 2500);
  };

  const simular = async () => {
    if (!cobranca) return;
    try {
      const atual = await simularPagamento(cobranca.id);
      setCobranca(atual);
      onPago();
    } catch (err) {
      setErro(mensagemErro(err, "Falha ao simular o pagamento."));
    }
  };

  return (
    <div className="dashboard-modal-overlay" onClick={onClose}>
      <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
        <div className="dashboard-modal-header">
          <h2 className="dashboard-modal-title">{titulo}</h2>
          <button type="button" className="dashboard-modal-close" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <div className="dashboard-modal-content page-form">
          {erro && (
            <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem", marginTop: 0 }}>
              <AlertCircle size={16} /> {erro}
            </div>
          )}

          {disponibilidade.simulado && !paga && (
            <div className="alert-banner alert-banner-info" style={{ marginTop: 0 }}>
              Ambiente de demonstração: nenhuma cobrança real é feita.
            </div>
          )}

          {paga ? (
            <div style={{ textAlign: "center", padding: "1rem 0" }}>
              <CheckCircle size={40} color="#1a5f4a" />
              <p className="list-card-title" style={{ marginTop: "0.75rem" }}>
                Pagamento confirmado
              </p>
              <p className="list-card-meta">{mensagemPago}</p>
            </div>
          ) : !cobranca ? (
            <>
              <p style={{ marginTop: 0 }}>Escolha a forma de pagamento:</p>
              <div className="list-stack">
                {disponibilidade.metodos.map((metodo) => (
                  <button
                    key={metodo}
                    type="button"
                    className="dashboard-btn-secondary"
                    style={{ justifyContent: "flex-start", width: "100%" }}
                    disabled={gerando}
                    onClick={() => escolher(metodo)}
                  >
                    {ICONE[metodo]} {METODO_LABEL[metodo]}
                  </button>
                ))}
              </div>
              {gerando && <p className="list-card-meta">Gerando cobrança...</p>}
            </>
          ) : cobranca.metodo === "pix" ? (
            <>
              {cobranca.pix_qrcode_base64 && (
                <div style={{ textAlign: "center" }}>
                  <img
                    src={`data:image/png;base64,${cobranca.pix_qrcode_base64}`}
                    alt="QR Code Pix"
                    style={{ width: 220, height: 220 }}
                  />
                </div>
              )}
              <div className="form-group">
                <label className="form-label">Pix copia e cola</label>
                <textarea className="form-input" readOnly rows={3} value={cobranca.pix_copia_cola} />
              </div>
              <button type="button" className="dashboard-btn-save" onClick={copiar}>
                <Copy size={14} /> {copiado ? "Copiado!" : "Copiar código"}
              </button>
              <p className="list-card-meta" style={{ marginTop: "1rem" }}>
                Assim que o banco confirmar, esta tela atualiza sozinha.
              </p>
            </>
          ) : (
            <>
              <p style={{ marginTop: 0 }}>
                O pagamento por {METODO_LABEL[cobranca.metodo].toLowerCase()} é feito na página segura do gateway.
              </p>
              {cobranca.url_pagamento && (
                <a
                  className="dashboard-btn-save"
                  href={cobranca.url_pagamento}
                  target="_blank"
                  rel="noreferrer"
                  style={{ textDecoration: "none", display: "inline-flex" }}
                >
                  <ExternalLink size={14} /> Abrir página de pagamento
                </a>
              )}
              <p className="list-card-meta" style={{ marginTop: "1rem" }}>
                Depois de pagar, esta tela atualiza sozinha.
              </p>
            </>
          )}
        </div>

        <div className="dashboard-modal-footer">
          {cobranca && !paga && cobranca.provedor === "simulado" && (
            <button type="button" className="dashboard-btn-edit" onClick={simular}>
              Simular pagamento confirmado
            </button>
          )}
          {cobranca && !paga && (
            <button type="button" className="dashboard-btn-secondary" onClick={() => setCobranca(null)}>
              Outra forma de pagamento
            </button>
          )}
          <button type="button" className="dashboard-btn-cancel" onClick={onClose}>
            {paga ? "Fechar" : "Pagar depois"}
          </button>
        </div>
      </div>
    </div>
  );
}
