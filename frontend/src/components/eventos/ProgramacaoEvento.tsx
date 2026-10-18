import React, { useEffect, useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import type { AtividadeProgramacao, EventoAcademico, TipoAtividade } from "@/types/eventos";
import { TIPOS_ATIVIDADE } from "@/types/eventos";
import { deleteAtividade, listProgramacao, salvarAtividade } from "@/services/eventos";
import { agruparPorDia, hora } from "@/utils/programacao";

/** ISO → valor de <input type="datetime-local"> no fuso do navegador. */
function paraInput(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const formVazio = (evento: EventoAcademico) => ({
  id: undefined as string | undefined,
  titulo: "",
  tipo: "palestra" as TipoAtividade,
  inicio: paraInput(evento.data_inicio),
  fim: paraInput(new Date(new Date(evento.data_inicio).getTime() + 60 * 60 * 1000).toISOString()),
  sala: "",
  responsaveis: "",
  descricao: "",
  link_transmissao: "",
});

function mensagemErro(err: unknown, padrao: string): string {
  const data = (err as { response?: { data?: Record<string, string | string[]> } })?.response?.data;
  if (!data) return padrao;
  const primeiro = data.detail ?? Object.values(data)[0];
  return String((Array.isArray(primeiro) ? primeiro[0] : primeiro) || padrao);
}

export default function ProgramacaoEvento({ evento }: { evento: EventoAcademico }) {
  const [atividades, setAtividades] = useState<AtividadeProgramacao[]>([]);
  const [form, setForm] = useState(formVazio(evento));
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);

  const carregar = () => listProgramacao(evento.id).then(setAtividades);

  useEffect(() => {
    void carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evento.id]);

  const editar = (a: AtividadeProgramacao) => {
    setForm({ ...a, inicio: paraInput(a.inicio), fim: paraInput(a.fim) });
    setAberto(true);
  };

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      await salvarAtividade({
        ...form,
        evento: evento.id,
        inicio: new Date(form.inicio).toISOString(),
        fim: new Date(form.fim).toISOString(),
      });
      // Próxima atividade começa onde esta terminou
      const umaHoraDepois = new Date(new Date(form.fim).getTime() + 60 * 60 * 1000).toISOString();
      setForm({ ...formVazio(evento), inicio: form.fim, fim: paraInput(umaHoraDepois), sala: form.sala });
      setAberto(Boolean(!form.id));
      await carregar();
    } catch (err) {
      setErro(mensagemErro(err, "Não foi possível salvar a atividade."));
    } finally {
      setSalvando(false);
    }
  };

  const remover = async (a: AtividadeProgramacao) => {
    if (!confirm(`Remover "${a.titulo}" da programação?`)) return;
    await deleteAtividade(a.id);
    await carregar();
  };

  return (
    <div className="dashboard-content-panel">
      <div className="filters-row" style={{ justifyContent: "space-between" }}>
        <p className="list-card-meta" style={{ margin: 0 }}>
          Grade exibida no hotsite do evento, em ordem de horário.
        </p>
        {!aberto && (
          <button
            type="button"
            className="dashboard-btn-new"
            onClick={() => {
              setForm(formVazio(evento));
              setAberto(true);
            }}
          >
            <Plus size={14} /> Nova atividade
          </button>
        )}
      </div>

      {aberto && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={salvar}>
            {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Título *</label>
                <input
                  className="form-input"
                  required
                  value={form.titulo}
                  onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tipo</label>
                <select
                  className="form-select"
                  value={form.tipo}
                  onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoAtividade })}
                >
                  {TIPOS_ATIVIDADE.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-row-3">
              <div className="form-group">
                <label className="form-label">Início *</label>
                <input
                  className="form-input"
                  type="datetime-local"
                  required
                  value={form.inicio}
                  onChange={(e) => setForm({ ...form, inicio: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Término *</label>
                <input
                  className="form-input"
                  type="datetime-local"
                  required
                  value={form.fim}
                  onChange={(e) => setForm({ ...form, fim: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Sala / local</label>
                <input
                  className="form-input"
                  value={form.sala}
                  onChange={(e) => setForm({ ...form, sala: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Palestrantes / mediação</label>
              <input
                className="form-input"
                value={form.responsaveis}
                onChange={(e) => setForm({ ...form, responsaveis: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Descrição</label>
              <textarea
                className="form-input"
                rows={2}
                value={form.descricao}
                onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Link da transmissão (YouTube, Meet...)</label>
              <input
                className="form-input"
                type="url"
                value={form.link_transmissao}
                onChange={(e) => setForm({ ...form, link_transmissao: e.target.value })}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setAberto(false)}>
                Fechar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Salvando..." : form.id ? "Salvar alterações" : "Adicionar"}
              </button>
            </div>
          </form>
        </div>
      )}

      {atividades.length === 0 ? (
        <div className="dashboard-empty">Nenhuma atividade na programação.</div>
      ) : (
        agruparPorDia(atividades).map(([dia, itens]) => (
          <div key={dia} style={{ marginBottom: "1.25rem" }}>
            <p className="list-card-title">
              {dia}
            </p>
            <div className="list-stack">
              {itens.map((a) => (
                <div key={a.id} className="list-card">
                  <div>
                    <p className="list-card-title">
                      {hora(a.inicio)}–{hora(a.fim)} · {a.titulo}
                    </p>
                    <p className="list-card-meta">
                      {[a.tipo_display, a.sala, a.responsaveis].filter(Boolean).join(" · ")}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button type="button" className="dashboard-btn-edit" onClick={() => editar(a)}>
                      <Pencil size={14} />
                    </button>
                    <button type="button" className="dashboard-btn-cancel" onClick={() => remover(a)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
