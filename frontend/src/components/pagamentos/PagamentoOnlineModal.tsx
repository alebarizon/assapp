import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Copy, X } from "lucide-react";
import type { ConfiguracaoPagamento } from "@/types/pagamentos";
import {
  getConfiguracaoPagamento,
  salvarConfiguracaoPagamento,
  testarConfiguracaoPagamento,
} from "@/services/pagamentos";

function mensagemErro(err: unknown, padrao: string): string {
  const data = (err as { response?: { data?: Record<string, string | string[]> } })?.response?.data;
  if (!data) return padrao;
  const primeiro = data.detail ?? Object.values(data)[0];
  return (Array.isArray(primeiro) ? primeiro[0] : primeiro) || padrao;
}

export default function PagamentoOnlineModal({ onClose }: { onClose: () => void }) {
  const [config, setConfig] = useState<ConfiguracaoPagamento | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getConfiguracaoPagamento()
      .then(setConfig)
      .catch((err) => setErro(mensagemErro(err, "Não foi possível carregar a configuração.")));
  }, []);

  const salvar = async () => {
    if (!config) return;
    setSalvando(true);
    setErro("");
    setMsg("");
    try {
      const atualizada = await salvarConfiguracaoPagamento({
        ativo: config.ativo,
        sandbox: config.sandbox,
        aceita_pix: config.aceita_pix,
        aceita_cartao: config.aceita_cartao,
        aceita_boleto: config.aceita_boleto,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
      });
      setConfig(atualizada);
      setApiKey("");
      setMsg("Configuração salva.");
    } catch (err) {
      setErro(mensagemErro(err, "Erro ao salvar."));
    } finally {
      setSalvando(false);
    }
  };

  const testar = async () => {
    setErro("");
    setMsg("");
    try {
      const r = await testarConfiguracaoPagamento();
      setMsg(
        r.saldo !== undefined
          ? `Conexão com o Asaas funcionando. Saldo da conta: R$ ${Number(r.saldo).toFixed(2)}.`
          : "Conexão com o Asaas funcionando."
      );
    } catch (err) {
      setErro(mensagemErro(err, "Falha ao conectar com o Asaas."));
    }
  };

  const set = <K extends keyof ConfiguracaoPagamento>(campo: K, valor: ConfiguracaoPagamento[K]) =>
    setConfig((atual) => (atual ? { ...atual, [campo]: valor } : atual));

  return (
    <div className="dashboard-modal-overlay" onClick={onClose}>
      <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 620 }}>
        <div className="dashboard-modal-header">
          <h2 className="dashboard-modal-title">Pagamento online (Asaas)</h2>
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
          {msg && (
            <div className="alert-banner alert-banner-success" style={{ display: "flex", gap: "0.5rem", marginTop: 0 }}>
              <CheckCircle size={16} /> {msg}
            </div>
          )}

          {!config ? (
            !erro && <p>Carregando...</p>
          ) : (
            <>
              <p className="dashboard-subtitle" style={{ marginTop: 0 }}>
                Os associados pagam a anuidade pelo portal e o dinheiro cai direto na conta Asaas da associação. A
                anuidade é quitada e lançada no financeiro automaticamente quando o Asaas confirma o pagamento.
              </p>

              <div className="form-group">
                <label className="form-label">
                  Chave de API{" "}
                  {config.tem_api_key && <span className="list-card-meta">(salva: {config.api_key_final})</span>}
                </label>
                <input
                  className="form-input"
                  type="password"
                  autoComplete="off"
                  placeholder={config.tem_api_key ? "Deixe em branco para manter a atual" : "$aact_..."}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <p className="form-help-text">No Asaas: Integrações → Chave de API.</p>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <input type="checkbox" checked={config.sandbox} onChange={(e) => set("sandbox", e.target.checked)} />{" "}
                  Ambiente de testes (sandbox) — desmarque para cobrar de verdade
                </label>
              </div>

              <div className="form-group">
                <span className="form-label">Formas aceitas</span>
                <label className="form-label" style={{ fontWeight: 400 }}>
                  <input type="checkbox" checked={config.aceita_pix} onChange={(e) => set("aceita_pix", e.target.checked)} />{" "}
                  Pix
                </label>
                <label className="form-label" style={{ fontWeight: 400 }}>
                  <input
                    type="checkbox"
                    checked={config.aceita_cartao}
                    onChange={(e) => set("aceita_cartao", e.target.checked)}
                  />{" "}
                  Cartão de crédito
                </label>
                <label className="form-label" style={{ fontWeight: 400 }}>
                  <input
                    type="checkbox"
                    checked={config.aceita_boleto}
                    onChange={(e) => set("aceita_boleto", e.target.checked)}
                  />{" "}
                  Boleto
                </label>
              </div>

              <div className="form-group">
                <span className="form-label">Webhook (cadastre no Asaas em Integrações → Webhooks)</span>
                <p className="form-help-text" style={{ marginBottom: "0.35rem" }}>
                  Eventos de cobrança; versão da API v3; envio sequencial.
                </p>
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
                  <input className="form-input" readOnly value={config.webhook_url} />
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    title="Copiar URL"
                    onClick={() => navigator.clipboard.writeText(config.webhook_url)}
                  >
                    <Copy size={14} />
                  </button>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <input className="form-input" readOnly value={config.webhook_token} aria-label="Token de autenticação" />
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    title="Copiar token"
                    onClick={() => navigator.clipboard.writeText(config.webhook_token)}
                  >
                    <Copy size={14} />
                  </button>
                </div>
                <p className="form-help-text">Cole o token acima no campo “Token de autenticação” do webhook.</p>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <input type="checkbox" checked={config.ativo} onChange={(e) => set("ativo", e.target.checked)} />{" "}
                  Oferecer pagamento online no portal do associado
                </label>
              </div>
            </>
          )}
        </div>

        <div className="dashboard-modal-footer">
          {config?.tem_api_key && (
            <button type="button" className="dashboard-btn-secondary" onClick={testar}>
              Testar conexão
            </button>
          )}
          <button type="button" className="dashboard-btn-cancel" onClick={onClose}>
            Fechar
          </button>
          <button type="button" className="dashboard-btn-save" onClick={salvar} disabled={!config || salvando}>
            {salvando ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
