import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { SiteShell, useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { useSiteShell } from "@/components/courses/useSiteShell";
import { dataCurta, validadeTexto } from "@/components/membros/CartaoAssociado";
import { verificarCarteirinha } from "@/services/membros";
import type { VerificacaoCarteirinha } from "@/types/membros";
import "@/components/tenant-site/TenantSite.css";
import "@/components/courses/Courses.css";

const VISUAL = {
  em_dia: { cor: "#027a48", Icone: CheckCircle, titulo: "Associado em dia" },
  pendente: { cor: "#b54708", Icone: AlertTriangle, titulo: "Filiação com anuidade pendente" },
  inativo: { cor: "#b42318", Icone: XCircle, titulo: "Filiação inativa" },
};

export default function TenantSiteCarteirinha() {
  const { codigo = "" } = useParams();
  const schema = useTenantSchema();
  const { payload, error: shellError } = useSiteShell(schema);
  const [dados, setDados] = useState<VerificacaoCarteirinha | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    setErro("");
    verificarCarteirinha(schema, codigo)
      .then(setDados)
      .catch(() => setErro("Carteirinha não encontrada ou substituída por uma mais recente."));
  }, [schema, codigo]);

  if (shellError) return <div className="tenant-site-empty">Site não encontrado.</div>;
  if (!payload) return <div className="tenant-site-empty">Carregando…</div>;

  const visual = dados ? VISUAL[dados.situacao] : null;

  return (
    <SiteShell payload={payload} schema={schema}>
      <section className="tenant-site-section" style={{ maxWidth: 560 }}>
        <h1 style={{ marginTop: 0 }}>Verificação de carteirinha</h1>
        {erro && (
          <div className="course-card" style={{ borderLeft: "4px solid #b42318" }}>
            <strong>Não validada.</strong> {erro}
          </div>
        )}
        {!erro && !dados && <p className="course-muted">Verificando…</p>}
        {dados && visual && (
          <div className="course-card" style={{ borderLeft: `4px solid ${visual.cor}` }}>
            <p style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: visual.cor, fontWeight: 700, marginTop: 0 }}>
              <visual.Icone size={22} /> {visual.titulo}
            </p>
            <h2 style={{ margin: "0 0 0.75rem" }}>{dados.nome}</h2>
            <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.35rem 1rem", margin: 0 }}>
              <dt className="course-muted">Associação</dt>
              <dd style={{ margin: 0 }}>{dados.associacao}</dd>
              {dados.matricula && (
                <>
                  <dt className="course-muted">Matrícula</dt>
                  <dd style={{ margin: 0 }}>{dados.matricula}</dd>
                </>
              )}
              <dt className="course-muted">Categoria</dt>
              <dd style={{ margin: 0 }}>{dados.tipo || "—"}</dd>
              {dados.situacao === "em_dia" && (
                <>
                  <dt className="course-muted">Validade</dt>
                  <dd style={{ margin: 0 }}>{validadeTexto(dados)}</dd>
                </>
              )}
              {dados.membro_desde && (
                <>
                  <dt className="course-muted">Associado desde</dt>
                  <dd style={{ margin: 0 }}>{dataCurta(dados.membro_desde, true)}</dd>
                </>
              )}
            </dl>
            <p className="course-muted" style={{ marginBottom: 0, fontSize: "0.85rem" }}>
              Situação consultada em {new Date(dados.verificado_em).toLocaleString("pt-BR")}.
            </p>
          </div>
        )}
      </section>
    </SiteShell>
  );
}
