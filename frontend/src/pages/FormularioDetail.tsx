import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Copy, Download, ExternalLink, Trash2 } from "lucide-react";
import FormBuilder from "@/components/formularios/FormBuilder";
import ResultadosResumo from "@/components/formularios/ResultadosResumo";
import { useAuth } from "@/contexts/AuthContext";
import { listEventos } from "@/services/eventos";
import { listMembros } from "@/services/membros";
import {
  convidar,
  excluirResposta,
  exportarCsv,
  getFormulario,
  getResumo,
  listConvites,
  listRespostas,
  updateFormulario,
} from "@/services/formularios";
import { apiErrorMessage } from "@/utils/apiError";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import type { Membro } from "@/types/membros";
import type {
  Formulario,
  FormularioStatus,
  RespostaItem,
  ResumoFormulario,
  Secao,
  ValorResposta,
} from "@/types/formularios";
import { FORMULARIO_STATUS_BADGE, RESPOSTA_STATUS_BADGE } from "@/types/formularios";
import "@/components/formularios/Formularios.css";

type Tab = "perguntas" | "config" | "distribuicao" | "respostas";

const formatDateTime = (value: string | null) => (value ? new Date(value).toLocaleString("pt-BR") : "—");

function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const mostrarValor = (v: ValorResposta | undefined) => (Array.isArray(v) ? v.join(", ") : v || "");

async function copiar(texto: string, onDone: (msg: string) => void) {
  try {
    await navigator.clipboard.writeText(texto);
    onDone("Link copiado.");
  } catch {
    window.prompt("Copie o link:", texto);
  }
}

// ---------------------------------------------------------------- Configurações

