import React, { useEffect, useState } from "react";
import { Download, FileText, Plus, Trash2 } from "lucide-react";
import {
  createDocument,
  deleteDocument,
  documentDownloadUrl,
  listDocuments,
  type DocumentAudience,
  type DocumentItem,
} from "@/services/documents";
import { listMembros } from "@/services/membros";
import type { Membro } from "@/types/membros";

export default function Documents() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [membros, setMembros] = useState<Membro[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    description: "",
    audience: "geral" as DocumentAudience,
    membro: "",
    file: null as File | null,
  });

  const load = async () => {
    setLoading(true);
    try {
      const [d, m] = await Promise.all([listDocuments(), listMembros()]);
      setDocs(d);
      setMembros(m);
    } catch {
      setError("Erro ao carregar documentos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.file) {
      setError("Selecione um arquivo.");
      return;
    }
    const fd = new FormData();
    fd.append("title", form.title);
    fd.append("audience", form.audience);
    if (form.description) fd.append("description", form.description);
    if (form.audience === "membro" && form.membro) fd.append("membro", form.membro);
    fd.append("file", form.file);
    try {
      await createDocument(fd);
      setShowForm(false);
      setForm({ title: "", description: "", audience: "geral", membro: "", file: null });
      await load();
    } catch {
      setError("Falha no upload.");
    }
  };

  const handleDownload = async (id: string, title: string) => {
    const token = localStorage.getItem("assapp_access");
    const url = documentDownloadUrl(id);
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      setError("Falha no download.");
      return;
    }
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = title;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando documentos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Documentos</h1>
          <p className="dashboard-subtitle">
            Arquivos gerais, da diretoria ou de associados específicos
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> Novo documento
          </button>
        </div>
      </div>

      {error && <div className="alert-banner alert-banner-error">{error}</div>}

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Título</label>
              <input
                className="form-input"
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Audiência</label>
              <select
                className="form-select"
                value={form.audience}
                onChange={(e) =>
                  setForm({ ...form, audience: e.target.value as DocumentAudience })
                }
              >
                <option value="geral">Geral (associação)</option>
                <option value="diretoria">Diretoria</option>
                <option value="membro">Membro específico</option>
              </select>
            </div>
            {form.audience === "membro" && (
              <div className="form-group">
                <label className="form-label">Membro</label>
                <select
                  className="form-select"
                  required
                  value={form.membro}
                  onChange={(e) => setForm({ ...form, membro: e.target.value })}
                >
                  <option value="">Selecione…</option>
                  {membros.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nome_completo}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="form-group">
              <label className="form-label">Descrição</label>
              <textarea
                className="form-input"
                rows={2}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Arquivo</label>
              <input
                className="form-input"
                type="file"
                required
                onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Enviar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-content-panel">
        {docs.length === 0 ? (
          <div className="dashboard-empty">Nenhum documento enviado.</div>
        ) : (
          <div className="list-stack">
            {docs.map((d) => (
              <div key={d.id} className="list-card">
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
                  <FileText size={20} style={{ marginTop: 2, color: "#9a6a0b" }} />
                  <div>
                    <p className="list-card-title">{d.title}</p>
                    <p className="list-card-meta">
                      {d.audience_display}
                      {d.membro_nome ? ` · ${d.membro_nome}` : ""}
                      {d.file_type ? ` · .${d.file_type}` : ""}
                    </p>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    onClick={() => handleDownload(d.id, d.title)}
                  >
                    <Download size={14} /> Baixar
                  </button>
                  <button
                    type="button"
                    className="dashboard-btn-danger"
                    style={{ padding: "0.5rem 0.75rem" }}
                    onClick={async () => {
                      if (!confirm("Excluir documento?")) return;
                      await deleteDocument(d.id);
                      await load();
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
