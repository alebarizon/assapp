import React, { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import {
  listMeusDocumentos,
  meuDocumentoDownloadUrl,
  type DocumentItem,
} from "@/services/documents";

export default function MeusDocumentos() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setDocs(await listMeusDocumentos());
      } catch {
        setError("Erro ao carregar documentos.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDownload = async (id: string, title: string) => {
    const token = localStorage.getItem("assapp_access");
    const res = await fetch(meuDocumentoDownloadUrl(id), {
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
      <div className="dashboard-header">
        <h1 className="dashboard-title">Meus documentos</h1>
        <p className="dashboard-subtitle">Arquivos gerais e documentos destinados a você</p>
      </div>

      {error && <div className="alert-banner alert-banner-error">{error}</div>}

      <div className="dashboard-content-panel">
        {docs.length === 0 ? (
          <div className="dashboard-empty">Nenhum documento disponível.</div>
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
                      {d.file_type ? ` · .${d.file_type}` : ""}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  onClick={() => handleDownload(d.id, d.title)}
                >
                  <Download size={14} /> Baixar
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
