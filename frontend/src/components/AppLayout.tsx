import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BookMarked,
  BookOpen,
  Calendar,
  FileText,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  UserRound,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { isMember } from "@/utils/roles";
import "./AppLayout.css";

export default function AppLayout() {
  const { user, logout, setupCompleted } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const boardNav = [
    { to: "/app/memoria", label: "Memória Institucional", icon: BookMarked },
    { to: "/app/membros", label: "Membros", icon: Users },
    { to: "/app/eventos", label: "Eventos", icon: Calendar },
    { to: "/app/mandatos", label: "Mandatos", icon: LayoutDashboard },
    { to: "/app/finance", label: "Financeiro", icon: Wallet },
    { to: "/app/documents", label: "Documentos", icon: FileText },
    { to: "/app/onboarding", label: "Onboarding", icon: BookOpen },
  ];

  const memberNav = [
    { to: "/app/portal", label: "Portal", icon: Home },
    { to: "/app/portal/perfil", label: "Meu perfil", icon: UserRound },
    { to: "/app/portal/documentos", label: "Meus documentos", icon: FileText },
  ];

  const setupNav = [{ to: "/app/setup", label: "Setup da associação", icon: Settings }];

  let nav = setupNav;
  if (setupCompleted) {
    nav = isMember(user?.role) ? memberNav : boardNav;
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
            <span style={{ fontSize: "0.8rem", color: "#666" }}>
              PIPE FAPESP · {user?.role === "member" ? "associado" : user?.perfil_tecnico || "—"}
            </span>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
