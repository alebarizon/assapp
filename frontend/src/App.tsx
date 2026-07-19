import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import AppLayout from "@/components/AppLayout";
import AssociationSetup from "@/pages/AssociationSetup";
import Login from "@/pages/Login";
import EventoDetail from "@/pages/EventoDetail";
import Eventos from "@/pages/Eventos";
import Mandatos from "@/pages/Mandatos";
import MandatoDetail from "@/pages/MandatoDetail";
import MembroDetail from "@/pages/MembroDetail";
import Membros from "@/pages/Membros";
import MemoriaInstitucional from "@/pages/MemoriaInstitucional";
import OnboardingWizard from "@/pages/OnboardingWizard";
import Finance from "@/pages/Finance";
import Documents from "@/pages/Documents";
import PortalHome from "@/pages/PortalHome";
import MeuPerfil from "@/pages/MeuPerfil";
import MeusDocumentos from "@/pages/MeusDocumentos";
import Signup from "@/pages/Signup";
import { homePathForRole, isMember } from "@/utils/roles";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="dashboard-loading" style={{ minHeight: "100vh" }}>
        <div className="loading-spinner" />
        <p>Carregando...</p>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function SetupGate({ children }: { children: React.ReactNode }) {
  const { setupCompleted, loading, tenantSchema, user } = useAuth();
  const location = useLocation();
  const onSetup = location.pathname.startsWith("/app/setup");
  const onPortal = location.pathname.startsWith("/app/portal");

  if (loading || setupCompleted === null) {
    return (
      <div className="dashboard-loading" style={{ minHeight: "40vh" }}>
        <div className="loading-spinner" />
        <p>Carregando...</p>
      </div>
    );
  }

  if (tenantSchema === "sistema") {
    if (onSetup) return <Navigate to="/app/memoria" replace />;
    return <>{children}</>;
  }

  // Associado: não passa por setup; fora do portal → redirect
  if (isMember(user?.role)) {
    if (onSetup) return <Navigate to="/app/portal" replace />;
    if (!onPortal) return <Navigate to="/app/portal" replace />;
    return <>{children}</>;
  }

  if (!setupCompleted && !onSetup) {
    return <Navigate to="/app/setup" replace />;
  }
  if (setupCompleted && onSetup) {
    return <Navigate to={homePathForRole(user?.role, true)} replace />;
  }
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/app"
        element={
          <PrivateRoute>
            <SetupGate>
              <AppLayout />
            </SetupGate>
          </PrivateRoute>
        }
      >
        <Route index element={<AppIndexRedirect />} />
        <Route path="setup" element={<AssociationSetup />} />
        <Route path="portal" element={<PortalHome />} />
        <Route path="portal/perfil" element={<MeuPerfil />} />
        <Route path="portal/documentos" element={<MeusDocumentos />} />
        <Route path="memoria" element={<MemoriaInstitucional />} />
        <Route path="membros" element={<Membros />} />
        <Route path="membros/:id" element={<MembroDetail />} />
        <Route path="eventos" element={<Eventos />} />
        <Route path="eventos/:id" element={<EventoDetail />} />
        <Route path="onboarding" element={<OnboardingWizard />} />
        <Route path="mandatos" element={<Mandatos />} />
        <Route path="mandatos/:id" element={<MandatoDetail />} />
        <Route path="finance" element={<Finance />} />
        <Route path="documents" element={<Documents />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function AppIndexRedirect() {
  const { user, setupCompleted } = useAuth();
  return <Navigate to={homePathForRole(user?.role, setupCompleted !== false).replace("/app/", "")} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
