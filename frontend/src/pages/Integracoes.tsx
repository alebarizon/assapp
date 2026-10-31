import { useEffect, useState, type FormEvent } from "react";
import { Copy, Plug, Plus, Send, Trash2, Webhook } from "lucide-react";
import PagamentoOnlineModal from "@/components/pagamentos/PagamentoOnlineModal";
import "@/components/integracoes/Integracoes.css";
import {
  deleteWebhook,
  getCatalogo,
  listEntregas,
  listWebhooks,
  regenerarSegredo,
  salvarWebhook,
  testarWebhook,
} from "@/services/integracoes";
import {
  SITUACAO_CONECTOR,
  STATUS_ENTREGA,
  type Catalogo,
  type Conector,
  type EntregaWebhook,
  type WebhookSaida,
} from "@/types/integracoes";
import { apiErrorMessage } from "@/utils/apiError";

function dataCurta(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "";
}

const FORM_VAZIO = { url: "", descricao: "", eventos: [] as string[] };

export default function Integracoes() {
  const [catalogo, setCatalogo] = useState<Catalogo>();
  const [webhooks, setWebhooks] = useState<WebhookSaida[]>([]);
  const [aba, setAba] = useState<"catalogo" | "webhooks">("catalogo");
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [pagamentoAberto, setPagamentoAberto] = useState(false);
  const [form, setForm] = useState(FORM_VAZIO);
  const [formAberto, setFormAberto] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [entregas, setEntregas] = useState<Record<string, EntregaWebhook[]>>({});

  const carregar = () =>
    Promise.all([getCatalogo(), listWebhooks()])
      .then(([c, w]) => {
        setCatalogo(c);
        setWebhooks(w);
      })
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar as integrações.")));

  useEffect(() => {
    carregar().finally(() => setLoading(false));
  }, []);

  const rotuloEvento = (slug: string) => catalogo?.eventos.find((e) => e.slug === slug)?.label ?? slug;

  const abrirConector = (c: Conector) => {
    setErro("");
    if (c.acao === "pagamento") setPagamentoAberto(true);
    if (c.acao === "webhooks") setAba("webhooks");
  };

  const criar = async (e: FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      const novo = await salvarWebhook(null, form);
      setWebhooks((lista) => [...lista, novo]);
      setForm(FORM_VAZIO);
      setFormAberto(false);
      setMsg("Webhook criado. Use “Testar” para conferir se o endereço responde.");
      getCatalogo().then(setCatalogo).catch(() => undefined);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar o webhook."));
    } finally {
      setSalvando(false);
    }
  };

  const substituir = (w: WebhookSaida) => setWebhooks((lista) => lista.map((x) => (x.id === w.id ? w : x)));

  const executar = async (acao: () => Promise<void>, falha: string) => {
    setErro("");
    setMsg("");
    try {
      await acao();
    } catch (err) {
      setErro(apiErrorMessage(err, falha));
    }
  };

  const verEntregas = (w: WebhookSaida) =>
    executar(async () => {
      if (entregas[w.id]) {
        setEntregas((atual) => {
          const resto = { ...atual };
          delete resto[w.id];
          return resto;
        });
        return;
      }
      const lista = await listEntregas(w.id);
      setEntregas((atual) => ({ ...atual, [w.id]: lista }));
    }, "Erro ao carregar as entregas.");

  const testar = (w: WebhookSaida) =>
    executar(async () => {
      const r = await testarWebhook(w.id);
      if (r.status === "entregue") setMsg(`Teste entregue (HTTP ${r.resposta_status}).`);
      else setErro(`O teste falhou: ${r.ultimo_erro || "sem resposta"}`);
      const lista = await listEntregas(w.id);
      setEntregas((atual) => ({ ...atual, [w.id]: lista }));
      setWebhooks(await listWebhooks());
    }, "Erro ao testar o webhook.");

  const alternar = (w: WebhookSaida) =>
    executar(async () => {
      substituir(await salvarWebhook(w.id, { ativo: !w.ativo }));
      getCatalogo().then(setCatalogo).catch(() => undefined);
    }, "Erro ao atualizar o webhook.");

  const novoSegredo = (w: WebhookSaida) => {
    if (!window.confirm("Gerar um novo segredo? O sistema que recebe precisa ser atualizado com o novo valor.")) return;
    executar(async () => substituir(await regenerarSegredo(w.id)), "Erro ao gerar o segredo.");
  };

  const excluir = (w: WebhookSaida) => {
    if (!window.confirm(`Excluir o webhook ${w.descricao || w.url}?`)) return;
    executar(async () => {
      await deleteWebhook(w.id);
      setWebhooks((lista) => lista.filter((x) => x.id !== w.id));
      getCatalogo().then(setCatalogo).catch(() => undefined);
    }, "Erro ao excluir o webhook.");
  };

  const copiar = (texto: string) => {
    navigator.clipboard?.writeText(texto).then(() => setMsg("Segredo copiado."));
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Integrações</h1>
        <p className="dashboard-subtitle">Conecte a associação a gateways de pagamento, automações e outros sistemas</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      <div className="dashboard-tabs">
        <button type="button" className={`dashboard-tab${aba === "catalogo" ? " active" : ""}`} onClick={() => setAba("catalogo")}>
          <Plug size={14} /> Catálogo
        </button>
        <button type="button" className={`dashboard-tab${aba === "webhooks" ? " active" : ""}`} onClick={() => setAba("webhooks")}>
          <Webhook size={14} /> Webhooks de saída ({webhooks.length})
        </button>
      </div>

      {aba === "catalogo" && catalogo && (
        <div className="dashboard-content-panel">
          {catalogo.categorias.map((cat) => {
            const itens = catalogo.conectores.filter((c) => c.categoria === cat.slug);
            if (!itens.length) return null;
            return (
              <section key={cat.slug} className="int-categoria">
                <h2 className="int-categoria-titulo">{cat.label}</h2>
                <div className="int-grid">
                  {itens.map((c) => {
                    const st = SITUACAO_CONECTOR[c.situacao];
                    const podeAbrir = c.acao === "webhooks" || (c.acao === "pagamento" && catalogo.pode_configurar_pagamento);
                    return (
                      <div key={c.slug} className={`int-card${c.situacao === "em_breve" ? " int-card-em-breve" : ""}`}>
                        <div className="int-card-topo">
                          <p className="list-card-title" style={{ margin: 0 }}>{c.nome}</p>
                          <span className={`status-badge status-badge-${st.badge}`}>{st.label}</span>
                        </div>
                        <p className="list-card-meta" style={{ margin: 0 }}>{c.descricao}</p>
                        {podeAbrir && (
                          <div className="int-card-acao">
                            <button type="button" className="dashboard-btn-secondary" onClick={() => abrirConector(c)}>
                              Configurar
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
          <p className="form-help-text">
            Os gateways de pagamento usam uma configuração só: ativar um deles substitui o anterior.
          </p>
        </div>
      )}

      {aba === "webhooks" && (
        <div className="dashboard-content-panel">
          <div className="dashboard-header-row" style={{ marginBottom: "1rem" }}>
            <p className="list-card-meta" style={{ margin: 0, maxWidth: 640 }}>
              A cada evento escolhido, o sistema envia um POST em JSON para o endereço. Cada envio leva o cabeçalho{" "}
              <code>X-Gesttora-Assinatura</code> (HMAC-SHA256 do segredo sobre <code>timestamp.corpo</code>, com o
              timestamp em <code>X-Gesttora-Timestamp</code>). Se o endereço não responder 2xx, o envio é repetido por
              até ~17 h.
            </p>
            {!formAberto && (
              <button type="button" className="dashboard-btn-new" onClick={() => setFormAberto(true)}>
                <Plus size={16} /> Novo webhook
              </button>
            )}
          </div>

          {formAberto && catalogo && (
            <form className="page-form" onSubmit={criar} style={{ marginBottom: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label" htmlFor="wh-url">Endereço (https)</label>
                <input
                  id="wh-url"
                  className="form-input"
                  type="url"
                  required
                  placeholder="https://hook.make.com/..."
                  value={form.url}
                  onChange={(e) => setForm({ ...form, url: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="wh-desc">Descrição</label>
                <input
                  id="wh-desc"
                  className="form-input"
                  maxLength={120}
                  placeholder="Ex.: Planilha da tesouraria (Make)"
                  value={form.descricao}
                  onChange={(e) => setForm({ ...form, descricao: e.target.value })}
                />
              </div>
              <div className="form-group">
                <span className="form-label">Eventos</span>
                <div className="int-eventos">
                  {catalogo.eventos.map((ev) => (
                    <label key={ev.slug}>
                      <input
                        type="checkbox"
                        checked={form.eventos.includes(ev.slug)}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            eventos: e.target.checked ? [...form.eventos, ev.slug] : form.eventos.filter((x) => x !== ev.slug),
                          })
                        }
                      />
                      {ev.label}
                    </label>
                  ))}
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="dashboard-btn-cancel" onClick={() => setFormAberto(false)}>
                  Cancelar
                </button>
                <button type="submit" className="dashboard-btn-save" disabled={salvando || !form.eventos.length}>
                  {salvando ? "Salvando..." : "Criar webhook"}
                </button>
              </div>
            </form>
          )}

          {webhooks.length === 0 && !formAberto ? (
            <div className="dashboard-empty">
              Nenhum webhook. Crie um para mandar os eventos ao Make, Zapier, n8n, Pluga ou a um sistema próprio.
            </div>
          ) : (
            <div className="list-stack">
              {webhooks.map((w) => (
                <div key={w.id} className="list-card" style={{ display: "block" }}>
                  <div className="int-card-topo">
                    <div>
                      <p className="list-card-title">{w.descricao || w.url}</p>
                      {w.descricao && <p className="list-card-meta">{w.url}</p>}
                      <p className="list-card-meta">
                        {w.eventos.map(rotuloEvento).join(" · ")}
                        {w.ultima_entrega_em && ` · última entrega ${dataCurta(w.ultima_entrega_em)}`}
                        {w.falhas_seguidas > 0 && ` · ${w.falhas_seguidas} falhas seguidas`}
                      </p>
                      <p className="list-card-meta int-segredo">
                        Segredo: {w.segredo}{" "}
                        <button type="button" className="int-copiar" onClick={() => copiar(w.segredo)} title="Copiar" aria-label="Copiar segredo">
                          <Copy size={12} />
                        </button>
                      </p>
                    </div>
                    <span className={`status-badge status-badge-${w.ativo ? "ativo" : "inativa"}`}>
                      {w.ativo ? "Ativo" : "Desligado"}
                    </span>
                  </div>
                  <div className="form-actions" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
                    <button type="button" className="dashboard-btn-secondary" onClick={() => testar(w)}>
                      <Send size={14} /> Testar
                    </button>
                    <button type="button" className="dashboard-btn-secondary" onClick={() => verEntregas(w)}>
                      {entregas[w.id] ? "Ocultar entregas" : "Entregas"}
                    </button>
                    <button type="button" className="dashboard-btn-secondary" onClick={() => alternar(w)}>
                      {w.ativo ? "Desligar" : "Ligar"}
                    </button>
                    <button type="button" className="dashboard-btn-secondary" onClick={() => novoSegredo(w)}>
                      Novo segredo
                    </button>
                    <button type="button" className="dashboard-btn-danger" onClick={() => excluir(w)}>
                      <Trash2 size={14} /> Excluir
                    </button>
                  </div>
                  {entregas[w.id] && (
                    <div className="int-entregas">
                      {entregas[w.id].length === 0 ? (
                        <p className="list-card-meta">Nenhuma entrega ainda.</p>
                      ) : (
                        entregas[w.id].map((e) => {
                          const st = STATUS_ENTREGA[e.status];
                          return (
                            <div key={e.id} className="int-entrega">
                              <span>
                                {e.evento === "ping" ? "Teste" : rotuloEvento(e.evento)} · {dataCurta(e.created_at)}
                                {e.resposta_status != null && ` · HTTP ${e.resposta_status}`}
                                {e.tentativas > 1 && ` · ${e.tentativas} tentativas`}
                                {e.ultimo_erro && e.status !== "entregue" && (
                                  <span className="list-card-meta"> — {e.ultimo_erro}</span>
                                )}
                              </span>
                              <span className={`status-badge status-badge-${st.badge}`}>{st.label}</span>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {pagamentoAberto && (
        <PagamentoOnlineModal
          onClose={() => {
            setPagamentoAberto(false);
            getCatalogo().then(setCatalogo).catch(() => undefined);
          }}
        />
      )}
    </div>
  );
}
