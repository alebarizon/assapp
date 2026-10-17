import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import FormResponder from "@/components/formularios/FormResponder";
import { useTenantSchema } from "@/components/tenant-site/TenantSiteLayout";
import { enviarFormularioPublico, getConvite, getFormularioPublico, responderConvite } from "@/services/formularios";
import type { FormularioParaResponder } from "@/types/formularios";
import "@/components/formularios/Formularios.css";

/** Resposta sem login: link aberto (`/site/formularios/:token`) ou convite (`/site/formularios/convite/:token`). */
export default function PublicFormulario({ convite = false }: { convite?: boolean }) {
  const { token = "" } = useParams();
  const schema = useTenantSchema();
  const [formulario, setFormulario] = useState<FormularioParaResponder | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    setErro("");
    (convite ? getConvite(schema, token) : getFormularioPublico(schema, token))
      .then(setFormulario)
      .catch(() => setErro("Formulário não encontrado ou indisponível."));
  }, [schema, token, convite]);

  return (
    <div className="form-public-page">
      <div className="form-public-card">
        {erro && <p>{erro}</p>}
        {!formulario && !erro && <p>Carregando…</p>}
        {formulario && (
          <>
            {formulario.associacao && <div className="form-public-brand">{formulario.associacao}</div>}
            <h1 style={{ margin: "0 0 0.5rem" }}>{formulario.titulo}</h1>
            {formulario.evento_titulo && <p className="fb-muted" style={{ marginTop: 0 }}>Evento: {formulario.evento_titulo}</p>}
            {convite && formulario.nome && <p>Olá, {formulario.nome.split(" ")[0]}!</p>}
            {formulario.descricao && <p style={{ whiteSpace: "pre-wrap", color: "#444" }}>{formulario.descricao}</p>}
            <FormResponder
              formulario={formulario}
              permitirRascunho={convite}
              pedirIdentificacao={!convite && formulario.pedir_identificacao}
              onEnviar={(answers, enviar, ident) =>
                convite
                  ? responderConvite(schema, token, answers, enviar)
                  : enviarFormularioPublico(schema, token, { ...ident, answers })
              }
            />
          </>
        )}
      </div>
    </div>
  );
}
