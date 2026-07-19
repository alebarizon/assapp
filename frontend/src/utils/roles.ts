/** Helpers de role — portal associado vs painel da diretoria */

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

export function homePathForRole(role?: string | null, setupCompleted = true): string {
  if (!setupCompleted && isBoardOrAdmin(role)) return "/app/setup";
  if (isMember(role)) return "/app/portal";
  return "/app/memoria";
}
