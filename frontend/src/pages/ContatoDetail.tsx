import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Mail, Pencil, Phone, Trash2, UserCheck, UserPlus } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  addNota,
  converterContato,
  deleteContato,
  getContato,
  getFichaContato,
  listEtiquetas,
  listNotas,
  updateContato,
} from "@/services/contatos";
import { apiErrorMessage } from "@/utils/apiError";
import {
  ASSUNTO_LABEL,
  ETAPA_BADGE,
  ETAPA_LABEL,
  ETAPAS,
  ORIGEM_LABEL,
  type Contato,
  type ContatoAssunto,
  type ContatoEtapa,
  type Etiqueta,
  type FichaContato,
  type NotaContato,
} from "@/types/contatos";
import { BADGE_SITUACAO } from "@/components/membros/CartaoAssociado";
import { formatBRL } from "@/utils/tenantSite";
import "@/components/contatos/Contatos.css";
import "@/components/membros/Membros.css";

const TIPOS_FILIACAO = [
  { value: "", label: "Sem filiação por enquanto" },
  { value: "efetivo", label: "Efetivo" },
  { value: "estudante", label: "Estudante" },
  { value: "institucional", label: "Institucional" },
  { value: "honorario", label: "Honorário" },
];

function formatDataHora(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function ContatoDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [contato, setContato] = useState<Contato | null>(null);
  const [notas, setNotas] = useState<NotaContato[]>([]);
  const [etiquetas, setEtiquetas] = useState<Etiqueta[]>([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [editando, setEditando] = useState(false);
  const [form, setForm] = useState<Partial<Contato>>({});
  const [novaNota, setNovaNota] = useState("");
  const [enviandoNota, setEnviandoNota] = useState(false);
  const [showConverter, setShowConverter] = useState(false);
  const [tipoFiliacao, setTipoFiliacao] = useState("efetivo");
  const [convertendo, setConvertendo] = useState(false);

  const [ficha, setFicha] = useState<FichaContato | null>(null);

  const loadNotas = useCallback(async () => {
    setNotas(await listNotas(id));
  }, [id]);

  const loadFicha = useCallback(async () => {
    try {
      setFicha(await getFichaContato(id));
    } catch {
      setFicha(null);
    }
  }, [id]);

  useEffect(() => {
    (async () => {
      try {
        const [c, tags] = await Promise.all([getContato(id), listEtiquetas()]);
        setContato(c);
        setEtiquetas(tags);
        await loadNotas();
        void loadFicha();
      } catch (err) {
        setErro(apiErrorMessage(err, "Contato não encontrado."));
      }
    })();
  }, [id, loadNotas, loadFicha]);

  const salvar = async (payload: Partial<Contato>) => {
    setErro("");
    try {
      const atualizado = await updateContato(id, payload);
      setContato(atualizado);
      await loadNotas();
      return true;
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar."));
      return false;
    }
  };

  const toggleEtiqueta = (t: Etiqueta) => {
    if (!contato) return;
    const atuais = contato.etiquetas.map((e) => e.id);
    const ids = atuais.includes(t.id) ? atuais.filter((x) => x !== t.id) : [...atuais, t.id];
    void salvar({ etiqueta_ids: ids });
  };

  const salvarEdicao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (await salvar(form)) setEditando(false);
  };

  const enviarNota = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!novaNota.trim()) return;
    setEnviandoNota(true);
    try {
      await addNota(id, novaNota);
      setNovaNota("");
      await loadNotas();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar anotação."));
    } finally {
      setEnviandoNota(false);
    }
  };

  const converter = async () => {
    setConvertendo(true);
    setErro("");
    try {
      const r = await converterContato(id, tipoFiliacao);
      setContato(r.contato);
      setShowConverter(false);
      setAviso(r.membro_criado ? "Associado cadastrado a partir deste contato." : "Contato vinculado ao associado já existente.");
      await Promise.all([loadNotas(), loadFicha()]);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao converter."));
    } finally {
      setConvertendo(false);
    }
  };

  const excluir = async () => {
    if (!contato || !window.confirm(`Excluir o contato "${contato.nome}" e todo o histórico? Prefira arquivar.`)) return;
    try {
      await deleteContato(id);
      navigate("/app/contatos");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
  };

  if (!contato) {
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

  const ehResponsavel = !!user && contato.responsavel === user.id;

  return (
    <div className="dashboard-page">
      <Link to="/app/contatos" className="dashboard-back-link" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Contatos
      </Link>
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title" style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            {contato.nome}
            <span className={`status-badge status-badge-${ETAPA_BADGE[contato.etapa]}`}>{ETAPA_LABEL[contato.etapa]}</span>
          </h1>
          <p className="dashboard-subtitle">
            {ORIGEM_LABEL[contato.origem]} · recebido em {formatDataHora(contato.created_at)}
          </p>
        </div>
        <div className="dashboard-header-actions">
          <a className="dashboard-btn-secondary" href={`mailto:${contato.email}`}>
            <Mail size={16} /> Responder por e-mail
          </a>
          {contato.membro ? (
            <Link className="dashboard-btn-secondary" to={`/app/membros/${contato.membro}`}>
              <UserCheck size={16} /> Ver associado
            </Link>
          ) : (
            <button type="button" className="dashboard-btn-new" onClick={() => setShowConverter(true)}>
              <UserPlus size={16} /> Converter em associado
            </button>
          )}
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}
      {aviso && <div className="highlight-banner">{aviso}</div>}

      <div className="contato-grid">
        <div>
          <div className="contato-card">
            <h3>Etapa no funil</h3>
            <div className="etiquetas-wrap">
              {ETAPAS.map((e) => (
                <button
                  key={e.value}
                  type="button"
                  className={`status-badge status-badge-${e.badge}`}
                  onClick={() => contato.etapa !== e.value && void salvar({ etapa: e.value as ContatoEtapa })}
                  style={{
                    cursor: "pointer",
                    opacity: contato.etapa === e.value ? 1 : 0.45,
                    outline: contato.etapa === e.value ? "2px solid currentColor" : "none",
                  }}
                >
                  {e.label}
                </button>
              ))}
            </div>
            <div style={{ marginTop: "0.9rem", fontSize: "0.85rem", display: "flex", gap: "0.75rem", alignItems: "center" }}>
              <span style={{ color: "#667085" }}>Responsável:</span>
              <strong>{contato.responsavel_nome || "ninguém"}</strong>
              {user && !ehResponsavel && (
                <button type="button" className="dashboard-btn-secondary" onClick={() => void salvar({ responsavel: user.id })}>
                  Assumir atendimento
                </button>
              )}
            </div>
          </div>

          <div className="contato-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3>Dados do contato</h3>
              {!editando && (
                <button
                  type="button"
                  className="ct-icon-btn"
                  title="Editar"
                  onClick={() => {
                    setForm({
                      nome: contato.nome,
                      email: contato.email,
                      telefone: contato.telefone,
                      instituicao: contato.instituicao,
                      assunto: contato.assunto,
                    });
                    setEditando(true);
                  }}
                >
                  <Pencil size={15} />
                </button>
              )}
            </div>
            {editando ? (
              <form className="page-form" onSubmit={salvarEdicao}>
                <div className="form-group">
                  <label className="form-label">Nome</label>
                  <input className="form-input" required value={form.nome || ""} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">E-mail</label>
                  <input className="form-input" type="email" required value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Telefone</label>
                    <input className="form-input" value={form.telefone || ""} onChange={(e) => setForm({ ...form, telefone: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Instituição</label>
                    <input className="form-input" value={form.instituicao || ""} onChange={(e) => setForm({ ...form, instituicao: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Assunto</label>
                  <select className="form-select" value={form.assunto} onChange={(e) => setForm({ ...form, assunto: e.target.value as ContatoAssunto })}>
                    {Object.entries(ASSUNTO_LABEL).map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                  <button type="button" className="dashboard-btn-secondary" onClick={() => setEditando(false)}>
                    Cancelar
                  </button>
                  <button type="submit" className="dashboard-btn-new">
                    Salvar
                  </button>
                </div>
              </form>
            ) : (
              <>
                <dl className="contato-dl">
                  <dt>E-mail</dt>
                  <dd>
                    <a href={`mailto:${contato.email}`}>{contato.email}</a>
                  </dd>
                  <dt>Telefone</dt>
                  <dd>
                    {contato.telefone ? (
                      <a href={`tel:${contato.telefone}`} style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                        <Phone size={13} /> {contato.telefone}
                      </a>
                    ) : (
                      "—"
                    )}
                  </dd>
                  <dt>Instituição</dt>
                  <dd>{contato.instituicao || "—"}</dd>
                  <dt>Assunto</dt>
                  <dd>{ASSUNTO_LABEL[contato.assunto]}</dd>
                  <dt>Associado</dt>
                  <dd>{contato.membro_nome || "Não"}</dd>
                  <dt>LGPD</dt>
                  <dd>{contato.consentimento_lgpd ? "Consentiu no formulário" : "Sem registro de consentimento"}</dd>
                </dl>
                {contato.mensagem && <p className="contato-mensagem">{contato.mensagem}</p>}
              </>
            )}
          </div>

          <div className="contato-card">
            <h3>Etiquetas</h3>
            {etiquetas.length === 0 ? (
              <p className="list-card-meta" style={{ margin: 0 }}>
                Crie etiquetas na lista de contatos (botão “Etiquetas”).
              </p>
            ) : (
              <div className="etiquetas-wrap">
                {etiquetas.map((t) => {
                  const ativa = contato.etiquetas.some((e) => e.id === t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      className={`etiqueta-chip ${ativa ? "" : "etiqueta-chip-off"}`}
                      style={{ background: t.cor }}
                      onClick={() => toggleEtiqueta(t)}
                    >
                      {t.nome}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <button type="button" className="dashboard-btn-secondary" onClick={excluir} style={{ color: "#b42318" }}>
            <Trash2 size={15} /> Excluir contato
          </button>
        </div>

        <div className="contato-card">
          <h3>Histórico e anotações</h3>
          <form className="page-form" onSubmit={enviarNota} style={{ marginBottom: "1rem" }}>
            <textarea
              className="form-input"
              rows={3}
              placeholder="Registrar ligação, e-mail enviado, próximo passo..."
              value={novaNota}
              onChange={(e) => setNovaNota(e.target.value)}
            />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
              <button type="submit" className="dashboard-btn-new" disabled={enviandoNota || !novaNota.trim()}>
                {enviandoNota ? "Salvando..." : "Adicionar anotação"}
              </button>
            </div>
          </form>
          {notas.length === 0 ? (
            <p className="list-card-meta">Nenhum registro ainda.</p>
          ) : (
            <ul className="timeline">
              {notas.map((n) => (
                <li key={n.id} className={`timeline-${n.tipo}`}>
                  <div className="timeline-meta">
                    {formatDataHora(n.created_at)}
                    {n.autor_nome && ` · ${n.autor_nome}`}
                    {n.tipo === "mensagem" && " · nova mensagem pelo site"}
                  </div>
                  <div className="timeline-texto">{n.texto}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {ficha && (
        <div className="contato-card">
          <h3>Ficha 360</h3>
          {ficha.resumo.associado ? (
            <p style={{ margin: "0 0 0.9rem", fontSize: "0.9rem", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
              Associado: <Link to={`/app/membros/${ficha.resumo.associado.id}`}>{ficha.resumo.associado.nome}</Link>
              <span className={`status-badge status-badge-${BADGE_SITUACAO[ficha.resumo.associado.situacao]}`}>
                {ficha.resumo.associado.situacao_display}
              </span>
            </p>
          ) : ficha.resumo.associado_mesmo_email ? (
            <div className="highlight-banner" style={{ marginBottom: "0.9rem" }}>
              Já existe um associado com este e-mail:{" "}
              <Link to={`/app/membros/${ficha.resumo.associado_mesmo_email.id}`}>{ficha.resumo.associado_mesmo_email.nome}</Link>. Use
              “Converter em associado” para vincular o contato a ele.
            </div>
          ) : null}
          <div className="ficha-resumo">
            <div className="ficha-resumo-item">
              <span>Contatos recebidos</span>
              <strong>{ficha.resumo.contatos}</strong>
            </div>
            <div className="ficha-resumo-item">
              <span>Inscrições em eventos</span>
              <strong>{ficha.resumo.eventos}</strong>
            </div>
            <div className="ficha-resumo-item">
              <span>Trabalhos submetidos</span>
              <strong>{ficha.resumo.trabalhos}</strong>
            </div>
            <div className="ficha-resumo-item">
              <span>Compras pagas</span>
              <strong>
                {ficha.resumo.pedidos_pagos} · {formatBRL(ficha.resumo.total_pago)}
              </strong>
            </div>
            <div className="ficha-resumo-item">
              <span>Última atividade</span>
              <strong>
                {ficha.resumo.ultima_atividade ? new Date(ficha.resumo.ultima_atividade).toLocaleDateString("pt-BR") : "—"}
              </strong>
            </div>
          </div>
          {ficha.itens.length === 0 ? (
            <p className="list-card-meta">Nenhuma atividade encontrada.</p>
          ) : (
            <ul className="membro-timeline">
              {ficha.itens.map((item, i) => (
                <li key={`${item.quando}-${i}`} className={`mt-${item.categoria}`}>
                  <div className="membro-timeline-meta">
                    {new Date(item.quando).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}
                  </div>
                  <div className="membro-timeline-titulo">
                    {item.link ? <Link to={item.link}>{item.titulo}</Link> : item.titulo}
                  </div>
                  {item.detalhe && <div className="membro-timeline-detalhe">{item.detalhe}</div>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {showConverter && (
        <div className="dashboard-modal-overlay" onClick={() => setShowConverter(false)}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">Converter em associado</h2>
            </div>
            <div className="dashboard-modal-content page-form">
              <p style={{ marginTop: 0, fontSize: "0.9rem" }}>
                Se já existir um associado com o e-mail <strong>{contato.email}</strong>, o contato será apenas vinculado a ele.
                Caso contrário, um novo cadastro será criado com nome, e-mail, telefone e instituição.
              </p>
              <div className="form-group">
                <label className="form-label">Filiação inicial (para novo cadastro)</label>
                <select className="form-select" value={tipoFiliacao} onChange={(e) => setTipoFiliacao(e.target.value)}>
                  {TIPOS_FILIACAO.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="dashboard-modal-footer">
              <button type="button" className="dashboard-btn-secondary" onClick={() => setShowConverter(false)}>
                Cancelar
              </button>
              <button type="button" className="dashboard-btn-new" onClick={converter} disabled={convertendo}>
                {convertendo ? "Convertendo..." : "Confirmar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
