import React, { useState } from "react";
import { BookOpen, ExternalLink, FileUp, Trash2 } from "lucide-react";
import {
  atualizarTrabalhoPublicado,
  editarAnais,
  gerarAnais,
  removerArquivoTrabalhoPublicado,
} from "@/services/eventos";
import type { AnaisPublicacao, EventoAcademico, Licenca, TrabalhoPublicado } from "@/types/eventos";
import { LICENCAS } from "@/types/eventos";
import { apiErrorMessage } from "@/utils/apiError";
import { buildTenantSiteQuery } from "@/utils/tenantSite";

interface Props {
  evento: EventoAcademico;
  temAceitos: boolean;
  podeEditar: boolean;
  tenantSchema: string | null;
  onAtualizado: () => void;
}

export default function AnaisEvento({ evento, temAceitos, podeEditar, tenantSchema, onAtualizado }: Props) {
  const anais = evento.anais;
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [gerando, setGerando] = useState(false);

  const gerar = async () => {
    const texto = anais
      ? "Atualizar os anais com os trabalhos aceitos agora? Links, DOIs e PDFs já publicados são mantidos."
      : "Publicar os anais com os trabalhos aceitos?";
    if (!confirm(texto)) return;
    setErro("");
    setGerando(true);
    try {
      await gerarAnais(evento.id);
      setMsg("Anais publicados.");
      onAtualizado();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível gerar os anais."));
    } finally {
      setGerando(false);
    }
  };

  const linkAnais = `/site/eventos/${evento.slug}/anais${tenantSchema ? buildTenantSiteQuery(tenantSchema) : ""}`;

  return (
    <div className="dashboard-content-panel">
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      <div className="filters-row" style={{ justifyContent: "space-between" }}>
        <p className="list-card-meta" style={{ margin: 0 }}>
          {anais
            ? `${anais.trabalhos.length} trabalho(s) publicados · cada um tem página própria e PDF para citação.`
            : "Os anais reúnem os trabalhos aceitos, cada um com página pública citável e PDF."}
        </p>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {anais && evento.publicado_site && (
            <a className="dashboard-btn-secondary" href={linkAnais} target="_blank" rel="noreferrer">
              <ExternalLink size={14} /> Ver no site
            </a>
          )}
          {podeEditar && temAceitos && (
            <button type="button" className="dashboard-btn-save" onClick={() => void gerar()} disabled={gerando}>
              <BookOpen size={14} /> {gerando ? "Publicando..." : anais ? "Atualizar anais" : "Gerar anais"}
            </button>
          )}
        </div>
      </div>

      {anais && !evento.publicado_site && (
        <div className="highlight-banner" style={{ marginBottom: "1rem" }}>
          O evento não está publicado no site; os anais só ficam públicos depois de publicar o evento (aba "Site e
          inscrição").
        </div>
      )}

      {!anais ? (
        <div className="dashboard-empty">
          {temAceitos ? 'Clique em "Gerar anais" para publicar.' : "Aceite trabalhos na aba Submissões para gerar os anais."}
        </div>
      ) : (
        <>
          <DadosEditoriais evento={evento} anais={anais} podeEditar={podeEditar} onSalvo={onAtualizado} />
          <div className="list-stack" style={{ marginTop: "1.25rem" }}>
            {anais.trabalhos.map((t) => (
              <LinhaTrabalho key={`${t.id}-${t.doi}`} trabalho={t} podeEditar={podeEditar} onSalvo={onAtualizado} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function DadosEditoriais({
  evento,
  anais,
  podeEditar,
  onSalvo,
}: {
  evento: EventoAcademico;
  anais: AnaisPublicacao;
  podeEditar: boolean;
  onSalvo: () => void;
}) {
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState("");
  const doServidor = () => ({
    titulo: anais.titulo,
    issn: anais.issn ?? "",
    isbn: anais.isbn,
    licenca: anais.licenca,
    editores: anais.editores,
    cidade: anais.cidade,
    apresentacao: anais.apresentacao,
  });
  const [form, setForm] = useState(doServidor);

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    try {
      await editarAnais(evento.id, { ...form, issn: form.issn || null });
      setAberto(false);
      onSalvo();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível salvar."));
    }
  };

  if (!aberto) {
    return (
      <div className="list-card" style={{ alignItems: "flex-start" }}>
        <div>
          <p className="list-card-title">{anais.titulo}</p>
          <p className="list-card-meta">
            {[
              anais.editores && `Organização: ${anais.editores}`,
              anais.cidade,
              anais.issn && `ISSN ${anais.issn}`,
              anais.isbn && `ISBN ${anais.isbn}`,
              anais.licenca_display,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {!anais.issn && !anais.isbn && (
            <p className="list-card-meta">
              Sem ISSN/ISBN. Se a associação já tem o número (IBICT / Câmara Brasileira do Livro), informe-o para
              aparecer na citação.
            </p>
          )}
        </div>
        {podeEditar && (
          <button
            type="button"
            className="dashboard-btn-edit"
            onClick={() => {
              setForm(doServidor());
              setAberto(true);
            }}
          >
            Dados editoriais
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="page-form-container">
      <form className="page-form" onSubmit={salvar}>
        {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
        <div className="form-group">
          <label className="form-label">Título dos anais</label>
          <input className="form-input" required value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
        </div>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">ISSN</label>
            <input className="form-input" placeholder="0000-0000" value={form.issn} onChange={(e) => setForm({ ...form, issn: e.target.value })} />
          </div>
          <div className="form-group">
            <label className="form-label">ISBN</label>
            <input className="form-input" placeholder="978-…" value={form.isbn} onChange={(e) => setForm({ ...form, isbn: e.target.value })} />
          </div>
        </div>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Organização / editores</label>
            <input className="form-input" value={form.editores} onChange={(e) => setForm({ ...form, editores: e.target.value })} />
          </div>
          <div className="form-group">
            <label className="form-label">Local de publicação (cidade)</label>
            <input className="form-input" value={form.cidade} onChange={(e) => setForm({ ...form, cidade: e.target.value })} />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Licença</label>
          <select className="form-select" value={form.licenca} onChange={(e) => setForm({ ...form, licenca: e.target.value as Licenca })}>
            {LICENCAS.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Apresentação</label>
          <textarea className="form-input" rows={4} value={form.apresentacao} onChange={(e) => setForm({ ...form, apresentacao: e.target.value })} />
        </div>
        <div className="form-actions">
          <button type="button" className="dashboard-btn-cancel" onClick={() => setAberto(false)}>
            Cancelar
          </button>
          <button type="submit" className="dashboard-btn-save">Salvar</button>
        </div>
      </form>
    </div>
  );
}

function LinhaTrabalho({
  trabalho: t,
  podeEditar,
  onSalvo,
}: {
  trabalho: TrabalhoPublicado;
  podeEditar: boolean;
  onSalvo: () => void;
}) {
  const [doi, setDoi] = useState(t.doi);
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  const executar = async (acao: () => Promise<unknown>) => {
    setErro("");
    setEnviando(true);
    try {
      await acao();
      onSalvo();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível salvar."));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="list-card" style={{ alignItems: "flex-start", flexDirection: "column", gap: "0.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: "1rem" }}>
        <div>
          <p className="list-card-title">
            {t.ordem}. {t.titulo}
          </p>
          <p className="list-card-meta">
            {t.autores.map((a) => a.nome).join("; ")}
            {t.area_tematica && ` · ${t.area_tematica}`}
          </p>
          <p className="list-card-meta">
            {t.tem_arquivo ? "PDF final anexado" : "Sem PDF final — o site gera um PDF com o resumo"}
          </p>
        </div>
        <a className="dashboard-btn-secondary" href={t.url_publica} target="_blank" rel="noreferrer" style={{ flexShrink: 0 }}>
          <ExternalLink size={14} /> Página
        </a>
      </div>

      {erro && <div className="alert-banner alert-banner-error" style={{ width: "100%" }}>{erro}</div>}

      {podeEditar && (
        <div className="filters-row" style={{ marginBottom: 0, width: "100%" }}>
          <input
            className="form-input"
            style={{ flex: 1, minWidth: "14rem" }}
            placeholder="DOI (ex.: 10.12345/anais.2026.001)"
            value={doi}
            onChange={(e) => setDoi(e.target.value)}
          />
          <button
            type="button"
            className="dashboard-btn-secondary"
            disabled={enviando || doi === t.doi}
            onClick={() => void executar(() => atualizarTrabalhoPublicado(t.id, { doi }))}
          >
            Salvar DOI
          </button>
          <label className="dashboard-btn-secondary" style={{ cursor: "pointer" }}>
            <FileUp size={14} /> {t.tem_arquivo ? "Trocar PDF" : "Anexar PDF final"}
            <input
              type="file"
              accept="application/pdf,.pdf"
              hidden
              onChange={(e) => {
                const arquivo = e.target.files?.[0];
                e.target.value = "";
                if (arquivo) void executar(() => atualizarTrabalhoPublicado(t.id, { arquivo }));
              }}
            />
          </label>
          {t.tem_arquivo && (
            <button
              type="button"
              className="dashboard-btn-cancel"
              disabled={enviando}
              aria-label="Remover PDF final"
              onClick={() => confirm("Remover o PDF final?") && void executar(() => removerArquivoTrabalhoPublicado(t.id))}
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
