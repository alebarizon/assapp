import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import AppLayout from "@/components/AppLayout";
import GoogleAnalytics from "@/components/GoogleAnalytics";
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
import EcommerceCatalog from "@/pages/EcommerceCatalog";
import EcommerceOrders from "@/pages/EcommerceOrders";
import PortalLoja from "@/pages/PortalLoja";
import PortalCarrinho from "@/pages/PortalCarrinho";
import PortalHome from "@/pages/PortalHome";
import MeuPerfil from "@/pages/MeuPerfil";
import MeusDocumentos from "@/pages/MeusDocumentos";
import Signup from "@/pages/Signup";
import GesttoraLanding from "@/pages/GesttoraLanding";
import TenantSiteHome from "@/pages/TenantSiteHome";
import TenantSitePage from "@/pages/TenantSitePage";
import WebsiteAdmin from "@/pages/WebsiteAdmin";
import Courses from "@/pages/Courses";
import CourseDetail from "@/pages/CourseDetail";
import MeusCursos from "@/pages/MeusCursos";
import CoursePlayer from "@/pages/CoursePlayer";
import TenantSiteCourses from "@/pages/TenantSiteCourses";
import TenantSiteEventos from "@/pages/TenantSiteEventos";
import TenantSiteEventoDetail from "@/pages/TenantSiteEventoDetail";
import TenantSiteAnais from "@/pages/TenantSiteAnais";
import TenantSiteTrabalho from "@/pages/TenantSiteTrabalho";
import TenantSiteCarteirinha from "@/pages/TenantSiteCarteirinha";
import MinhaCarteirinha from "@/pages/MinhaCarteirinha";
import Publicacoes from "@/pages/Publicacoes";
import Governanca from "@/pages/Governanca";
import AssembleiaDetail from "@/pages/AssembleiaDetail";
import VotacaoDetail from "@/pages/VotacaoDetail";
import MinhaGovernanca from "@/pages/MinhaGovernanca";
import Newsletter from "@/pages/Newsletter";
import Integracoes from "@/pages/Integracoes";
import CampanhaDetail from "@/pages/CampanhaDetail";
import TenantSiteDescadastrar from "@/pages/TenantSiteDescadastrar";
import TenantSiteDiretorio from "@/pages/TenantSiteDiretorio";
import MinhasPublicacoes from "@/pages/MinhasPublicacoes";
import TenantSitePublicacoes from "@/pages/TenantSitePublicacoes";
import TenantSitePublicacao from "@/pages/TenantSitePublicacao";
import TenantSiteCourseDetail from "@/pages/TenantSiteCourseDetail";
import TenantSiteCertificate from "@/pages/TenantSiteCertificate";
import Formularios from "@/pages/Formularios";
import FormularioDetail from "@/pages/FormularioDetail";
import MeusFormularios from "@/pages/MeusFormularios";
import PortalFormulario from "@/pages/PortalFormulario";
import PublicFormulario from "@/pages/PublicFormulario";
import Contatos from "@/pages/Contatos";
import ContatoDetail from "@/pages/ContatoDetail";
import Suporte from "@/pages/Suporte";
import SuporteDetail from "@/pages/SuporteDetail";
import Mensagens from "@/pages/Mensagens";
import MensagemDetail from "@/pages/MensagemDetail";
import MinhasMensagens from "@/pages/MinhasMensagens";
import PortalMensagem from "@/pages/PortalMensagem";
import MeusTrabalhos from "@/pages/MeusTrabalhos";
import MeusPareceres from "@/pages/MeusPareceres";
import Usuarios from "@/pages/Usuarios";
import DefinirSenha from "@/pages/DefinirSenha";
import EsqueciSenha from "@/pages/EsqueciSenha";
import { homePathForUser, isMember, isReviewer } from "@/utils/roles";

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

  if (isReviewer(user?.role)) {
    const permitido = ["/app/portal/pareceres", "/app/portal/trabalhos"].some((p) =>
      location.pathname.startsWith(p)
    );
    return permitido ? <>{children}</> : <Navigate to="/app/portal/pareceres" replace />;
  }

  if (!setupCompleted && !onSetup) {
    return <Navigate to="/app/setup" replace />;
  }
  if (setupCompleted && onSetup) {
    return <Navigate to={homePathForUser(user, true)} replace />;
  }
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<GesttoraLanding />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/esqueci-senha" element={<EsqueciSenha />} />
      <Route path="/definir-senha" element={<DefinirSenha />} />
      <Route path="/site" element={<TenantSiteHome />} />
      <Route path="/site/p/:slug" element={<TenantSitePage />} />
      <Route path="/site/cursos" element={<TenantSiteCourses />} />
      <Route path="/site/cursos/:slug" element={<TenantSiteCourseDetail />} />
      <Route path="/site/eventos" element={<TenantSiteEventos />} />
      <Route path="/site/eventos/:slug" element={<TenantSiteEventoDetail />} />
      <Route path="/site/eventos/:slug/anais" element={<TenantSiteAnais />} />
      <Route path="/site/eventos/:slug/anais/:trabalho" element={<TenantSiteTrabalho />} />
      <Route path="/site/certificados" element={<TenantSiteCertificate />} />
      <Route path="/site/carteirinha/:codigo" element={<TenantSiteCarteirinha />} />
      <Route path="/site/publicacoes" element={<TenantSitePublicacoes />} />
      <Route path="/site/publicacoes/:slug" element={<TenantSitePublicacao />} />
      <Route path="/site/descadastrar" element={<TenantSiteDescadastrar />} />
      <Route path="/site/associados" element={<TenantSiteDiretorio />} />
      <Route path="/site/formularios/:token" element={<PublicFormulario />} />
      <Route path="/site/formularios/convite/:token" element={<PublicFormulario convite />} />
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
        <Route path="portal/carteirinha" element={<MinhaCarteirinha />} />
        <Route path="portal/documentos" element={<MeusDocumentos />} />
        <Route path="portal/publicacoes" element={<MinhasPublicacoes />} />
        <Route path="portal/governanca" element={<MinhaGovernanca />} />
        <Route path="portal/loja" element={<PortalLoja />} />
        <Route path="portal/carrinho" element={<PortalCarrinho />} />
        <Route path="portal/cursos" element={<MeusCursos />} />
        <Route path="portal/cursos/:enrollmentId/lessons/:lessonId" element={<CoursePlayer />} />
        <Route path="portal/formularios" element={<MeusFormularios />} />
        <Route path="portal/formularios/:id" element={<PortalFormulario />} />
        <Route path="portal/mensagens" element={<MinhasMensagens />} />
        <Route path="portal/mensagens/:id" element={<PortalMensagem />} />
        <Route path="portal/trabalhos" element={<MeusTrabalhos />} />
        <Route path="portal/pareceres" element={<MeusPareceres />} />
        <Route path="pareceres" element={<MeusPareceres />} />
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
        <Route path="publicacoes" element={<Publicacoes />} />
        <Route path="governanca" element={<Governanca />} />
        <Route path="governanca/assembleias/:id" element={<AssembleiaDetail />} />
        <Route path="governanca/votacoes/:id" element={<VotacaoDetail />} />
        <Route path="newsletter" element={<Newsletter />} />
        <Route path="integracoes" element={<Integracoes />} />
        <Route path="newsletter/:id" element={<CampanhaDetail />} />
        <Route path="ecommerce/catalog" element={<EcommerceCatalog />} />
        <Route path="ecommerce/orders" element={<EcommerceOrders />} />
        <Route path="website" element={<WebsiteAdmin />} />
        <Route path="courses" element={<Courses />} />
        <Route path="courses/:id" element={<CourseDetail />} />
        <Route path="formularios" element={<Formularios />} />
        <Route path="formularios/:id" element={<FormularioDetail />} />
        <Route path="contatos" element={<Contatos />} />
        <Route path="contatos/:id" element={<ContatoDetail />} />
        <Route path="suporte" element={<Suporte />} />
        <Route path="suporte/:id" element={<SuporteDetail />} />
        <Route path="mensagens" element={<Mensagens />} />
        <Route path="mensagens/:id" element={<MensagemDetail />} />
        <Route path="usuarios" element={<Usuarios />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function AppIndexRedirect() {
  const { user, setupCompleted } = useAuth();
  return <Navigate to={homePathForUser(user, setupCompleted !== false).replace("/app/", "")} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <GoogleAnalytics />
      <AppRoutes />
    </AuthProvider>
  );
}
