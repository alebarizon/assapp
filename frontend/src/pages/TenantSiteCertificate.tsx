import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { downloadPublicCertificate, verifyCertificate } from "@/services/courses";
import type { CertificateVerification } from "@/types/courses";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "@/components/tenant-site/TenantSite.css";

export default function TenantSiteCertificate() {
  const schema = useTenantSchema();
  const [searchParams] = useSearchParams();
  const { payload, error } = useSiteShell(schema);
  const [code, setCode] = useState(searchParams.get("codigo") || "");
  const [result, setResult] = useState<CertificateVerification | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [baixando, setBaixando] = useState(false);
  const q = buildTenantSiteQuery(schema);

  const verificar = async (value: string) => {
    if (!value.trim()) return;
    setResult(null);
    setNotFound(false);
    try {
      setResult(await verifyCertificate(schema, value.trim()));
    } catch {
      setNotFound(true);
    }
  };

  useEffect(() => {
    const initial = searchParams.get("codigo");
    if (initial) void verificar(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schema]);

  const baixar = async () => {
    if (!result) return;
    setBaixando(true);
    try {
      await downloadPublicCertificate(schema, result.code);
    } finally {
      setBaixando(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void verificar(code);
  };

  if (error) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section" style={{ maxWidth: 640 }}>
        <p>
          <Link to={`/site${q}`}>← Início</Link>
        </p>
        <h1>Verificar certificado</h1>
        <p style={{ color: "var(--ts-muted)" }}>Informe o código impresso no certificado.</p>
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", margin: "1rem 0" }}>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Código do certificado"
            style={{ flex: 1, padding: "0.7rem 0.9rem", border: "1px solid #ddd", borderRadius: 8 }}
          />
          <button type="submit" className="tenant-site-btn">
            Verificar
          </button>
        </form>

        {notFound && <p style={{ color: "#b42318" }}>Certificado não encontrado. Confira o código.</p>}
        {result && (
          <div className="tenant-site-card">
            <p style={{ color: "#027a48", fontWeight: 600, marginTop: 0 }}>Certificado válido</p>
            <p>
              <strong>{result.participant_name}</strong> {result.action} <strong>{result.title}</strong>
              {result.workload_hours ? ` (${result.workload_hours} h)` : ""}.
            </p>
            <p style={{ color: "var(--ts-muted)" }}>
              Emitido por {result.issuer}
              {result.issued_at ? ` em ${new Date(`${result.issued_at}T12:00:00`).toLocaleDateString("pt-BR")}` : ""} · Código{" "}
              {result.code}
            </p>
            <button
              type="button"
              className="tenant-site-btn"
              style={{ background: "var(--ts-primary)", color: "#fff", marginTop: "0.5rem" }}
              disabled={baixando}
              onClick={baixar}
            >
              {baixando ? "Gerando PDF…" : "Baixar certificado (PDF)"}
            </button>
          </div>
        )}
      </section>
    </SiteShell>
  );
}
