import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, MessageSquare, Plus, Search, Tag, Trash2, UserCheck, X } from "lucide-react";
import {
  createContato,
  createEtiqueta,
  deleteEtiqueta,
  getResumoFunil,
  listContatos,
  listEtiquetas,
} from "@/services/contatos";
import { apiErrorMessage } from "@/utils/apiError";
import {
  ASSUNTO_LABEL,
  ETAPA_BADGE,
  ETAPA_LABEL,
  ETAPAS,
  ORIGEM_LABEL,
  type Contato,
  type ContatoEtapa,
  type ContatoOrigem,
  type Etiqueta,
  type ResumoFunil,
} from "@/types/contatos";
import "@/components/contatos/Contatos.css";

const CORES = ["#1a5f4a", "#2563eb", "#7c3aed", "#db2777", "#ea580c", "#ca8a04", "#64748b"];

function formatData(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

export default function Contatos() {
  const navigate = useNavigate();
  const [contatos, setContatos] = useState<Contato[]>([]);
  const [resumo, setResumo] = useState<ResumoFunil | null>(null);
  const [etiquetas, setEtiquetas] = useState<Etiqueta[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [etapa, setEtapa] = useState<ContatoEtapa | "abertos" | "">("abertos");
  const [origem, setOrigem] = useState<ContatoOrigem | "">("");
  const [etiqueta, setEtiqueta] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [novo, setNovo] = useState({ nome: "", email: "", telefone: "", instituicao: "", mensagem: "", origem: "manual" });
  const [salvando, setSalvando] = useState(false);
  const [showTags, setShowTags] = useState(false);
  const [novaTag, setNovaTag] = useState({ nome: "", cor: CORES[0] });

  const load = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const [lista, funil] = await Promise.all([
        listContatos({
          search: busca || undefined,
          etapa: etapa && etapa !== "abertos" ? etapa : undefined,
          abertos: etapa === "abertos",
          origem: origem || undefined,
          etiqueta: etiqueta || undefined,
        }),
        getResumoFunil(),
      ]);
      setContatos(lista);
      setResumo(funil);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar contatos."));
    } finally {
      setLoading(false);
    }
  }, [busca, etapa, origem, etiqueta]);

  const loadEtiquetas = useCallback(async () => {
    try {
      setEtiquetas(await listEtiquetas());
    } catch {
      /* lista de etiquetas é opcional para a página */
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), busca ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, busca]);

  useEffect(() => {
    void loadEtiquetas();
  }, [loadEtiquetas]);

  const abertos = resumo ? resumo.novo + resumo.em_atendimento + resumo.interessado : 0;

  const criar = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    try {
      const c = await createContato(novo as Partial<Contato>);
      navigate(`/app/contatos/${c.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao cadastrar contato."));
      setSalvando(false);
    }
  };

  const criarTag = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createEtiqueta(novaTag);
      setNovaTag({ nome: "", cor: CORES[0] });
      await loadEtiquetas();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar etiqueta."));
    }
  };

  const excluirTag = async (t: Etiqueta) => {
    if (!window.confirm(`Excluir a etiqueta "${t.nome}"? Ela será removida de ${t.contatos_count ?? 0} contato(s).`)) return;
    try {
      await deleteEtiqueta(t.id);
      if (etiqueta === String(t.id)) setEtiqueta("");
      await loadEtiquetas();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir etiqueta."));
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Contatos</h1>
          <p className="dashboard-subtitle">Mensagens do site, interessados em filiação, imprensa e parceiros</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-secondary" onClick={() => setShowTags(true)}>
            <Tag size={16} /> Etiquetas
          </button>
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
            <Plus size={16} /> Novo contato
          </button>
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      {showForm && (
        <div className="page-form-container">
          <form className="page-form" onSubmit={criar}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Nome *</label>
                <input className="form-input" required autoFocus value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label">E-mail *</label>
                <input className="form-input" type="email" required value={novo.email} onChange={(e) => setNovo({ ...novo, email: e.target.value })} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Telefone</label>
                <input className="form-input" value={novo.telefone} onChange={(e) => setNovo({ ...novo, telefone: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label">Instituição</label>
                <input className="form-input" value={novo.instituicao} onChange={(e) => setNovo({ ...novo, instituicao: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label">Origem</label>
                <select className="form-select" value={novo.origem} onChange={(e) => setNovo({ ...novo, origem: e.target.value })}>
                  {Object.entries(ORIGEM_LABEL)
                    .filter(([v]) => !v.startsWith("site_"))
                    .map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Observação inicial</label>
              <textarea className="form-input" rows={3} value={novo.mensagem} onChange={(e) => setNovo({ ...novo, mensagem: e.target.value })} />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Salvando..." : "Cadastrar"}
              </button>
            </div>
          </form>
        </div>
      )}

      {resumo && (
        <div className="funil-row">
          <button
            type="button"
            className={`funil-card ${etapa === "abertos" ? "funil-card-active" : ""}`}
            onClick={() => setEtapa("abertos")}
          >
            <div className="funil-card-value">{abertos}</div>
            <div className="funil-card-label">Em aberto</div>
          </button>
          {ETAPAS.map((e) => (
            <button
              key={e.value}
              type="button"
              className={`funil-card ${etapa === e.value ? "funil-card-active" : ""}`}
              onClick={() => setEtapa(e.value)}
            >
              <div className="funil-card-value">{resumo[e.value]}</div>
              <div className="funil-card-label">{e.label}</div>
            </button>
          ))}
          <button type="button" className={`funil-card ${etapa === "" ? "funil-card-active" : ""}`} onClick={() => setEtapa("")}>
            <div className="funil-card-value">{Object.values(resumo).reduce((a, b) => a + b, 0)}</div>
            <div className="funil-card-label">Todos</div>
          </button>
        </div>
      )}

      <div className="filters-row">
        <div style={{ position: "relative", flex: 1, minWidth: "12rem" }}>
          <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "0.7rem", color: "#a0a0a0" }} />
          <input
            className="form-input"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por nome, e-mail, instituição ou mensagem..."
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
        <select className="form-select" value={origem} onChange={(e) => setOrigem(e.target.value as ContatoOrigem | "")}>
          <option value="">Todas as origens</option>
          {Object.entries(ORIGEM_LABEL).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
        {etiquetas.length > 0 && (
          <select className="form-select" value={etiqueta} onChange={(e) => setEtiqueta(e.target.value)}>
            <option value="">Todas as etiquetas</option>
            {etiquetas.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        )}
      </div>

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : contatos.length === 0 ? (
        <div className="dashboard-empty">
          Nenhum contato nesta visão. As mensagens enviadas pelo formulário do site aparecem aqui.
        </div>
      ) : (
        <div className="list-stack">
          {contatos.map((c) => (
            <Link
              key={c.id}
              to={`/app/contatos/${c.id}`}
              className="list-card"
              style={{ display: "flex", gap: "1rem", alignItems: "center", color: "inherit", textDecoration: "none" }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="list-card-title" style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                  {c.nome}
                  {c.membro && (
                    <span title={`Associado: ${c.membro_nome}`} style={{ color: "#067647", display: "inline-flex" }}>
                      <UserCheck size={15} />
                    </span>
                  )}
                  {c.etiquetas.map((t) => (
                    <span key={t.id} className="etiqueta-chip" style={{ background: t.cor }}>
                      {t.nome}
                    </span>
                  ))}
                </div>
                <div className="list-card-meta" style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                  <span>{c.email}</span>
                  <span>{ASSUNTO_LABEL[c.assunto]}</span>
                  <span>{ORIGEM_LABEL[c.origem]}</span>
                  <span>Última interação: {formatData(c.ultima_interacao_em || c.created_at)}</span>
                  {!!c.notas_count && (
                    <span>
                      <MessageSquare size={13} /> {c.notas_count}
                    </span>
                  )}
                </div>
                {c.mensagem && (
                  <div className="list-card-meta" style={{ marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    “{c.mensagem}”
                  </div>
                )}
              </div>
              <span className={`status-badge status-badge-${ETAPA_BADGE[c.etapa]}`}>{ETAPA_LABEL[c.etapa]}</span>
            </Link>
          ))}
        </div>
      )}

      {showTags && (
        <div className="dashboard-modal-overlay" onClick={() => setShowTags(false)}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">Etiquetas</h2>
              <button type="button" className="dashboard-modal-close" onClick={() => setShowTags(false)} aria-label="Fechar">
                <X size={18} />
              </button>
            </div>
            <div className="dashboard-modal-content page-form">
            <p className="dashboard-subtitle" style={{ marginTop: 0 }}>
              Use etiquetas para segmentar contatos (ex.: “Congresso 2026”, “Imprensa”, “Patrocinador”).
            </p>
            {etiquetas.length === 0 ? (
              <p className="list-card-meta">Nenhuma etiqueta criada.</p>
            ) : (
              <div className="list-stack" style={{ marginBottom: "1rem" }}>
                {etiquetas.map((t) => (
                  <div key={t.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span className="etiqueta-chip" style={{ background: t.cor }}>
                      {t.nome}
                    </span>
                    <span className="list-card-meta" style={{ flex: 1 }}>
                      {t.contatos_count ?? 0} contato(s)
                    </span>
                    <button type="button" className="ct-icon-btn" title="Excluir" onClick={() => excluirTag(t)}>
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <form onSubmit={criarTag} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <input
                className="form-input"
                placeholder="Nova etiqueta"
                maxLength={50}
                value={novaTag.nome}
                onChange={(e) => setNovaTag({ ...novaTag, nome: e.target.value })}
                style={{ flex: 1 }}
              />
              <div style={{ display: "flex", gap: 4 }}>
                {CORES.map((cor) => (
                  <button
                    key={cor}
                    type="button"
                    aria-label={`Cor ${cor}`}
                    onClick={() => setNovaTag({ ...novaTag, cor })}
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      background: cor,
                      border: novaTag.cor === cor ? "2px solid #0f172a" : "2px solid transparent",
                      cursor: "pointer",
                      padding: 0,
                    }}
                  />
                ))}
              </div>
              <button type="submit" className="dashboard-btn-new" disabled={!novaTag.nome.trim()}>
                Criar
              </button>
            </form>
            </div>
            <div className="dashboard-modal-footer">
              <button type="button" className="dashboard-btn-secondary" onClick={() => setShowTags(false)}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
