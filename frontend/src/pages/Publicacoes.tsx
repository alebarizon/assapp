import React, { useEffect, useState } from "react";
import { BookOpen, Download, ExternalLink, Pencil, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { baixarArquivoPublicacao, deletePublicacao, listPublicacoes, salvarPublicacao } from "@/services/publicacoes";
import {
  ACESSOS_PUBLICACAO,
  TIPOS_PUBLICACAO,
  type AcessoPublicacao,
  type AutorPublicacao,
  type Publicacao,
  type TipoPublicacao,
} from "@/types/publicacoes";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";
import { buildTenantSiteQuery, formatBRL } from "@/utils/tenantSite";
import "@/components/publicacoes/Publicacoes.css";

interface FormState {
  titulo: string;
  subtitulo: string;
  tipo: TipoPublicacao;
  acesso: AcessoPublicacao;
  resumo: string;
  autores: string;
  palavras_chave: string;
  ano: string;
  edicao: string;
  isbn: string;
  issn: string;
  preco: string;
  preco_socio: string;
  publicada: boolean;
  capa: File | null;
  arquivo: File | null;
  remover_capa: boolean;
  remover_arquivo: boolean;
}

const VAZIO: FormState = {
  titulo: "",
  subtitulo: "",
  tipo: "ebook",
  acesso: "associados",
  resumo: "",
  autores: "",
  palavras_chave: "",
  ano: String(new Date().getFullYear()),
  edicao: "",
  isbn: "",
  issn: "",
  preco: "",
  preco_socio: "",
  publicada: false,
  capa: null,
  arquivo: null,
  remover_capa: false,
  remover_arquivo: false,
};

/** Uma linha por autor: "Nome; Instituição; ORCID". */
function autoresParaTexto(autores: AutorPublicacao[]) {
  return autores.map((a) => [a.nome, a.instituicao, a.orcid].filter(Boolean).join("; ")).join("\n");
}

function textoParaAutores(texto: string): AutorPublicacao[] {
  return texto
    .split("\n")
    .map((linha) => linha.split(";").map((p) => p.trim()))
    .filter(([nome]) => nome)
    .map(([nome, instituicao = "", orcid = ""]) => ({ nome, instituicao, orcid }));
}

function paraForm(p: Publicacao): FormState {
  return {
    ...VAZIO,
    titulo: p.titulo,
    subtitulo: p.subtitulo,
    tipo: p.tipo,
    acesso: p.acesso,
    resumo: p.resumo,
    autores: autoresParaTexto(p.autores),
    palavras_chave: p.palavras_chave.join(", "),
    ano: p.ano ? String(p.ano) : "",
    edicao: p.edicao,
    isbn: p.isbn,
    issn: p.issn,
    preco: p.preco ?? "",
    preco_socio: p.preco_socio ?? "",
    publicada: p.publicada,
  };
}

export default function Publicacoes() {
  const { user, tenantSchema } = useAuth();
  const editavel = podeEditar(user, "publicacoes");
  const [itens, setItens] = useState<Publicacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [editando, setEditando] = useState<Publicacao | "nova" | null>(null);
  const [form, setForm] = useState<FormState>(VAZIO);
  const [salvando, setSalvando] = useState(false);

  const load = async () => {
    try {
      setItens(await listPublicacoes());
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar publicações."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const abrir = (p: Publicacao | "nova") => {
    setErro("");
    setForm(p === "nova" ? VAZIO : paraForm(p));
    setEditando(p);
  };

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    const fd = new FormData();
    const campos = ["titulo", "subtitulo", "tipo", "acesso", "resumo", "edicao", "isbn", "issn"] as const;
    campos.forEach((c) => fd.append(c, form[c]));
    fd.append("ano", form.ano);
    fd.append("publicada", String(form.publicada));
    fd.append("autores", JSON.stringify(textoParaAutores(form.autores)));
    fd.append(
      "palavras_chave",
      JSON.stringify(
        form.palavras_chave
          .split(",")
          .map((p) => p.trim())
          .filter(Boolean),
      ),
    );
    const vende = form.acesso !== "publico" && form.preco !== "";
    fd.append("preco", vende ? form.preco : "");
    fd.append("preco_socio", vende ? form.preco_socio : "");
    if (form.capa) fd.append("capa", form.capa);
    if (form.arquivo) fd.append("arquivo", form.arquivo);
    if (form.remover_capa) fd.append("remover_capa", "true");
    if (form.remover_arquivo) fd.append("remover_arquivo", "true");
    setSalvando(true);
    setErro("");
    try {
      await salvarPublicacao(editando === "nova" ? null : editando.id, fd);
      setEditando(null);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar."));
    } finally {
      setSalvando(false);
    }
  };

  const excluir = async (p: Publicacao) => {
    if (!window.confirm(`Excluir "${p.titulo}"? Quem já comprou perde o acesso.`)) return;
    try {
      await deletePublicacao(p.id);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao excluir."));
    }
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

  const atual = editando && editando !== "nova" ? editando : null;
  const ajudaAcesso = ACESSOS_PUBLICACAO.find((a) => a.value === form.acesso)?.ajuda;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Publicações</h1>
          <p className="dashboard-subtitle">Dossiês, e-books e boletins — no site, no portal do associado e na loja</p>
        </div>
        <div className="dashboard-header-actions">
          <a className="dashboard-btn-secondary" href={`/site/publicacoes${tenantSchema ? buildTenantSiteQuery(tenantSchema) : ""}`} target="_blank" rel="noreferrer">
            <ExternalLink size={16} /> Ver no site
          </a>
          {editavel && (
            <button type="button" className="dashboard-btn-new" onClick={() => abrir("nova")}>
              <Plus size={16} /> Nova publicação
            </button>
          )}
        </div>
      </div>

      {erro && !editando && <div className="alert-banner alert-banner-error">{erro}</div>}

      {itens.length === 0 ? (
        <div className="dashboard-content-panel">
          <div className="dashboard-empty">Nenhuma publicação cadastrada.</div>
        </div>
      ) : (
        <div className="pub-grid">
          {itens.map((p) => (
            <div key={p.id} className="pub-card">
              <div className="pub-capa" style={p.capa_url ? { backgroundImage: `url(${p.capa_url})` } : undefined}>
                {!p.capa_url && <BookOpen size={40} />}
              </div>
              <div className="pub-corpo">
                <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                  <span className={`status-badge status-badge-${p.publicada ? "ativa" : "pendente"}`}>
                    {p.publicada ? "Publicada" : "Rascunho"}
                  </span>
                  <span className="status-badge">{p.acesso_display}</span>
                </div>
                <p className="pub-titulo">{p.titulo}</p>
                <p className="pub-meta">
                  {p.tipo_display}
                  {p.ano ? ` · ${p.ano}` : ""}
                  {p.preco ? ` · ${formatBRL(p.preco)}` : ""}
                </p>
                <p className="pub-meta">
                  {p.downloads} download{p.downloads === 1 ? "" : "s"}
                  {p.catalog_item ? ` · ${p.vendas} venda${p.vendas === 1 ? "" : "s"}` : ""}
                  {!p.tem_arquivo && " · sem arquivo"}
                </p>
                <div className="pub-acoes">
                  {p.tem_arquivo && (
                    <button
                      type="button"
                      className="dashboard-btn-secondary"
                      onClick={() => void baixarArquivoPublicacao(p.id)}
                      title="Baixar arquivo"
                    >
                      <Download size={14} />
                    </button>
                  )}
                  {editavel && (
                    <>
                      <button type="button" className="dashboard-btn-secondary" onClick={() => abrir(p)}>
                        <Pencil size={14} /> Editar
                      </button>
                      <button
                        type="button"
                        className="dashboard-btn-danger"
                        style={{ padding: "0.5rem 0.75rem" }}
                        onClick={() => void excluir(p)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {editando && (
        <div className="dashboard-modal-overlay" onClick={() => setEditando(null)}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 720 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">{atual ? "Editar publicação" : "Nova publicação"}</h2>
            </div>
            <form onSubmit={salvar}>
              <div className="dashboard-modal-content page-form">
                {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
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
                  <label className="form-label">Subtítulo</label>
                  <input
                    className="form-input"
                    value={form.subtitulo}
                    onChange={(e) => setForm({ ...form, subtitulo: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Tipo</label>
                    <select
                      className="form-select"
                      value={form.tipo}
                      onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoPublicacao })}
                    >
                      {TIPOS_PUBLICACAO.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Ano</label>
                    <input
                      className="form-input"
                      type="number"
                      min={1900}
                      max={2100}
                      value={form.ano}
                      onChange={(e) => setForm({ ...form, ano: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Edição / volume</label>
                    <input
                      className="form-input"
                      placeholder="v. 3, n. 2"
                      value={form.edicao}
                      onChange={(e) => setForm({ ...form, edicao: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Resumo / apresentação</label>
                  <textarea
                    className="form-input"
                    rows={4}
                    value={form.resumo}
                    onChange={(e) => setForm({ ...form, resumo: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Autores / organizadores</label>
                  <textarea
                    className="form-input"
                    rows={3}
                    placeholder={"Uma linha por autor: Nome; Instituição; ORCID\nMaria Souza; UFMG; 0000-0002-1825-0097"}
                    value={form.autores}
                    onChange={(e) => setForm({ ...form, autores: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Palavras-chave (separadas por vírgula)</label>
                  <input
                    className="form-input"
                    value={form.palavras_chave}
                    onChange={(e) => setForm({ ...form, palavras_chave: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">ISBN</label>
                    <input className="form-input" value={form.isbn} onChange={(e) => setForm({ ...form, isbn: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">ISSN</label>
                    <input className="form-input" value={form.issn} onChange={(e) => setForm({ ...form, issn: e.target.value })} />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Quem pode baixar</label>
                  <select
                    className="form-select"
                    value={form.acesso}
                    onChange={(e) => setForm({ ...form, acesso: e.target.value as AcessoPublicacao })}
                  >
                    {ACESSOS_PUBLICACAO.map((a) => (
                      <option key={a.value} value={a.value}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                  {ajudaAcesso && <p className="list-card-meta" style={{ margin: "0.35rem 0 0" }}>{ajudaAcesso}</p>}
                </div>
                {form.acesso !== "publico" && (
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">
                        Preço na loja (R$){form.acesso === "associados" && " — opcional"}
                      </label>
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        min={0}
                        required={form.acesso === "venda"}
                        value={form.preco}
                        onChange={(e) => setForm({ ...form, preco: e.target.value })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Preço para sócio em dia (R$)</label>
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        min={0}
                        disabled={!form.preco}
                        value={form.preco_socio}
                        onChange={(e) => setForm({ ...form, preco_socio: e.target.value })}
                      />
                    </div>
                  </div>
                )}

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Capa (imagem)</label>
                    <input
                      className="form-input"
                      type="file"
                      accept="image/*"
                      onChange={(e) => setForm({ ...form, capa: e.target.files?.[0] || null, remover_capa: false })}
                    />
                    {atual?.capa_url && !form.capa && (
                      <label className="list-card-meta" style={{ display: "flex", gap: 6, marginTop: 4 }}>
                        <input
                          type="checkbox"
                          checked={form.remover_capa}
                          onChange={(e) => setForm({ ...form, remover_capa: e.target.checked })}
                        />
                        Remover capa atual
                      </label>
                    )}
                  </div>
                  <div className="form-group">
                    <label className="form-label">Arquivo (PDF, EPUB…)</label>
                    <input
                      className="form-input"
                      type="file"
                      onChange={(e) => setForm({ ...form, arquivo: e.target.files?.[0] || null, remover_arquivo: false })}
                    />
                    {atual?.arquivo_nome && !form.arquivo && (
                      <label className="list-card-meta" style={{ display: "flex", gap: 6, marginTop: 4 }}>
                        <input
                          type="checkbox"
                          checked={form.remover_arquivo}
                          onChange={(e) => setForm({ ...form, remover_arquivo: e.target.checked })}
                        />
                        Remover {atual.arquivo_nome}
                      </label>
                    )}
                  </div>
                </div>
                <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.9rem" }}>
                  <input
                    type="checkbox"
                    checked={form.publicada}
                    onChange={(e) => setForm({ ...form, publicada: e.target.checked })}
                  />
                  Publicada (aparece no site, no portal e na loja)
                </label>
              </div>
              <div className="dashboard-modal-footer">
                <button type="button" className="dashboard-btn-secondary" onClick={() => setEditando(null)}>
                  Cancelar
                </button>
                <button type="submit" className="dashboard-btn-new" disabled={salvando}>
                  {salvando ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
