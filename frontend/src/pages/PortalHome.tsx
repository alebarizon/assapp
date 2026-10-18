import { Link } from "react-router-dom";
import {
  ClipboardList,
  CreditCard,
  FileText,
  GraduationCap,
  MessageSquare,
  Library,
  ScrollText,
  ShoppingBag,
  UserRound,
} from "lucide-react";
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
        <p className="highlight-banner-title">Consulte perfil, anuidades, loja e documentos</p>
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
        <Link to="/app/portal/carteirinha" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <CreditCard size={20} />
            <div>
              <p className="list-card-title">Carteirinha</p>
              <p className="list-card-meta">Carteira de associado com QR code e situação da anuidade</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/trabalhos" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <ScrollText size={20} />
            <div>
              <p className="list-card-title">Trabalhos científicos</p>
              <p className="list-card-meta">Submeta trabalhos aos eventos e acompanhe a avaliação</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/cursos" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <GraduationCap size={20} />
            <div>
              <p className="list-card-title">Meus cursos</p>
              <p className="list-card-meta">Aulas, progresso e certificados</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/publicacoes" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <Library size={20} />
            <div>
              <p className="list-card-title">Publicações</p>
              <p className="list-card-meta">Dossiês, e-books e boletins da associação</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/formularios" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <ClipboardList size={20} />
            <div>
              <p className="list-card-title">Formulários</p>
              <p className="list-card-meta">Pesquisas e consultas da associação</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/mensagens" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <MessageSquare size={20} />
            <div>
              <p className="list-card-title">Mensagens</p>
              <p className="list-card-meta">Fale com a secretaria e a diretoria</p>
            </div>
          </div>
        </Link>
        <Link to="/app/portal/loja" className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <ShoppingBag size={20} />
            <div>
              <p className="list-card-title">Loja</p>
              <p className="list-card-meta">Anuidades, inscrições, cursos e materiais</p>
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
