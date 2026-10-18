import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Copy, FlaskConical, Save, Send, Trash2, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  cancelarCampanha,
  deleteCampanha,
  duplicarCampanha,
  enviarCampanha,
  enviarTeste,
  getCampanha,
  getOpcoesPublico,
  listEnvios,
  previaPublico,
  salvarCampanha,
} from "@/services/newsletter";
import {
  SITUACAO_LABEL,
  STATUS_CAMPANHA,
  STATUS_ENVIO,
  TIPO_LABEL,
  descreverPublico,
  type Campanha,
  type EnvioCampanha,
  type OpcoesPublico,
  type PublicoCampanha,
  type ResumoPublico,
  type SituacaoPublico,
  type StatusEnvio,
  type TipoFiliacao,
} from "@/types/newsletter";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";
import "@/components/newsletter/Newsletter.css";

const PUBLICO_PADRAO: PublicoCampanha = { associados: { situacoes: ["em_dia", "pendente"], tipos: [] } };
const ORIGEM_LABEL: Record<string, string> = { associados: "associado", eventos: "inscrito", contatos: "contato" };

function alternar<T>(lista: T[], valor: T): T[] {
  return lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor];
}

function dataHora(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";
}

function Chip({ on, label, onClick, disabled }: { on: boolean; label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <label className={`nl-chip${on ? " is-on" : ""}`}>
      <input type="checkbox" checked={on} onChange={onClick} disabled={disabled} />
      {label}
    </label>
  );
}

