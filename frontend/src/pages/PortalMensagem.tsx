import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import ConversaThread from "@/components/mensagens/ConversaThread";
import { getMinhaConversa, responderMinhaConversa } from "@/services/mensagens";
import { apiErrorMessage } from "@/utils/apiError";
import type { Conversa } from "@/types/mensagens";

export default function PortalMensagem() {
  const { id = "" } = useParams();
  const [conversa, setConversa] = useState<Conversa | null>(null);
  const [erro, setErro] = useState("");

  const load = useCallback(async () => {
    try {
      setConversa(await getMinhaConversa(id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Conversa não encontrada."));
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const responder = async (texto: string) => {
    setErro("");
    try {
      setConversa(await responderMinhaConversa(id, texto));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar."));
      throw err;
    }
  };

  return (
    <div className="dashboard-page">
      <Link to="/app/portal/mensagens" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Mensagens
      </Link>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {conversa ? (
        <>
          <div className="dashboard-header">
            <h1 className="dashboard-title">{conversa.assunto}</h1>
            <p className="dashboard-subtitle">Conversa com a diretoria</p>
          </div>
          <ConversaThread conversa={conversa} diretoria={false} onResponder={responder} />
        </>
      ) : (
        !erro && (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
          </div>
        )
      )}
    </div>
  );
}
