import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Copy, X } from "lucide-react";
import type { ConfiguracaoPagamento, ProvedorPagamento } from "@/types/pagamentos";
import { PROVEDOR_INFO } from "@/types/pagamentos";
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
  const [provedorSalvo, setProvedorSalvo] = useState<ProvedorPagamento | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getConfiguracaoPagamento()
      .then((c) => {
        setConfig(c);
        setProvedorSalvo(c.provedor);
      })
      .catch((err) => setErro(mensagemErro(err, "Não foi possível carregar a configuração.")));
  }, []);

  const info = config ? PROVEDOR_INFO[config.provedor] : PROVEDOR_INFO.asaas;
  const trocouProvedor = !!config && config.provedor !== provedorSalvo;
  const chaveSalva = !!config?.tem_api_key && !trocouProvedor;

  const salvar = async () => {
    if (!config) return;
    setSalvando(true);
    setErro("");
    setMsg("");
    try {
      const atualizada = await salvarConfiguracaoPagamento({
        provedor: config.provedor,
        ativo: config.ativo,
        sandbox: config.sandbox,
        aceita_pix: config.aceita_pix,
        aceita_cartao: config.aceita_cartao,
        aceita_boleto: config.aceita_boleto,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
      });
      setConfig(atualizada);
      setProvedorSalvo(atualizada.provedor);
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
      const base = `Conexão com o ${info.nome} funcionando.`;
      if (r.saldo !== undefined && r.saldo !== null) {
        setMsg(`${base} Saldo da conta: R$ ${Number(r.saldo).toFixed(2)}.`);
      } else if (r.conta) {
        setMsg(`${base} Conta: ${r.conta}.`);
      } else {
        setMsg(base);
      }
    } catch (err) {
      setErro(mensagemErro(err, `Falha ao conectar com o ${info.nome}.`));
    }
  };

  const copiavel = (valor: string, rotulo: string) => (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
      <input className="form-input" readOnly value={valor} aria-label={rotulo} />
      <button
        type="button"
        className="dashboard-btn-secondary"
        title={`Copiar ${rotulo.toLowerCase()}`}
        onClick={() => navigator.clipboard.writeText(valor)}
      >
        <Copy size={14} />
      </button>
    </div>
  );

  const set = <K extends keyof ConfiguracaoPagamento>(campo: K, valor: ConfiguracaoPagamento[K]) =>
    setConfig((atual) => (atual ? { ...atual, [campo]: valor } : atual));

  return (
    <div className="dashboard-modal-overlay" onClick={onClose}>
      <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 620 }}>
        <div className="dashboard-modal-header">
          <h2 className="dashboard-modal-title">Pagamento online</h2>
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
                Os associados pagam a anuidade e os pedidos da loja pelo portal e o dinheiro cai direto na conta da
                associação no gateway escolhido. A cobrança é quitada e lançada no financeiro automaticamente quando o
                gateway confirma o pagamento.
              </p>

              <div className="form-group">
                <label className="form-label" htmlFor="provedor-pagamento">
                  Gateway
                </label>
                <select
                  id="provedor-pagamento"
                  className="form-select"
                  value={config.provedor}
                  onChange={(e) => set("provedor", e.target.value as ProvedorPagamento)}
                >
                  {(Object.keys(PROVEDOR_INFO) as ProvedorPagamento[]).map((p) => (
                    <option key={p} value={p}>
                      {PROVEDOR_INFO[p].nome}
                    </option>
                  ))}
                </select>
                {trocouProvedor && (
                  <p className="form-help-text">
                    Ao trocar de gateway, informe a chave do {info.nome}. Cobranças já geradas no gateway anterior
                    continuam válidas lá, mas deixam de ser acompanhadas por aqui.
                  </p>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">
                  {config.provedor === "mercadopago" ? "Access Token" : config.provedor === "pagbank" ? "Token" : "Chave de API"}{" "}
                  {chaveSalva && <span className="list-card-meta">(salva: {config.api_key_final})</span>}
                </label>
                <input
                  className="form-input"
                  type="password"
                  autoComplete="off"
                  placeholder={chaveSalva ? "Deixe em branco para manter a atual" : info.placeholder}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <p className="form-help-text">{info.ondeChave}</p>
              </div>

              {info.sandbox && (
                <div className="form-group">
                  <label className="form-label">
                    <input type="checkbox" checked={config.sandbox} onChange={(e) => set("sandbox", e.target.checked)} />{" "}
                    Ambiente de testes (sandbox) — desmarque para cobrar de verdade
                  </label>
                </div>
              )}

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

              {config.provedor === "asaas" ? (
                <div className="form-group">
                  <span className="form-label">Webhook (cadastre no Asaas em Integrações → Webhooks)</span>
                  <p className="form-help-text" style={{ marginBottom: "0.35rem" }}>
                    Eventos de cobrança; versão da API v3; envio sequencial.
                  </p>
                  {copiavel(config.webhook_url, "URL")}
                  {copiavel(config.webhook_token, "Token de autenticação")}
                  <p className="form-help-text">Cole o token acima no campo “Token de autenticação” do webhook.</p>
                </div>
              ) : (
                <div className="form-group">
                  <span className="form-label">Confirmação do pagamento</span>
                  <p className="form-help-text">
                    Pix aparece com QR Code no portal; cartão e boleto abrem a página de pagamento do {info.nome}, onde
                    o associado completa os dados.
                  </p>
                  {config.notificacao_automatica ? (
                    <p className="form-help-text">
                      O endereço de notificação é enviado automaticamente em cada cobrança — não é preciso cadastrar
                      webhook no {info.nome}.
                    </p>
                  ) : (
                    <div className="alert-banner alert-banner-info" style={{ marginTop: "0.35rem" }}>
                      O site ainda não usa HTTPS, exigido pelo {info.nome} para notificar pagamentos. Enquanto isso, o
                      sistema consulta o {info.nome}: com o portal aberto, o Pix é confirmado em segundos; nos demais
                      casos, em até 30 minutos.
                    </div>
                  )}
                </div>
              )}

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
          {chaveSalva && (
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
