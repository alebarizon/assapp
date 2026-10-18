import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CheckCircle, MailX } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { confirmarDescadastro, getDescadastro, type SituacaoDescadastro } from "@/services/newsletter";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

export default function TenantSiteDescadastrar() {
  const [params] = useSearchParams();
  const token = params.get("t") ?? "";
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [dados, setDados] = useState<SituacaoDescadastro | null>(null);
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!token) {
      setErro("Link de descadastro incompleto.");
      return;
    }
    getDescadastro(schema, token)
      .then(setDados)
      .catch(() => setErro("Link de descadastro inválido ou expirado."));
  }, [schema, token]);

  const confirmar = async () => {
    setEnviando(true);
    try {
      setDados(await confirmarDescadastro(schema, token));
    } catch {
      setErro("Não foi possível concluir. Tente novamente mais tarde.");
    } finally {
      setEnviando(false);
    }
  };

  if (!payload && !shellError) return <div className="tenant-site-empty">Carregando…</div>;

  const conteudo = (
    <section className="tenant-site-section" style={{ maxWidth: 560, margin: shellError ? "3rem auto" : undefined }}>
      <h1 style={{ marginTop: 0 }}>Comunicados por e-mail</h1>
      {erro && (
        <div className="course-card" style={{ borderLeft: "4px solid #b42318" }}>
          {erro}
        </div>
      )}
      {!erro && !dados && <p className="course-muted">Carregando…</p>}
      {dados && !dados.descadastrado && (
        <div className="course-card">
          <p style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 700, marginTop: 0 }}>
            <MailX size={22} /> Deixar de receber a newsletter
          </p>
          <p>
            O endereço <strong>{dados.email}</strong> deixará de receber as campanhas de {dados.associacao}. Avisos
            obrigatórios da filiação, como cobranças e convocações, continuam sendo enviados.
          </p>
          <button type="button" className="tenant-site-btn" onClick={confirmar} disabled={enviando}>
            {enviando ? "Confirmando…" : "Confirmar descadastro"}
          </button>
        </div>
      )}
      {dados?.descadastrado && (
        <div className="course-card" style={{ borderLeft: "4px solid #027a48" }}>
          <p style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#027a48", fontWeight: 700, marginTop: 0 }}>
            <CheckCircle size={22} /> Pronto
          </p>
          <p style={{ marginBottom: 0 }}>
            <strong>{dados.email}</strong> não receberá mais a newsletter de {dados.associacao}. Se mudar de ideia,
            peça à secretaria para reativar.
          </p>
        </div>
      )}
    </section>
  );

  return payload ? (
    <SiteShell payload={payload} schema={schema}>
      {conteudo}
    </SiteShell>
  ) : (
    conteudo
  );
}
