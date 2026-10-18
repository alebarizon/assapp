import React, { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { abrirCfp } from "@/services/eventos";
import type { CriterioAvaliacao, EventoAcademico } from "@/types/eventos";
import { apiErrorMessage } from "@/utils/apiError";

const CRITERIOS_SUGERIDOS: CriterioAvaliacao[] = [
  { nome: "Relevância e originalidade", peso: 2 },
  { nome: "Rigor metodológico", peso: 2 },
  { nome: "Clareza da escrita", peso: 1 },
  { nome: "Adequação à área temática", peso: 1 },
];

function paraInputLocal(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

interface Props {
  evento: EventoAcademico;
  podeEditar: boolean;
  onSalvo: () => void;
}

export default function ChamadaTrabalhos({ evento, podeEditar, onSalvo }: Props) {
  const cfp = evento.call_for_papers;
  const [editando, setEditando] = useState(!cfp);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [form, setForm] = useState({
    titulo: cfp?.titulo ?? `Chamada de trabalhos — ${evento.titulo}`,
    instrucoes: cfp?.instrucoes ?? "Resumos expandidos de até 500 palavras, em português ou inglês.",
    data_abertura: paraInputLocal(cfp?.data_abertura),
    data_fechamento: paraInputLocal(cfp?.data_fechamento),
    areas: cfp?.areas_tematicas.join(", ") ?? "",
    max_submissoes_por_autor: cfp?.max_submissoes_por_autor ?? 3,
    anonimo: cfp?.anonimo ?? true,
    exige_arquivo: cfp?.exige_arquivo ?? false,
    nota_corte: cfp?.nota_corte ?? "",
    criterios: cfp?.criterios.length ? cfp.criterios : CRITERIOS_SUGERIDOS,
  });

  const setCriterio = (i: number, campo: keyof CriterioAvaliacao, valor: string) =>
    setForm({
      ...form,
      criterios: form.criterios.map((c, j) =>
        j === i ? { ...c, [campo]: campo === "peso" ? Number(valor) : valor } : c
      ),
    });

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setSalvando(true);
    try {
      await abrirCfp(evento.id, {
        titulo: form.titulo,
        instrucoes: form.instrucoes,
        data_abertura: new Date(form.data_abertura).toISOString(),
        data_fechamento: new Date(form.data_fechamento).toISOString(),
        areas_tematicas: form.areas.split(",").map((a) => a.trim()).filter(Boolean),
        max_submissoes_por_autor: form.max_submissoes_por_autor,
        anonimo: form.anonimo,
        exige_arquivo: form.exige_arquivo,
        nota_corte: form.nota_corte || null,
        criterios: form.criterios.filter((c) => c.nome.trim()),
      });
      setEditando(false);
      onSalvo();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível salvar a chamada."));
    } finally {
      setSalvando(false);
    }
  };

  if (!editando && cfp) {
    return (
      <div className="dashboard-content-panel">
        <div className="filters-row" style={{ justifyContent: "space-between" }}>
          <div>
            <p className="list-card-title">{cfp.titulo}</p>
            <p className="list-card-meta">
              {new Date(cfp.data_abertura).toLocaleString("pt-BR")} até{" "}
              {new Date(cfp.data_fechamento).toLocaleString("pt-BR")} ·{" "}
              {cfp.aberta ? "recebendo submissões" : "fora do período de submissão"}
            </p>
          </div>
          {podeEditar && (
            <button type="button" className="dashboard-btn-edit" onClick={() => setEditando(true)}>
              Editar chamada
            </button>
          )}
        </div>
        <p className="list-card-meta" style={{ whiteSpace: "pre-wrap" }}>{cfp.instrucoes}</p>
        <p className="list-card-meta">Áreas: {cfp.areas_tematicas.join(", ") || "livre"}</p>
        <p className="list-card-meta">
          Parecer duplo-cego: {cfp.anonimo ? "sim" : "não"} · Arquivo obrigatório: {cfp.exige_arquivo ? "sim" : "não"} ·
          Até {cfp.max_submissoes_por_autor} trabalho(s) por autor
          {cfp.nota_corte ? ` · Nota de corte ${cfp.nota_corte}` : ""}
        </p>
        <p className="list-card-meta">
          Critérios (nota de 1 a 5, média ponderada):{" "}
          {cfp.criterios_efetivos.map((c) => `${c.nome} (peso ${c.peso})`).join(" · ")}
        </p>
      </div>
    );
  }

  if (!podeEditar) {
    return <div className="dashboard-empty">Este evento não tem chamada de trabalhos.</div>;
  }

  return (
    <div className="page-form-container">
      <form className="page-form" onSubmit={salvar}>
        <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
          {cfp ? "Editar chamada de trabalhos" : "Abrir chamada de trabalhos"}
        </h3>
        {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
        <div className="form-group">
          <label className="form-label">Título</label>
          <input
            className="form-input"
            required
            value={form.titulo}
            onChange={(e) => setForm({ ...form, titulo: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Instruções aos autores</label>
          <textarea
            className="form-input"
            rows={3}
            value={form.instrucoes}
            onChange={(e) => setForm({ ...form, instrucoes: e.target.value })}
          />
        </div>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Abertura</label>
            <input
              className="form-input"
              required
              type="datetime-local"
              value={form.data_abertura}
              onChange={(e) => setForm({ ...form, data_abertura: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Encerramento</label>
            <input
              className="form-input"
              required
              type="datetime-local"
              value={form.data_fechamento}
              onChange={(e) => setForm({ ...form, data_fechamento: e.target.value })}
            />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Áreas temáticas (separadas por vírgula)</label>
          <input
            className="form-input"
            placeholder="Ex.: Ensino, Pesquisa, Extensão"
            value={form.areas}
            onChange={(e) => setForm({ ...form, areas: e.target.value })}
          />
        </div>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Máximo de trabalhos por autor</label>
            <input
              className="form-input"
              type="number"
              min={1}
              value={form.max_submissoes_por_autor}
              onChange={(e) => setForm({ ...form, max_submissoes_por_autor: Number(e.target.value) })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Nota de corte (1 a 5, opcional)</label>
            <input
              className="form-input"
              type="number"
              min={1}
              max={5}
              step={0.1}
              value={form.nota_corte}
              onChange={(e) => setForm({ ...form, nota_corte: e.target.value })}
            />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input
              type="checkbox"
              checked={form.anonimo}
              onChange={(e) => setForm({ ...form, anonimo: e.target.checked })}
            />
            Parecer duplo-cego (pareceristas não veem os autores)
          </label>
          <label className="form-label" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input
              type="checkbox"
              checked={form.exige_arquivo}
              onChange={(e) => setForm({ ...form, exige_arquivo: e.target.checked })}
            />
            Exigir arquivo do trabalho (PDF, DOC, DOCX ou ODT)
          </label>
        </div>

        <div className="form-group">
          <label className="form-label">Critérios de avaliação (o parecerista dá nota de 1 a 5 em cada um)</label>
          {form.criterios.map((c, i) => (
            <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <input
                className="form-input"
                style={{ flex: 1 }}
                placeholder="Critério"
                value={c.nome}
                onChange={(e) => setCriterio(i, "nome", e.target.value)}
              />
              <select
                className="form-select"
                style={{ width: "7rem" }}
                value={c.peso}
                onChange={(e) => setCriterio(i, "peso", e.target.value)}
                aria-label="Peso"
              >
                {[1, 2, 3, 4, 5].map((p) => (
                  <option key={p} value={p}>Peso {p}</option>
                ))}
              </select>
              <button
                type="button"
                className="dashboard-btn-cancel"
                aria-label="Remover critério"
                onClick={() => setForm({ ...form, criterios: form.criterios.filter((_, j) => j !== i) })}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          <button
            type="button"
            className="dashboard-btn-secondary"
            onClick={() => setForm({ ...form, criterios: [...form.criterios, { nome: "", peso: 1 }] })}
          >
            <Plus size={14} /> Adicionar critério
          </button>
        </div>

        <div className="form-actions">
          {cfp && (
            <button type="button" className="dashboard-btn-cancel" onClick={() => setEditando(false)}>
              Cancelar
            </button>
          )}
          <button type="submit" className="dashboard-btn-save" disabled={salvando}>
            {salvando ? "Salvando..." : cfp ? "Salvar chamada" : "Abrir chamada"}
          </button>
        </div>
      </form>
    </div>
  );
}
