import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import FormResponder from "@/components/formularios/FormResponder";
import { getMeuFormulario, salvarMeuFormulario } from "@/services/formularios";
import { apiErrorMessage } from "@/utils/apiError";
import type { FormularioParaResponder } from "@/types/formularios";
import "@/components/formularios/Formularios.css";

export default function PortalFormulario() {
  const { id = "" } = useParams();
  const [formulario, setFormulario] = useState<FormularioParaResponder | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getMeuFormulario(id)
      .then(setFormulario)
      .catch((err) => setErro(apiErrorMessage(err, "Formulário não encontrado.")));
  }, [id]);

  return (
    <div className="dashboard-page">
      <Link to="/app/portal/formularios" className="fb-muted" style={{ display: "inline-flex", gap: "0.25rem" }}>
        <ArrowLeft size={14} /> Formulários
      </Link>
      {erro && <div className="alert-banner alert-banner-error" style={{ marginTop: "1rem" }}>{erro}</div>}
      {formulario && (
        <>
          <div className="dashboard-header" style={{ marginTop: "0.5rem" }}>
            <h1 className="dashboard-title">{formulario.titulo}</h1>
            {formulario.descricao && (
              <p className="dashboard-subtitle" style={{ whiteSpace: "pre-wrap" }}>
                {formulario.descricao}
              </p>
            )}
          </div>
          <div className="page-form-container">
            <FormResponder
              formulario={formulario}
              permitirRascunho
              onEnviar={(answers, enviar) => salvarMeuFormulario(formulario.id, answers, enviar)}
              acaoFinal={
                <Link to="/app/portal/formularios" className="dashboard-btn-secondary">
                  Voltar aos formulários
                </Link>
              }
            />
          </div>
        </>
      )}
    </div>
  );
}
