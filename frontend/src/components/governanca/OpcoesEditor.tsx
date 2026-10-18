import { Plus, Trash2 } from "lucide-react";
import type { OpcaoVotacao } from "@/types/governanca";

export interface OpcaoForm {
  titulo: string;
  /** Uma linha por integrante: "Nome; Cargo". */
  integrantes: string;
}

export function opcoesParaForm(opcoes: OpcaoVotacao[]): OpcaoForm[] {
  return opcoes.map((o) => ({
    titulo: o.titulo,
    integrantes: (o.integrantes ?? []).map((i) => [i.nome, i.cargo].filter(Boolean).join("; ")).join("\n"),
  }));
}

export function opcoesParaPayload(opcoes: OpcaoForm[]): OpcaoVotacao[] {
  return opcoes
    .filter((o) => o.titulo.trim())
    .map((o) => ({
      titulo: o.titulo.trim(),
      integrantes: o.integrantes
        .split("\n")
        .map((l) => l.split(";").map((p) => p.trim()))
        .filter(([nome]) => nome)
        .map(([nome, cargo = ""]) => ({ nome, cargo })),
    }));
}

export default function OpcoesEditor({ opcoes, onChange }: { opcoes: OpcaoForm[]; onChange: (o: OpcaoForm[]) => void }) {
  const atualizar = (i: number, campo: keyof OpcaoForm, valor: string) =>
    onChange(opcoes.map((o, j) => (j === i ? { ...o, [campo]: valor } : o)));

  return (
    <div className="form-group">
      <label className="form-label">Chapas / candidatos</label>
      {opcoes.map((o, i) => (
        <div key={i} className="list-card" style={{ display: "block", marginBottom: "0.5rem" }}>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              className="form-input"
              placeholder={`Chapa ${i + 1}`}
              value={o.titulo}
              onChange={(e) => atualizar(i, "titulo", e.target.value)}
            />
            {opcoes.length > 2 && (
              <button type="button" className="dashboard-btn-danger" style={{ padding: "0.5rem 0.75rem" }} title="Remover" onClick={() => onChange(opcoes.filter((_, j) => j !== i))}>
                <Trash2 size={15} />
              </button>
            )}
          </div>
          <textarea
            className="form-input"
            rows={2}
            style={{ marginTop: "0.4rem" }}
            placeholder={"Integrantes (opcional), um por linha: Nome; Cargo"}
            value={o.integrantes}
            onChange={(e) => atualizar(i, "integrantes", e.target.value)}
          />
        </div>
      ))}
      <button type="button" className="dashboard-btn-secondary" onClick={() => onChange([...opcoes, { titulo: "", integrantes: "" }])}>
        <Plus size={14} /> Adicionar opção
      </button>
    </div>
  );
}
