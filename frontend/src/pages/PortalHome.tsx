import { Link } from "react-router-dom";
import { FileText, UserRound } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function PortalHome() {
  const { user } = useAuth();
  const nome = user?.membro_nome || user?.first_name || "Associado";

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Portal do associado</h1>
        <p className="dashboard-subtitle">Olá, {nome}</p>
      </div>

      <div className="highlight-banner" style={{ marginBottom: "1.25rem" }}>
        <p className="highlight-banner-label">Sua área na associação</p>
        <p className="highlight-banner-title">Consulte perfil, anuidades e documentos</p>
        <p className="highlight-banner-meta">
          Acesso somente leitura — gestão completa fica com a diretoria.
        </p>
      </div>

      <div className="list-stack">
        <Link to="/app/portal/perfil" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <UserRound size={20} />
            <div>
              <p className="list-card-title">Meu perfil</p>
              <p className="list-card-meta">Dados cadastrais, filiação e anuidades</p>
            </div>
          </div>
        </Link>
        <Link
          to="/app/portal/documentos"
          className="list-card"
          style={{ textDecoration: "none", color: "inherit" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <FileText size={20} />
            <div>
              <p className="list-card-title">Meus documentos</p>
              <p className="list-card-meta">Arquivos gerais da associação e documentos seus</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
