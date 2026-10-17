import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Archive, ArchiveRestore, ArrowLeft } from "lucide-react";
import ConversaThread from "@/components/mensagens/ConversaThread";
import { arquivarConversa, getConversa, responderConversa } from "@/services/mensagens";
import { apiErrorMessage } from "@/utils/apiError";
import type { Conversa } from "@/types/mensagens";

export default function MensagemDetail() {
  const { id = "" } = useParams();
  const [conversa, setConversa] = useState<Conversa | null>(null);
  const [erro, setErro] = useState("");

  const load = useCallback(async () => {
    try {
      setConversa(await getConversa(id));
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
      setConversa(await responderConversa(id, texto));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao enviar."));
      throw err;
    }
  };

  const alternarArquivo = async () => {
    if (!conversa) return;
    try {
      await arquivarConversa(id, conversa.status === "aberta");
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao arquivar."));
    }
  };

  return (
    <div className="dashboard-page">
      <Link to="/app/mensagens" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Mensagens
      </Link>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {!conversa ? (
        !erro && (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
          </div>
        )
      ) : (
        <>
          <div className="dashboard-header dashboard-header-row">
            <div>
              <h1 className="dashboard-title">{conversa.assunto}</h1>
              <p className="dashboard-subtitle">
                <Link to={`/app/membros/${conversa.membro}`}>{conversa.membro_nome}</Link> · {conversa.membro_email}
                {conversa.status === "arquivada" && " · arquivada"}
              </p>
            </div>
            <div className="dashboard-header-actions">
              <button type="button" className="dashboard-btn-secondary" onClick={alternarArquivo}>
                {conversa.status === "aberta" ? (
                  <>
                    <Archive size={16} /> Arquivar
                  </>
                ) : (
                  <>
                    <ArchiveRestore size={16} /> Desarquivar
                  </>
                )}
              </button>
            </div>
          </div>
          <ConversaThread conversa={conversa} diretoria onResponder={responder} />
        </>
      )}
    </div>
  );
}
