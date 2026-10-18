/** Helpers de role e perfis de acesso — portal associado vs painel da equipe */
import type { ModuloPainel, NivelAcesso, User } from "@/types";

const BOARD_ROLES = new Set([
  "superadmin",
  "association_admin",
  "board_member",
]);

export function isBoardOrAdmin(role?: string | null): boolean {
  return Boolean(role && BOARD_ROLES.has(role));
}

export function isMember(role?: string | null): boolean {
  return role === "member";
}

/** Parecerista externo: sem cadastro de associado nem acesso ao painel. */
export function isReviewer(role?: string | null): boolean {
  return role === "reviewer";
}

/** Usuários que navegam pelo portal (`/app/portal/*`), não pelo painel da equipe. */
export function isPortalUser(role?: string | null): boolean {
  return isMember(role) || isReviewer(role);
}

export function nivelModulo(user: User | null | undefined, modulo: ModuloPainel): NivelAcesso | null {
  return user?.modulos?.[modulo] ?? null;
}

export function podeVer(user: User | null | undefined, modulo: ModuloPainel): boolean {
  return nivelModulo(user, modulo) !== null;
}

export function podeEditar(user: User | null | undefined, modulo: ModuloPainel): boolean {
  return nivelModulo(user, modulo) === "total";
}

export function isGestor(user: User | null | undefined): boolean {
  return podeEditar(user, "usuarios");
}

/** Ordem de preferência da página inicial da equipe. */
const HOME_POR_MODULO: [ModuloPainel, string][] = [
  ["memoria", "/app/memoria"],
  ["membros", "/app/membros"],
  ["financeiro", "/app/finance"],
  ["eventos", "/app/eventos"],
  ["contatos", "/app/contatos"],
  ["documentos", "/app/documents"],
  ["suporte", "/app/suporte"],
];

export function homePathForUser(user: User | null | undefined, setupCompleted = true): string {
  if (!setupCompleted && isBoardOrAdmin(user?.role)) return "/app/setup";
  if (isMember(user?.role)) return "/app/portal";
  if (isReviewer(user?.role)) return "/app/portal/pareceres";
  if (!user?.modulos) return "/app/memoria";
  const destino = HOME_POR_MODULO.find(([m]) => podeVer(user, m));
  return destino ? destino[1] : "/app/suporte";
}
