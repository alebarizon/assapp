/** Agrupa atividades (já ordenadas por início) por dia, com rótulo "segunda-feira, 12 de outubro". */
export function agruparPorDia<T extends { inicio: string }>(itens: T[]): [string, T[]][] {
  const grupos = new Map<string, T[]>();
  for (const item of itens) {
    const rotulo = new Date(item.inicio).toLocaleDateString("pt-BR", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
    const dia = rotulo.charAt(0).toUpperCase() + rotulo.slice(1);
    grupos.set(dia, [...(grupos.get(dia) ?? []), item]);
  }
  return Array.from(grupos.entries());
}

/** "12 a 14 de outubro de 2026" ou "12 de outubro de 2026" (mesmo dia). */
export function periodoEvento(inicioIso: string, fimIso: string): string {
  const inicio = new Date(inicioIso);
  const fim = new Date(fimIso);
  const completo = (d: Date) => d.toLocaleDateString("pt-BR", { day: "numeric", month: "long", year: "numeric" });
  if (inicio.toDateString() === fim.toDateString()) return completo(inicio);
  if (inicio.getMonth() === fim.getMonth() && inicio.getFullYear() === fim.getFullYear()) {
    return `${inicio.getDate()} a ${completo(fim)}`;
  }
  return `${completo(inicio)} a ${completo(fim)}`;
}

export function hora(iso: string): string {
  return new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}
