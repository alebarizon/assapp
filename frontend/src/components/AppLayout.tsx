import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Eye,
  FileText,
  Home,
  LogOut,
  Menu,
  Settings,
  UserRound,
  X,
  ShoppingBag,
  GraduationCap,
  ClipboardList,
  MessageSquare,
  FileSearch,
  ScrollText,
  CreditCard,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { BOARD_NAV, PERFIL_LABEL, moduloDaRota } from "@/utils/modulos";
import { homePathForUser, isMember, isPortalUser, isReviewer, nivelModulo, podeVer } from "@/utils/roles";
import { listMeusPareceres } from "@/services/eventos";
import { buildTenantSiteQuery } from "@/utils/tenantSite";
import "./AppLayout.css";

export default function AppLayout() {
  const { user, logout, setupCompleted, tenantSchema } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [temPareceres, setTemPareceres] = useState(false);

  useEffect(() => {
    if (!user || !setupCompleted || isReviewer(user.role)) return;
    listMeusPareceres()
      .then((lista) => setTemPareceres(lista.length > 0))
      .catch(() => setTemPareceres(false));
  }, [user, setupCompleted]);

  const boardNav = BOARD_NAV.filter((item) => podeVer(user, item.modulo));
  const moduloAtual = moduloDaRota(location.pathname);
  const restrito = !isPortalUser(user?.role) && Boolean(user?.modulos);
  const semAcesso = restrito && moduloAtual !== null && !podeVer(user, moduloAtual);
  const somenteLeitura = restrito && moduloAtual !== null && nivelModulo(user, moduloAtual) === "leitura";

  const memberNav = [
    { to: "/app/portal", label: "Portal", icon: Home },
    { to: "/app/portal/cursos", label: "Meus cursos", icon: GraduationCap },
    { to: "/app/portal/formularios", label: "Formulários", icon: ClipboardList },
    { to: "/app/portal/mensagens", label: "Mensagens", icon: MessageSquare },
    { to: "/app/portal/trabalhos", label: "Trabalhos científicos", icon: ScrollText },
    ...(temPareceres ? [{ to: "/app/portal/pareceres", label: "Pareceres", icon: FileSearch }] : []),
    { to: "/app/portal/loja", label: "Loja", icon: ShoppingBag },
    { to: "/app/portal/carrinho", label: "Carrinho", icon: ShoppingBag },
    { to: "/app/portal/perfil", label: "Meu perfil", icon: UserRound },
    { to: "/app/portal/carteirinha", label: "Carteirinha", icon: CreditCard },
    { to: "/app/portal/documentos", label: "Meus documentos", icon: FileText },
  ];

  const reviewerNav = [
    { to: "/app/portal/pareceres", label: "Pareceres", icon: FileSearch },
    { to: "/app/portal/trabalhos", label: "Trabalhos científicos", icon: ScrollText },
  ];

  const setupNav = [{ to: "/app/setup", label: "Setup da associação", icon: Settings }];

  let nav = setupNav;
  if (isReviewer(user?.role)) {
    nav = reviewerNav;
  } else if (setupCompleted) {
    nav = isMember(user?.role)
      ? memberNav
      : [...boardNav, ...(temPareceres ? [{ to: "/app/pareceres", label: "Meus pareceres", icon: FileSearch }] : [])];
  }

  const initials =
    [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join("").toUpperCase() ||
    user?.email?.[0]?.toUpperCase() ||
    "A";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="main-layout">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-profile">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-profile-name">{user?.first_name || "AssApp"}</div>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setSidebarOpen(false)}
            aria-label="Fechar menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <ul className="nav-list">
            {nav.map(({ to, label, icon: Icon }) => (
              <li key={to} className="nav-item">
                <NavLink
                  to={to}
                  end={to === "/app/portal"}
                  className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon size={16} strokeWidth={1.75} />
                  <span className="nav-label">{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <p style={{ fontSize: "0.75rem", color: "#888", margin: "0 0 0.5rem", padding: "0 0.5rem" }}>
            {user?.email}
          </p>
          <button type="button" className="sidebar-logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <div className="main-content">
        <header className="main-header">
          <button
            type="button"
            className="menu-toggle"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu size={18} />
          </button>
          <div className="header-actions">
            {setupCompleted && !isPortalUser(user?.role) && tenantSchema && (
              <a
                href={`/site${buildTenantSiteQuery(tenantSchema)}`}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: "0.8rem", marginRight: "1rem" }}
              >
                Ver site público
              </a>
            )}
            <span style={{ fontSize: "0.8rem", color: "#666" }}>
              Gesttora ·{" "}
              {user?.role === "member"
                ? "associado"
                : user?.role === "reviewer"
                ? "parecerista"
                : (user?.perfis || []).map((p) => PERFIL_LABEL[p]).join(" + ") || "—"}
            </span>
          </div>
        </header>
        <main className="page-content">
          {somenteLeitura && (
            <div className="highlight-banner" style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "1rem" }}>
              <Eye size={16} /> Seu perfil tem acesso somente leitura a este módulo. Alterações serão recusadas.
            </div>
          )}
          {semAcesso ? (
            <div className="dashboard-page">
              <div className="dashboard-empty">
                <p style={{ marginBottom: "1rem" }}>Seu perfil não tem acesso a este módulo.</p>
                <Link to={homePathForUser(user)} className="dashboard-btn-secondary">
                  Voltar ao início
                </Link>
              </div>
            </div>
          ) : (
            <Outlet />
          )}
        </main>
      </div>
    </div>
  );
}