export default function CampanhaDetail() {
  const { id = "nova" } = useParams();
  const nova = id === "nova";
  const navigate = useNavigate();
  const { user } = useAuth();
  const editavel = podeEditar(user, "newsletter");

  const [campanha, setCampanha] = useState<Campanha | null>(null);
  const [form, setForm] = useState({ assunto: "", corpo: "Olá, {nome}!\n\n", link: "", link_label: "" });
  const [publico, setPublico] = useState<PublicoCampanha>(PUBLICO_PADRAO);
  const [opcoes, setOpcoes] = useState<OpcoesPublico>({ eventos: [], etiquetas: [] });
  const [resumo, setResumo] = useState<ResumoPublico | null>(null);
  const [envios, setEnvios] = useState<EnvioCampanha[]>([]);
  const [filtro, setFiltro] = useState<StatusEnvio | "">("");
  const [carregando, setCarregando] = useState(!nova);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  const rascunho = nova || campanha?.status === "rascunho";
  const podeMexer = editavel && rascunho;

  const carregar = useCallback(async () => {
    if (nova) return;
    try {
      const c = await getCampanha(id);
      setCampanha(c);
      setForm({ assunto: c.assunto, corpo: c.corpo, link: c.link, link_label: c.link_label });
      setPublico(c.publico);
    } catch (err) {
      setErro(apiErrorMessage(err, "Campanha não encontrada."));
    } finally {
      setCarregando(false);
    }
  }, [id, nova]);

  useEffect(() => {
    void carregar();
    getOpcoesPublico().then(setOpcoes).catch(() => undefined);
  }, [carregar]);

  useEffect(() => {
    if (!rascunho) return;
    const t = window.setTimeout(() => {
      previaPublico(publico).then(setResumo).catch(() => setResumo(null));
    }, 400);
    return () => window.clearTimeout(t);
  }, [publico, rascunho]);

  useEffect(() => {
    if (!campanha || campanha.status === "rascunho") return;
    listEnvios(campanha.id, filtro || undefined).then(setEnvios).catch(() => undefined);
  }, [campanha, filtro]);

  useEffect(() => {
    if (campanha?.status !== "enviando") return;
    const t = window.setInterval(() => void carregar(), 10000);
    return () => window.clearInterval(t);
  }, [campanha?.status, carregar]);

  const assoc = publico.associados;
  const setAssoc = (valor: PublicoCampanha["associados"]) => setPublico({ ...publico, associados: valor });

  const salvar = async (silencioso = false): Promise<Campanha | null> => {
    setOcupado(true);
    setErro("");
    if (!silencioso) setAviso("");
    try {
      const c = await salvarCampanha(nova ? null : id, { ...form, publico });
      setCampanha(c);
      if (!silencioso) setAviso("Rascunho salvo.");
      if (nova) navigate(`/app/newsletter/${c.id}`, { replace: true });
      return c;
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar a campanha."));
      return null;
    } finally {
      setOcupado(false);
    }
  };

  const teste = async () => {
    const email = window.prompt("Enviar o teste para qual e-mail?", user?.email ?? "");
    if (!email) return;
    const c = await salvar(true);
    if (!c) return;
    setOcupado(true);
    try {
      const r = await enviarTeste(c.id, email);
      setAviso(`Teste enviado para ${r.enviado_para}.`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar o teste."));
    } finally {
      setOcupado(false);
    }
  };

  const enviar = async () => {
    const total = resumo?.total ?? 0;
    if (!total) {
      setErro("Nenhum destinatário no público escolhido.");
      return;
    }
    if (!window.confirm(`Enviar “${form.assunto}” para ${total} pessoa(s)? Depois de enviada, a campanha não pode ser editada.`)) return;
    const c = await salvar(true);
    if (!c) return;
    setOcupado(true);
    try {
      const r = await enviarCampanha(c.id);
      setCampanha(r);
      setAviso(`${r.enfileirados} e-mail(s) na fila. O envio é gradual e esta página se atualiza sozinha.`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar a campanha."));
    } finally {
      setOcupado(false);
    }
  };

  const cancelar = async () => {
    if (!campanha || !window.confirm("Interromper o envio? Quem ainda está na fila não receberá.")) return;
    setOcupado(true);
    try {
      const r = await cancelarCampanha(campanha.id);
      setCampanha(r);
      setAviso(`Envio interrompido. ${r.cancelados} e-mail(s) saíram da fila.`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao cancelar."));
    } finally {
      setOcupado(false);
    }
  };

  const duplicar = async () => {
    if (!campanha) return;
    const c = await duplicarCampanha(campanha.id);
    navigate(`/app/newsletter/${c.id}`);
  };

  const excluir = async () => {
    if (!campanha || !window.confirm("Excluir este rascunho?")) return;
    await deleteCampanha(campanha.id);
    navigate("/app/newsletter");
  };

  const corpoPrevia = useMemo(() => {
    const primeiro = (user?.first_name || "Maria").split(" ")[0];
    return form.corpo.split("{nome}").join(primeiro);
  }, [form.corpo, user?.first_name]);

  if (carregando) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  if (!nova && !campanha) {
    return (
      <div className="dashboard-page">
        <div className="alert-banner alert-banner-error">{erro || "Campanha não encontrada."}</div>
      </div>
    );
  }

  const st = campanha ? STATUS_CAMPANHA[campanha.status] : STATUS_CAMPANHA.rascunho;
  const e = campanha?.estatisticas;
  const processados = e ? e.enviado + e.falha + e.cancelado : 0;

  return (
    <div className="dashboard-page">
      <Link to="/app/newsletter" className="dashboard-back-link" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Newsletter
      </Link>
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title" style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            {nova ? "Nova campanha" : campanha?.assunto}
            <span className={`status-badge status-badge-${st.badge}`}>{st.label}</span>
          </h1>
          <p className="dashboard-subtitle">
            {rascunho
              ? "Escreva, escolha o público, envie um teste para você e depois dispare."
              : `${descreverPublico(publico, opcoes)} · enviada em ${dataHora(campanha?.enviada_em ?? null)}`}
          </p>
        </div>
        {editavel && (
          <div className="dashboard-header-actions">
            {rascunho ? (
              <>
                {campanha && (
                  <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void excluir()} title="Excluir rascunho">
                    <Trash2 size={16} />
                  </button>
                )}
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado || !form.assunto} onClick={() => void salvar()}>
                  <Save size={16} /> Salvar
                </button>
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado || !form.assunto} onClick={() => void teste()}>
                  <FlaskConical size={16} /> Enviar teste
                </button>
                <button type="button" className="dashboard-btn-new" disabled={ocupado || !form.assunto || !form.corpo.trim()} onClick={() => void enviar()}>
                  <Send size={16} /> Enviar{resumo ? ` para ${resumo.total}` : ""}
                </button>
              </>
            ) : (
              <>
                {campanha?.status === "enviando" && (
                  <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void cancelar()}>
                    <X size={16} /> Interromper envio
                  </button>
                )}
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void duplicar()}>
                  <Copy size={16} /> Duplicar
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {aviso && <div className="highlight-banner">{aviso}</div>}

      {!rascunho && e && (
        <>
          <div className="nl-stats">
            <div className="nl-stat"><span>Destinatários</span><strong>{e.total}</strong></div>
            <div className="nl-stat"><span>Enviados</span><strong>{e.enviado}</strong></div>
            <div className="nl-stat"><span>Na fila</span><strong>{e.pendente}</strong></div>
            <div className="nl-stat"><span>Falhas</span><strong>{e.falha}</strong></div>
            <div className="nl-stat"><span>Descadastros</span><strong>{e.descadastros}</strong></div>
          </div>
          <div className="nl-progress" title={`${processados} de ${e.total}`}>
            <div style={{ width: `${e.total ? (100 * processados) / e.total : 0}%` }} />
          </div>
        </>
      )}

      <div className="nl-grid">
        <div>
          <div className="dashboard-content-panel page-form" style={{ marginBottom: "1.25rem" }}>
            <h2 className="nl-section-title">Mensagem</h2>
            <div className="form-group">
              <label className="form-label">Assunto</label>
              <input className="form-input" maxLength={200} disabled={!podeMexer} value={form.assunto} onChange={(ev) => setForm({ ...form, assunto: ev.target.value })} placeholder="Boletim de outubro: inscrições abertas para o congresso" />
            </div>
            <div className="form-group">
              <label className="form-label">Texto</label>
              <textarea className="form-input" rows={10} disabled={!podeMexer} value={form.corpo} onChange={(ev) => setForm({ ...form, corpo: ev.target.value })} />
              <p className="nl-fonte-hint">Use {"{nome}"} para o primeiro nome de quem recebe. Endereços com https:// viram links.</p>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Link do botão (opcional)</label>
                <input className="form-input" type="url" disabled={!podeMexer} value={form.link} onChange={(ev) => setForm({ ...form, link: ev.target.value })} placeholder="https://" />
              </div>
              <div className="form-group">
                <label className="form-label">Texto do botão</label>
                <input className="form-input" maxLength={60} disabled={!podeMexer || !form.link} value={form.link_label} onChange={(ev) => setForm({ ...form, link_label: ev.target.value })} placeholder="Saiba mais" />
              </div>
            </div>
          </div>

          <div className="dashboard-content-panel">
            <h2 className="nl-section-title">Público</h2>
            <div className="nl-fonte">
              <label className="nl-fonte-head">
                <input type="checkbox" disabled={!podeMexer} checked={!!assoc} onChange={() => setAssoc(assoc ? undefined : { situacoes: ["em_dia", "pendente"], tipos: [] })} />
                Associados
              </label>
              {assoc && (
                <>
                  <div className="nl-chips">
                    {(Object.keys(SITUACAO_LABEL) as SituacaoPublico[]).map((s) => (
                      <Chip key={s} on={assoc.situacoes.includes(s)} label={SITUACAO_LABEL[s]} disabled={!podeMexer} onClick={() => setAssoc({ ...assoc, situacoes: alternar(assoc.situacoes, s) })} />
                    ))}
                  </div>
                  <div className="nl-chips" style={{ marginTop: "0.5rem" }}>
                    {(Object.keys(TIPO_LABEL) as TipoFiliacao[]).map((t) => (
                      <Chip key={t} on={assoc.tipos.includes(t)} label={TIPO_LABEL[t]} disabled={!podeMexer} onClick={() => setAssoc({ ...assoc, tipos: alternar(assoc.tipos, t) })} />
                    ))}
                  </div>
                  <p className="nl-fonte-hint">Sem categoria marcada, vale para todas. Sem situação marcada, vale para todas.</p>
                </>
              )}
            </div>

            <div className="nl-fonte">
              <div className="nl-fonte-head">Inscritos em eventos</div>
              {opcoes.eventos.length === 0 ? (
                <p className="nl-fonte-hint">Nenhum evento cadastrado.</p>
              ) : (
                <div className="nl-chips">
                  {opcoes.eventos.map((ev) => (
                    <Chip key={ev.id} on={!!publico.eventos?.includes(ev.id)} label={ev.titulo} disabled={!podeMexer} onClick={() => setPublico({ ...publico, eventos: alternar(publico.eventos ?? [], ev.id) })} />
                  ))}
                </div>
              )}
            </div>

            <div className="nl-fonte" style={{ marginBottom: 0 }}>
              <div className="nl-fonte-head">Contatos por etiqueta</div>
              {opcoes.etiquetas.length === 0 ? (
                <p className="nl-fonte-hint">Nenhuma etiqueta em Contatos.</p>
              ) : (
                <div className="nl-chips">
                  {opcoes.etiquetas.map((et) => (
                    <Chip key={et.id} on={!!publico.etiquetas?.includes(et.id)} label={et.nome} disabled={!podeMexer} onClick={() => setPublico({ ...publico, etiquetas: alternar(publico.etiquetas ?? [], et.id) })} />
                  ))}
                </div>
              )}
              <p className="nl-fonte-hint">Só entram contatos que deram consentimento (LGPD) no formulário do site.</p>
            </div>
          </div>
        </div>

        <div>
          {rascunho && (
            <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
              <h2 className="nl-section-title">Quem vai receber</h2>
              {resumo ? (
                <>
                  <div className="nl-total">
                    <strong>{resumo.total}</strong> pessoa(s)
                  </div>
                  <p className="nl-fonte-hint">
                    {resumo.por_origem.associados} associado(s) · {resumo.por_origem.eventos} inscrito(s) · {resumo.por_origem.contatos} contato(s)
                    {resumo.descadastrados > 0 && ` · ${resumo.descadastrados} descadastrado(s) ficam de fora`}
                  </p>
                  {resumo.amostra.length > 0 && (
                    <ul className="nl-amostra">
                      {resumo.amostra.map((d) => (
                        <li key={d.email}>
                          {d.nome || d.email} <span style={{ color: "#98a2b3" }}>· {ORIGEM_LABEL[d.origem]}</span>
                        </li>
                      ))}
                      {resumo.total > resumo.amostra.length && <li>… e mais {resumo.total - resumo.amostra.length}</li>}
                    </ul>
                  )}
                </>
              ) : (
                <p className="nl-fonte-hint">Calculando…</p>
              )}
            </div>
          )}

          <div className="nl-preview">
            <div className="nl-preview-head">
              Pré-visualização
              <strong>{form.assunto || "(sem assunto)"}</strong>
            </div>
            <div className="nl-preview-body">
              {corpoPrevia}
              {form.link && (
                <div>
                  <span className="nl-preview-btn">{form.link_label || "Saiba mais"}</span>
                </div>
              )}
              <div className="nl-preview-footer">
                Você recebe este e-mail por seu vínculo com a associação. <u>Não quero mais receber</u>.
              </div>
            </div>
          </div>

          {!rascunho && (
            <div className="dashboard-content-panel" style={{ marginTop: "1.25rem" }}>
              <h2 className="nl-section-title">Envios</h2>
              <div className="dashboard-tabs">
                {([["", "Todos"], ["enviado", "Enviados"], ["pendente", "Na fila"], ["falha", "Falhas"], ["cancelado", "Cancelados"]] as const).map(([valor, label]) => (
                  <button key={valor} type="button" className={`dashboard-tab${filtro === valor ? " active" : ""}`} onClick={() => setFiltro(valor)}>
                    {label}
                  </button>
                ))}
              </div>
              {envios.length === 0 ? (
                <div className="dashboard-empty">Nada aqui.</div>
              ) : (
                <ul className="nl-amostra">
                  {envios.map((en) => (
                    <li key={en.id} title={en.erro || undefined}>
                      {en.nome || en.email} <span style={{ color: "#98a2b3" }}>· {en.email} · {STATUS_ENVIO[en.status]}</span>
                      {en.erro && <span style={{ color: "#b42318" }}> · {en.erro}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
