import React, { useCallback, useEffect, useState } from "react";
import { Award, Download, FilePlus, Plus, Send, Trash2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  downloadMeuArquivo,
  enviarMinhaSubmissao,
  excluirMinhaSubmissao,
  listMinhasChamadas,
  listMinhasSubmissoes,
  salvarMinhaSubmissao,
} from "@/services/eventos";
import type { ChamadaAberta, Coautor, MinhaSubmissao } from "@/types/eventos";
import { apiErrorMessage } from "@/utils/apiError";
import { buildTenantSiteQuery } from "@/utils/tenantSite";

interface Rascunho {
  id?: string;
  cfp: string;
  titulo: string;
  resumo: string;
  area_tematica: string;
  palavras: string;
  coautores: Coautor[];
  arquivo: File | null;
  tem_arquivo: boolean;
}

const novoRascunho = (cfp: string): Rascunho => ({
  cfp,
  titulo: "",
  resumo: "",
  area_tematica: "",
  palavras: "",
  coautores: [],
  arquivo: null,
  tem_arquivo: false,
});

const DATA = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

export default function MeusTrabalhos() {
  const { tenantSchema } = useAuth();
  const [chamadas, setChamadas] = useState<ChamadaAberta[]>([]);
  const [trabalhos, setTrabalhos] = useState<MinhaSubmissao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState<Rascunho | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const [cs, ts] = await Promise.all([listMinhasChamadas(), listMinhasSubmissoes()]);
      setChamadas(cs);
      setTrabalhos(ts);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar seus trabalhos."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const chamadaDoForm = form ? chamadas.find((c) => c.id === form.cfp) : undefined;

  const editar = (t: MinhaSubmissao) =>
    setForm({
      id: t.id,
      cfp: t.cfp,
      titulo: t.titulo,
      resumo: t.resumo,
      area_tematica: t.area_tematica,
      palavras: t.palavras_chave.join(", "),
      coautores: t.coautores,
      arquivo: null,
      tem_arquivo: t.tem_arquivo,
    });

  const setCoautor = (i: number, campo: keyof Coautor, valor: string) =>
    form && setForm({ ...form, coautores: form.coautores.map((c, j) => (j === i ? { ...c, [campo]: valor } : c)) });

  const salvar = async (e: React.SyntheticEvent, submeter: boolean) => {
    e.preventDefault();
    if (!form) return;
    setErro("");
    setSalvando(true);
    try {
      const salvo = await salvarMinhaSubmissao(
        {
          cfp: form.cfp,
          titulo: form.titulo,
          resumo: form.resumo,
          area_tematica: form.area_tematica,
          palavras_chave: form.palavras.split(",").map((p) => p.trim()).filter(Boolean),
          coautores: form.coautores.filter((c) => c.nome.trim()),
          arquivo: form.arquivo,
        },
        form.id
      );
      setForm({ ...form, id: salvo.id, arquivo: null, tem_arquivo: salvo.tem_arquivo });
      if (submeter) {
        await enviarMinhaSubmissao(salvo.id);
        setMsg("Trabalho submetido! Você receberá a decisão da comissão por e-mail.");
      } else {
        setMsg("Rascunho salvo. Você pode editar e submeter até o encerramento da chamada.");
      }
      setForm(null);
      await carregar();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível salvar o trabalho."));
      await carregar();
    } finally {
      setSalvando(false);
    }
  };

  const acao = async (fn: () => Promise<unknown>, sucesso: string) => {
    setErro("");
    try {
      await fn();
      setMsg(sucesso);
      await carregar();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível concluir a ação."));
    }
  };

  const linkCertificado = (codigo: string) => {
    const query = tenantSchema ? buildTenantSiteQuery(tenantSchema) : "";
    return `/site/certificados${query}${query ? "&" : "?"}codigo=${encodeURIComponent(codigo)}`;
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Trabalhos científicos</h1>
        <p className="dashboard-subtitle">Submeta trabalhos aos eventos e acompanhe a avaliação</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      {form && (
        <div className="page-form-container" style={{ marginBottom: "1.5rem" }}>
          <form className="page-form" onSubmit={(e) => void salvar(e, false)}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "0.25rem" }}>
              {form.id ? "Editar trabalho" : "Novo trabalho"}
            </h3>
            {chamadaDoForm && (
              <p className="list-card-meta" style={{ marginBottom: "1rem" }}>
                {chamadaDoForm.evento_titulo} · submissões até {DATA(chamadaDoForm.data_fechamento)}
                {chamadaDoForm.anonimo && " · avaliação duplo-cega: não identifique os autores no arquivo"}
              </p>
            )}
            <div className="form-group">
              <label className="form-label">Título</label>
              <input
                className="form-input"
                required
                value={form.titulo}
                onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Resumo</label>
              <textarea
                className="form-input"
                required
                rows={6}
                value={form.resumo}
                onChange={(e) => setForm({ ...form, resumo: e.target.value })}
              />
            </div>
            <div className="form-row-2">
              {chamadaDoForm && chamadaDoForm.areas_tematicas.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Área temática</label>
                  <select
                    className="form-select"
                    required
                    value={form.area_tematica}
                    onChange={(e) => setForm({ ...form, area_tematica: e.target.value })}
                  >
                    <option value="">Selecione</option>
                    {chamadaDoForm.areas_tematicas.map((a) => (
                      <option key={a} value={a}>{a}</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="form-group">
                <label className="form-label">Palavras-chave (separadas por vírgula)</label>
                <input
                  className="form-input"
                  value={form.palavras}
                  onChange={(e) => setForm({ ...form, palavras: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Coautores</label>
              {form.coautores.map((c, i) => (
                <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
                  <input
                    className="form-input"
                    style={{ flex: "2 1 10rem" }}
                    placeholder="Nome completo"
                    value={c.nome}
                    onChange={(e) => setCoautor(i, "nome", e.target.value)}
                  />
                  <input
                    className="form-input"
                    style={{ flex: "2 1 10rem" }}
                    type="email"
                    placeholder="E-mail"
                    value={c.email}
                    onChange={(e) => setCoautor(i, "email", e.target.value)}
                  />
                  <input
                    className="form-input"
                    style={{ flex: "2 1 10rem" }}
                    placeholder="Instituição"
                    value={c.instituicao}
                    onChange={(e) => setCoautor(i, "instituicao", e.target.value)}
                  />
                  <button
                    type="button"
                    className="dashboard-btn-cancel"
                    aria-label="Remover coautor"
                    onClick={() => setForm({ ...form, coautores: form.coautores.filter((_, j) => j !== i) })}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="dashboard-btn-secondary"
                onClick={() =>
                  setForm({ ...form, coautores: [...form.coautores, { nome: "", email: "", instituicao: "" }] })
                }
              >
                <Plus size={14} /> Adicionar coautor
              </button>
            </div>

            <div className="form-group">
              <label className="form-label">
                Arquivo do trabalho (PDF, DOC, DOCX ou ODT, até 15 MB)
                {chamadaDoForm?.exige_arquivo ? " — obrigatório" : " — opcional"}
              </label>
              {form.tem_arquivo && !form.arquivo && (
                <p className="list-card-meta">Arquivo já enviado. Escolha outro para substituir.</p>
              )}
              <input
                className="form-input"
                type="file"
                accept=".pdf,.doc,.docx,.odt"
                onChange={(e) => setForm({ ...form, arquivo: e.target.files?.[0] ?? null })}
              />
            </div>

            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setForm(null)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-secondary" disabled={salvando}>
                Salvar rascunho
              </button>
              <button
                type="button"
                className="dashboard-btn-save"
                disabled={salvando}
                onClick={(e) => {
                  const f = (e.currentTarget as HTMLButtonElement).form;
                  if (f && !f.reportValidity()) return;
                  void salvar(e, true);
                }}
              >
                <Send size={14} /> {salvando ? "Enviando..." : "Salvar e submeter"}
              </button>
            </div>
          </form>
        </div>
      )}

      <h2 className="dashboard-section-title" style={{ fontSize: "1.05rem", margin: "0 0 0.75rem" }}>
        Chamadas abertas
      </h2>
      {chamadas.length === 0 ? (
        <div className="dashboard-empty" style={{ marginBottom: "1.5rem" }}>
          Nenhuma chamada de trabalhos aberta no momento.
        </div>
      ) : (
        <div className="list-stack" style={{ marginBottom: "1.5rem" }}>
          {chamadas.map((c) => {
            const esgotado = c.minhas_enviadas >= c.max_submissoes_por_autor;
            return (
              <div key={c.id} className="list-card" style={{ alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <p className="list-card-title">{c.evento_titulo}</p>
                  <p className="list-card-meta">
                    {c.titulo} · até {DATA(c.data_fechamento)} · {c.minhas_enviadas} de {c.max_submissoes_por_autor}{" "}
                    trabalho(s) enviados
                  </p>
                  {c.instrucoes && (
                    <p className="list-card-meta" style={{ whiteSpace: "pre-wrap" }}>{c.instrucoes}</p>
                  )}
                </div>
                <button
                  type="button"
                  className="dashboard-btn-new"
                  disabled={esgotado}
                  title={esgotado ? "Limite de trabalhos por autor atingido" : undefined}
                  onClick={() => {
                    setMsg("");
                    setForm(novoRascunho(c.id));
                  }}
                >
                  <FilePlus size={14} /> Novo trabalho
                </button>
              </div>
            );
          })}
        </div>
      )}

      <h2 className="dashboard-section-title" style={{ fontSize: "1.05rem", margin: "0 0 0.75rem" }}>
        Meus trabalhos
      </h2>
      {trabalhos.length === 0 ? (
        <div className="dashboard-empty">Você ainda não submeteu trabalhos.</div>
      ) : (
        <div className="list-stack">
          {trabalhos.map((t) => {
            const chamadaAberta = chamadas.some((c) => c.id === t.cfp);
            return (
              <div key={t.id} className="list-card" style={{ alignItems: "flex-start", flexDirection: "column" }}>
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: "1rem" }}>
                  <div>
                    <p className="list-card-title">{t.titulo}</p>
                    <p className="list-card-meta">
                      {t.evento_titulo}
                      {t.area_tematica && ` · ${t.area_tematica}`}
                      {t.submetido_em && ` · submetido em ${DATA(t.submetido_em)}`}
                    </p>
                  </div>
                  <span className={`status-badge status-badge-${t.status}`}>{t.status_display}</span>
                </div>

                {t.decidido_em && (
                  <div style={{ width: "100%", marginTop: "0.5rem" }}>
                    {t.decisao_comentario && (
                      <p className="list-card-meta">
                        <strong>Comissão:</strong> {t.decisao_comentario}
                      </p>
                    )}
                    {t.comentarios_pareceres.map((c, i) => (
                      <p key={i} className="list-card-meta" style={{ whiteSpace: "pre-wrap" }}>
                        <strong>Parecer {i + 1}:</strong> {c}
                      </p>
                    ))}
                  </div>
                )}

                <div className="filters-row" style={{ marginBottom: 0, marginTop: "0.5rem" }}>
                  {t.status === "rascunho" && chamadaAberta && (
                    <>
                      <button type="button" className="dashboard-btn-edit" onClick={() => editar(t)}>
                        Editar
                      </button>
                      <button
                        type="button"
                        className="dashboard-btn-save"
                        onClick={() => void acao(() => enviarMinhaSubmissao(t.id), "Trabalho submetido!")}
                      >
                        <Send size={14} /> Submeter
                      </button>
                    </>
                  )}
                  {t.status === "rascunho" && !chamadaAberta && (
                    <span className="list-card-meta">Chamada encerrada — rascunho não enviado.</span>
                  )}
                  {t.status === "rascunho" && (
                    <button
                      type="button"
                      className="dashboard-btn-cancel"
                      onClick={() =>
                        confirm("Excluir este rascunho?") &&
                        void acao(() => excluirMinhaSubmissao(t.id), "Rascunho excluído.")
                      }
                    >
                      <Trash2 size={14} /> Excluir
                    </button>
                  )}
                  {t.tem_arquivo && (
                    <button type="button" className="dashboard-btn-secondary" onClick={() => void downloadMeuArquivo(t.id)}>
                      <Download size={14} /> Arquivo
                    </button>
                  )}
                  {t.certificado_codigo && (
                    <a
                      className="dashboard-btn-secondary"
                      href={linkCertificado(t.certificado_codigo)}
                      target="_blank"
                      rel="noreferrer"
                      style={{ textDecoration: "none" }}
                    >
                      <Award size={14} /> Certificado
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