function ConfigForm({ formulario, onSaved }: { formulario: Formulario; onSaved: (f: Formulario) => void }) {
  const [form, setForm] = useState({
    titulo: formulario.titulo,
    descricao: formulario.descricao,
    mensagem_confirmacao: formulario.mensagem_confirmacao,
    evento: formulario.evento || "",
    encerra_em: toLocalInput(formulario.encerra_em),
  });
  const [eventos, setEventos] = useState<{ id: string; titulo: string }[]>([]);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    listEventos()
      .then((evs) => setEventos(evs.map((e) => ({ id: e.id, titulo: e.titulo }))))
      .catch(() => setEventos([]));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setMsg("");
    setSalvando(true);
    try {
      const saved = await updateFormulario(formulario.id, {
        titulo: form.titulo,
        descricao: form.descricao,
        mensagem_confirmacao: form.mensagem_confirmacao,
        evento: form.evento || null,
        encerra_em: form.encerra_em ? new Date(form.encerra_em).toISOString() : null,
      });
      onSaved(saved);
      setMsg("Configurações salvas.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar."));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="page-form-container">
      <form className="page-form" onSubmit={handleSubmit}>
        {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
        {msg && <div className="alert-banner alert-banner-success">{msg}</div>}
        <div className="form-group">
          <label className="form-label">Título *</label>
          <input className="form-input" required maxLength={200} value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">Descrição / instruções</label>
          <textarea className="form-input" rows={3} value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
        </div>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Evento avaliado</label>
            <select className="form-select" value={form.evento} onChange={(e) => setForm({ ...form, evento: e.target.value })}>
              <option value="">Nenhum</option>
              {eventos.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.titulo}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Encerrar automaticamente em</label>
            <input
              className="form-input"
              type="datetime-local"
              value={form.encerra_em}
              onChange={(e) => setForm({ ...form, encerra_em: e.target.value })}
            />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Mensagem após o envio</label>
          <textarea
            className="form-input"
            rows={2}
            value={form.mensagem_confirmacao}
            placeholder="Obrigado pela sua participação!"
            onChange={(e) => setForm({ ...form, mensagem_confirmacao: e.target.value })}
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="dashboard-btn-save" disabled={salvando}>
            {salvando ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------- Distribuição

function Distribuicao({ formulario, onSaved }: { formulario: Formulario; onSaved: (f: Formulario) => void }) {
  const { tenantSchema } = useAuth();
  const [convites, setConvites] = useState<RespostaItem[]>([]);
  const [busca, setBusca] = useState("");
  const [resultados, setResultados] = useState<Membro[]>([]);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const q = buildTenantSiteQuery(tenantSchema || "");
  const linkPublico = `${window.location.origin}/site/formularios/${formulario.public_token}${q}`;

  const loadConvites = useCallback(() => {
    listConvites(formulario.id).then(setConvites).catch(() => setConvites([]));
  }, [formulario.id]);

  useEffect(() => {
    loadConvites();
  }, [loadConvites]);

  const alternar = async (campo: "link_publico_ativo" | "disponivel_no_portal" | "pedir_identificacao", valor: boolean) => {
    setErro("");
    try {
      onSaved(await updateFormulario(formulario.id, { [campo]: valor }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar."));
    }
  };

  const convidarMembros = async (payload: { membros?: string[]; todos_ativos?: boolean; reenviar_pendentes?: boolean }) => {
    setErro("");
    setMsg("");
    try {
      const r = await convidar(formulario.id, payload);
      const partes = payload.reenviar_pendentes
        ? []
        : [`${r.criados} convite(s) criado(s)${r.existentes ? `; ${r.existentes} já existiam` : ""}`];
      if (formulario.status === "publicado") partes.push(`${r.emails_enviados} e-mail(s) enviado(s)`);
      else partes.push("e-mails serão enviados quando você usar “Reenviar e-mail aos pendentes” após publicar");
      setMsg(`${partes.join(" · ")}.`);
      setResultados([]);
      setBusca("");
      loadConvites();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao convidar."));
    }
  };

  const buscar = async () => {
    if (!busca.trim()) return;
    try {
      const convidados = new Set(convites.map((c) => c.membro));
      const found = await listMembros({ q: busca.trim(), ativo: true });
      setResultados(found.filter((m) => !convidados.has(m.id)).slice(0, 10));
      if (!found.length) setMsg("Nenhum associado encontrado.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao buscar associados."));
    }
  };

  return (
    <div>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}
      {formulario.status !== "publicado" && (
        <div className="highlight-banner" style={{ marginBottom: "1rem" }}>
          <div className="highlight-banner-meta">
            {formulario.status === "rascunho"
              ? "O formulário está em rascunho: publique para começar a receber respostas."
              : "O formulário está encerrado e não recebe novas respostas."}
          </div>
        </div>
      )}

      <div className="page-form-container">
        <div className="page-form">
          <h3 className="page-form-title" style={{ fontSize: "1.1rem" }}>Link público</h3>
          <label className="inline-check">
            <input type="checkbox" checked={formulario.link_publico_ativo} onChange={(e) => alternar("link_publico_ativo", e.target.checked)} />
            <span>Qualquer pessoa com o link pode responder (ex.: participantes de um evento)</span>
          </label>
          {formulario.link_publico_ativo && (
            <>
              <label className="inline-check">
                <input
                  type="checkbox"
                  checked={formulario.pedir_identificacao}
                  onChange={(e) => alternar("pedir_identificacao", e.target.checked)}
                />
                <span>Pedir nome e e-mail (desmarque para respostas anônimas)</span>
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input className="form-input" readOnly value={linkPublico} onFocus={(e) => e.target.select()} />
                <button type="button" className="dashboard-btn-secondary" onClick={() => copiar(linkPublico, setMsg)}>
                  <Copy size={14} /> Copiar
                </button>
                <a className="dashboard-btn-secondary" href={linkPublico} target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={14} /> Abrir
                </a>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="page-form-container">
        <div className="page-form">
          <h3 className="page-form-title" style={{ fontSize: "1.1rem" }}>Associados</h3>
          <label className="inline-check">
            <input type="checkbox" checked={formulario.disponivel_no_portal} onChange={(e) => alternar("disponivel_no_portal", e.target.checked)} />
            <span>Disponível para todos os associados no portal (uma resposta por associado)</span>
          </label>
          <div className="form-group">
            <label className="form-label">Convidar associados específicos</label>
            <p className="form-help-text">
              O associado recebe o link pessoal por e-mail (com o formulário publicado) e também vê o convite em “Formulários”
              no portal.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <input
                className="form-input"
                style={{ flex: 1, minWidth: 200 }}
                value={busca}
                placeholder="Buscar por nome, e-mail ou CPF"
                onChange={(e) => setBusca(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void buscar();
                  }
                }}
              />
              <button type="button" className="dashboard-btn-secondary" onClick={buscar}>
                Buscar
              </button>
              <button
                type="button"
                className="dashboard-btn-secondary"
                onClick={() => window.confirm("Convidar todos os associados ativos?") && convidarMembros({ todos_ativos: true })}
              >
                Convidar todos os ativos
              </button>
              {convites.some((c) => c.status !== "enviada") && formulario.status === "publicado" && (
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  onClick={() =>
                    window.confirm("Reenviar o e-mail de convite a todos que ainda não responderam?") &&
                    convidarMembros({ reenviar_pendentes: true })
                  }
                >
                  Reenviar e-mail aos pendentes
                </button>
              )}
            </div>
          </div>
          {resultados.length > 0 && (
            <div className="list-stack">
              {resultados.map((m) => (
                <div key={m.id} className="list-card" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <div style={{ flex: 1 }}>
                    <div className="list-card-title">{m.nome_completo}</div>
                    <div className="list-card-meta">{m.email}</div>
                  </div>
                  <button type="button" className="btn-action-confirm" onClick={() => convidarMembros({ membros: [m.id] })}>
                    Convidar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {convites.length > 0 && (
        <div className="fres-table-wrap">
          <table className="fres-table">
            <thead>
              <tr>
                <th>Associado</th>
                <th>Situação</th>
                <th>Enviada em</th>
                <th>Link pessoal</th>
              </tr>
            </thead>
            <tbody>
              {convites.map((c) => {
                const link = `${window.location.origin}/site/formularios/convite/${c.token}${q}`;
                return (
                  <tr key={c.id}>
                    <td>
                      <div>{c.nome}</div>
                      <div className="fb-muted">{c.email}</div>
                    </td>
                    <td>
                      <span className={`status-badge status-badge-${RESPOSTA_STATUS_BADGE[c.status]}`}>{c.status_display}</span>
                    </td>
                    <td>{formatDateTime(c.enviada_em)}</td>
                    <td>
                      <button type="button" className="fb-icon-btn" title="Copiar link pessoal" onClick={() => copiar(link, setMsg)}>
                        <Copy size={15} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Respostas

function Respostas({ formulario }: { formulario: Formulario }) {
  const [modo, setModo] = useState<"resumo" | "individuais">("resumo");
  const [resumo, setResumo] = useState<ResumoFormulario | null>(null);
  const [respostas, setRespostas] = useState<RespostaItem[] | null>(null);
  const [erro, setErro] = useState("");
  const perguntas = formulario.secoes.flatMap((s) => s.perguntas);

  const load = useCallback(() => {
    getResumo(formulario.id).then(setResumo).catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar.")));
    listRespostas(formulario.id).then(setRespostas).catch(() => setRespostas([]));
  }, [formulario.id]);

  useEffect(() => {
    load();
  }, [load]);

  const excluir = async (r: RespostaItem) => {
    if (!window.confirm(`Excluir a resposta de ${r.nome || "anônimo"}?`)) return;
    try {
      await excluirResposta(formulario.id, r.id);
      load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
  };

  return (
    <div>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      <div className="filters-row" style={{ justifyContent: "space-between" }}>
        <div className="dashboard-tabs" style={{ margin: 0 }}>
          <button type="button" className={`dashboard-tab${modo === "resumo" ? " active" : ""}`} onClick={() => setModo("resumo")}>
            Resumo
          </button>
          <button type="button" className={`dashboard-tab${modo === "individuais" ? " active" : ""}`} onClick={() => setModo("individuais")}>
            Individuais{respostas ? ` (${respostas.length})` : ""}
          </button>
        </div>
        <button
          type="button"
          className="dashboard-btn-secondary"
          disabled={!respostas?.length}
          onClick={() => exportarCsv(formulario.id, formulario.titulo).catch((err) => setErro(apiErrorMessage(err, "Erro ao exportar.")))}
        >
          <Download size={15} /> Exportar CSV
        </button>
      </div>

      {modo === "resumo" ? (
        resumo ? (
          <ResultadosResumo resumo={resumo} />
        ) : (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
          </div>
        )
      ) : !respostas ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      ) : respostas.length === 0 ? (
        <div className="dashboard-empty">Nenhuma resposta enviada ainda.</div>
      ) : (
        <div className="fres-table-wrap">
          <table className="fres-table">
            <thead>
              <tr>
                <th>Enviada em</th>
                <th>Quem respondeu</th>
                <th>Origem</th>
                {perguntas.map((p) => (
                  <th key={p.id} title={p.texto}>
                    {p.texto.length > 40 ? `${p.texto.slice(0, 40)}…` : p.texto}
                  </th>
                ))}
                <th />
              </tr>
            </thead>
            <tbody>
              {respostas.map((r) => (
                <tr key={r.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{formatDateTime(r.enviada_em)}</td>
                  <td>
                    <div>{r.nome || "Anônimo"}</div>
                    {r.email && <div className="fb-muted">{r.email}</div>}
                  </td>
                  <td>{r.origem_display}</td>
                  {perguntas.map((p) => (
                    <td key={p.id} style={{ whiteSpace: "pre-wrap" }}>
                      {mostrarValor(p.id ? r.valores?.[p.id] : undefined)}
                    </td>
                  ))}
                  <td>
                    <button type="button" className="fb-icon-btn" title="Excluir resposta" onClick={() => excluir(r)}>
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Página

export default function FormularioDetail() {
  const { id = "" } = useParams();
  const [formulario, setFormulario] = useState<Formulario | null>(null);
  const [secoes, setSecoes] = useState<Secao[]>([]);
  const [alterado, setAlterado] = useState(false);
  const [tab, setTab] = useState<Tab>("perguntas");
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [salvando, setSalvando] = useState(false);

  const aplicar = (f: Formulario) => {
    setFormulario(f);
    setSecoes(JSON.parse(JSON.stringify(f.secoes)));
    setAlterado(false);
  };

  useEffect(() => {
    getFormulario(id)
      .then(aplicar)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar o formulário.")));
  }, [id]);

  useEffect(() => {
    if (!alterado) return;
    const aviso = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", aviso);
    return () => window.removeEventListener("beforeunload", aviso);
  }, [alterado]);

  if (!formulario) {
    return (
      <div className="dashboard-page">
        {erro ? (
          <div className="alert-banner alert-banner-error">{erro}</div>
        ) : (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
          </div>
        )}
      </div>
    );
  }

  const salvarPerguntas = async () => {
    setErro("");
    setMsg("");
    const vazias = secoes.some((s) => s.perguntas.some((p) => !p.texto.trim()));
    if (vazias) {
      setErro("Preencha o texto de todas as perguntas (ou remova as vazias).");
      return;
    }
    setSalvando(true);
    try {
      aplicar(await updateFormulario(formulario.id, { secoes }));
      setMsg("Perguntas salvas.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar as perguntas."));
    } finally {
      setSalvando(false);
    }
  };

  const mudarStatus = async (status: FormularioStatus) => {
    setErro("");
    setMsg("");
    if (alterado) {
      setErro("Salve as perguntas antes de mudar o status.");
      return;
    }
    try {
      aplicar(await updateFormulario(formulario.id, { status }));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao mudar o status."));
    }
  };

  const trocarAba = (nova: Tab) => {
    if (alterado && nova !== "perguntas" && !window.confirm("Há alterações não salvas nas perguntas. Descartar?")) return;
    if (alterado && nova !== "perguntas") aplicar(formulario);
    setTab(nova);
  };

  return (
    <div className="dashboard-page">
      <Link to="/app/formularios" className="fb-muted" style={{ display: "inline-flex", gap: "0.25rem" }}>
        <ArrowLeft size={14} /> Formulários
      </Link>

      <div className="dashboard-header dashboard-header-row" style={{ marginTop: "0.5rem" }}>
        <div>
          <h1 className="dashboard-title">
            {formulario.titulo}{" "}
            <span className={`status-badge status-badge-${FORMULARIO_STATUS_BADGE[formulario.status]}`}>{formulario.status_display}</span>
          </h1>
          <p className="dashboard-subtitle">
            {formulario.evento_titulo ? `Evento: ${formulario.evento_titulo}` : "Sem evento vinculado"}
            {formulario.encerra_em ? ` · encerra em ${formatDateTime(formulario.encerra_em)}` : ""}
          </p>
        </div>
        <div className="dashboard-header-actions">
          {formulario.status !== "publicado" && (
            <button type="button" className="dashboard-btn-new" onClick={() => mudarStatus("publicado")}>
              {formulario.status === "encerrado" ? "Reabrir" : "Publicar"}
            </button>
          )}
          {formulario.status === "publicado" && (
            <button type="button" className="dashboard-btn-secondary" onClick={() => mudarStatus("encerrado")}>
              Encerrar
            </button>
          )}
        </div>
      </div>

      {formulario.status === "publicado" && !formulario.link_publico_ativo && !formulario.disponivel_no_portal && (
        <div className="highlight-banner" style={{ marginBottom: "1rem" }}>
          <div className="highlight-banner-meta">
            Publicado, mas sem link público nem acesso pelo portal: só quem receber convite consegue responder. Veja a aba Distribuição.
          </div>
        </div>
      )}

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      <div className="dashboard-tabs">
        {(
          [
            ["perguntas", "Perguntas"],
            ["config", "Configurações"],
            ["distribuicao", "Distribuição"],
            ["respostas", "Respostas"],
          ] as [Tab, string][]
        ).map(([key, label]) => (
          <button key={key} type="button" className={`dashboard-tab${tab === key ? " active" : ""}`} onClick={() => trocarAba(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "perguntas" && (
        <div>
          {formulario.tem_respostas && (
            <div className="highlight-banner" style={{ marginBottom: "1rem" }}>
              <div className="highlight-banner-meta">
                Este formulário já tem respostas. Remover uma pergunta apaga as respostas dela; mudar opções pode deixar
                respostas antigas fora da lista.
              </div>
            </div>
          )}
          <FormBuilder
            secoes={secoes}
            onChange={(next) => {
              setSecoes(next);
              setAlterado(true);
            }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
            {alterado && (
              <button type="button" className="dashboard-btn-secondary" onClick={() => aplicar(formulario)}>
                Descartar alterações
              </button>
            )}
            <button type="button" className="dashboard-btn-new" disabled={!alterado || salvando} onClick={salvarPerguntas}>
              {salvando ? "Salvando..." : alterado ? "Salvar perguntas" : "Perguntas salvas"}
            </button>
          </div>
        </div>
      )}
      {tab === "config" && <ConfigForm key={formulario.id} formulario={formulario} onSaved={aplicar} />}
      {tab === "distribuicao" && <Distribuicao formulario={formulario} onSaved={aplicar} />}
      {tab === "respostas" && <Respostas formulario={formulario} />}
    </div>
  );
}
