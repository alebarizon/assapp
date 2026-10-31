import {
  BookMarked,
  BookOpen,
  Calendar,
  ClipboardList,
  FileText,
  Gavel,
  Globe,
  GraduationCap,
  Inbox,
  LayoutDashboard,
  Library,
  LifeBuoy,
  Mail,
  Plug,
  MessageSquare,
  ShoppingBag,
  UserCog,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import type { ModuloPainel, PerfilAcesso } from "@/types";

export const PERFIL_LABEL: Record<PerfilAcesso, string> = {
  gestor: "Gestor",
  diretoria: "Diretoria",
  administrativo: "Administrativo",
  financeiro: "Financeiro",
};

export const PERFIL_DESCRICAO: Record<PerfilAcesso, string> = {
  gestor: "Acesso total, inclusive usuários e configurações da associação.",
  diretoria: "Todos os módulos; financeiro e loja só para consulta.",
  administrativo: "Secretaria: associados, eventos, cursos, contatos, newsletter, site, documentos e publicações.",
  financeiro: "Tesouraria: financeiro, loja, anuidades e documentos.",
};

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  modulo: ModuloPainel;
}

export const BOARD_NAV: NavItem[] = [
  { to: "/app/memoria", label: "Memória Institucional", icon: BookMarked, modulo: "memoria" },
  { to: "/app/membros", label: "Membros", icon: Users, modulo: "membros" },
  { to: "/app/contatos", label: "Contatos", icon: Inbox, modulo: "contatos" },
  { to: "/app/mensagens", label: "Mensagens", icon: MessageSquare, modulo: "mensagens" },
  { to: "/app/newsletter", label: "Newsletter", icon: Mail, modulo: "newsletter" },
  { to: "/app/eventos", label: "Eventos", icon: Calendar, modulo: "eventos" },
  { to: "/app/courses", label: "Cursos", icon: GraduationCap, modulo: "cursos" },
  { to: "/app/formularios", label: "Formulários", icon: ClipboardList, modulo: "formularios" },
  { to: "/app/mandatos", label: "Mandatos", icon: LayoutDashboard, modulo: "mandatos" },
  { to: "/app/governanca", label: "Assembleias e votações", icon: Gavel, modulo: "governanca" },
  { to: "/app/finance", label: "Financeiro", icon: Wallet, modulo: "financeiro" },
  { to: "/app/website", label: "Website", icon: Globe, modulo: "website" },
  { to: "/app/ecommerce/catalog", label: "Loja — catálogo", icon: ShoppingBag, modulo: "loja" },
  { to: "/app/ecommerce/orders", label: "Loja — pedidos", icon: ShoppingBag, modulo: "loja" },
  { to: "/app/documents", label: "Documentos", icon: FileText, modulo: "documentos" },
  { to: "/app/publicacoes", label: "Publicações", icon: Library, modulo: "publicacoes" },
  { to: "/app/onboarding", label: "Onboarding", icon: BookOpen, modulo: "onboarding" },
  { to: "/app/usuarios", label: "Usuários e perfis", icon: UserCog, modulo: "usuarios" },
  { to: "/app/integracoes", label: "Integrações", icon: Plug, modulo: "integracoes" },
  { to: "/app/suporte", label: "Suporte", icon: LifeBuoy, modulo: "suporte" },
];

const PREFIXO_MODULO: [string, ModuloPainel][] = [
  ["/app/memoria", "memoria"],
  ["/app/membros", "membros"],
  ["/app/contatos", "contatos"],
  ["/app/mensagens", "mensagens"],
  ["/app/newsletter", "newsletter"],
  ["/app/eventos", "eventos"],
  ["/app/courses", "cursos"],
  ["/app/formularios", "formularios"],
  ["/app/mandatos", "mandatos"],
  ["/app/governanca", "governanca"],
  ["/app/finance", "financeiro"],
  ["/app/website", "website"],
  ["/app/ecommerce", "loja"],
  ["/app/documents", "documentos"],
  ["/app/publicacoes", "publicacoes"],
  ["/app/onboarding", "onboarding"],
  ["/app/usuarios", "usuarios"],
  ["/app/integracoes", "integracoes"],
  ["/app/suporte", "suporte"],
];

export function moduloDaRota(pathname: string): ModuloPainel | null {
  const hit = PREFIXO_MODULO.find(([prefixo]) => pathname === prefixo || pathname.startsWith(`${prefixo}/`));
  return hit ? hit[1] : null;
}
