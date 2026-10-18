import type { Carteirinha, SituacaoCarteirinha } from "@/types/membros";
import "./Membros.css";

export const BADGE_SITUACAO: Record<SituacaoCarteirinha, string> = {
  em_dia: "ativa",
  pendente: "pendente",
  inativo: "rejeitado",
};

/** Datas `YYYY-MM-DD` sem passar por UTC (evita mostrar o dia anterior). */
export function dataCurta(iso: string | null, mesAno = false): string {
  if (!iso) return "—";
  const [ano, mes, dia] = iso.slice(0, 10).split("-");
  return mesAno ? `${mes}/${ano}` : `${dia}/${mes}/${ano}`;
}

export function validadeTexto(c: { honoraria: boolean; valida_ate: string | null }): string {
  if (c.honoraria) return "Sócio honorário";
  return dataCurta(c.valida_ate);
}

export default function CartaoAssociado({ carteirinha: c }: { carteirinha: Carteirinha }) {
  return (
    <div className="cartao-associado" aria-label="Carteirinha do associado">
      <div className="cartao-associado-topo">
        <div className="cartao-associado-assoc">{c.associacao}</div>
        <div className="cartao-associado-sub">Carteira de associado</div>
      </div>
      <div className="cartao-associado-corpo">
        <div className="cartao-associado-dados">
          <div className="cartao-associado-nome" title={c.nome}>{c.nome}</div>
          <div className="cartao-associado-campo">Matrícula</div>
          <div className="cartao-associado-valor">{c.matricula}</div>
          <div className="cartao-associado-campo">Categoria</div>
          <div className="cartao-associado-valor">{c.tipo || "—"}</div>
          <div className="cartao-associado-campo">Validade</div>
          <div className="cartao-associado-valor">{validadeTexto(c)}</div>
        </div>
        <div className="cartao-associado-qr">
          <img src={c.qr} alt="QR code de verificação da carteirinha" />
        </div>
      </div>
    </div>
  );
}
