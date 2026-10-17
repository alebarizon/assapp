import { ArrowDown, ArrowUp, Copy, Plus, Trash2 } from "lucide-react";
import type { Pergunta, PerguntaTipo, Secao } from "@/types/formularios";
import { PERGUNTA_TIPOS, novaPergunta } from "@/types/formularios";

interface FormBuilderProps {
  secoes: Secao[];
  onChange: (secoes: Secao[]) => void;
}

function mover<T>(lista: T[], index: number, delta: number): T[] {
  const alvo = index + delta;
  if (alvo < 0 || alvo >= lista.length) return lista;
  const copia = [...lista];
  [copia[index], copia[alvo]] = [copia[alvo], copia[index]];
  return copia;
}

export default function FormBuilder({ secoes, onChange }: FormBuilderProps) {
  const updateSecao = (sIndex: number, patch: Partial<Secao>) =>
    onChange(secoes.map((s, i) => (i === sIndex ? { ...s, ...patch } : s)));

  const updatePergunta = (sIndex: number, pIndex: number, patch: Partial<Pergunta>) =>
    updateSecao(sIndex, {
      perguntas: secoes[sIndex].perguntas.map((p, i) => (i === pIndex ? { ...p, ...patch } : p)),
    });

  const changeTipo = (sIndex: number, pIndex: number, tipo: PerguntaTipo) => {
    const atual = secoes[sIndex].perguntas[pIndex];
    const comOpcoes = tipo === "escolha_unica" || tipo === "multipla_escolha";
    updatePergunta(sIndex, pIndex, {
      tipo,
      opcoes: comOpcoes ? (atual.opcoes.length ? atual.opcoes : ["Opção 1", "Opção 2"]) : [],
    });
  };

  const removePergunta = (sIndex: number, pIndex: number) =>
    updateSecao(sIndex, { perguntas: secoes[sIndex].perguntas.filter((_, i) => i !== pIndex) });

  const duplicarPergunta = (sIndex: number, pIndex: number) => {
    const { id: _id, ...resto } = secoes[sIndex].perguntas[pIndex];
    const perguntas = [...secoes[sIndex].perguntas];
    perguntas.splice(pIndex + 1, 0, { ...resto, opcoes: [...resto.opcoes] });
    updateSecao(sIndex, { perguntas });
  };

  const removeSecao = (sIndex: number) => {
    if (secoes[sIndex].perguntas.length && !window.confirm("Remover a seção e suas perguntas?")) return;
    onChange(secoes.filter((_, i) => i !== sIndex));
  };

  return (
    <div>
      {secoes.map((secao, sIndex) => (
        <div key={secao.id || `s-${sIndex}`} className="fb-section page-form" style={{ gap: 0 }}>
          <div className="fb-section-header">
            <input
              className="form-input"
              value={secao.titulo}
              placeholder={secoes.length > 1 ? `Título da seção ${sIndex + 1}` : "Título da seção (opcional)"}
              onChange={(e) => updateSecao(sIndex, { titulo: e.target.value })}
            />
            <button type="button" className="fb-icon-btn" title="Subir seção" disabled={sIndex === 0} onClick={() => onChange(mover(secoes, sIndex, -1))}>
              <ArrowUp size={16} />
            </button>
            <button
              type="button"
              className="fb-icon-btn"
              title="Descer seção"
              disabled={sIndex === secoes.length - 1}
              onClick={() => onChange(mover(secoes, sIndex, 1))}
            >
              <ArrowDown size={16} />
            </button>
            {secoes.length > 1 && (
              <button type="button" className="fb-icon-btn" title="Remover seção" onClick={() => removeSecao(sIndex)}>
                <Trash2 size={16} />
              </button>
            )}
          </div>
          <textarea
            className="form-input"
            rows={1}
            style={{ marginBottom: "0.75rem" }}
            value={secao.descricao}
            placeholder="Descrição da seção (opcional)"
            onChange={(e) => updateSecao(sIndex, { descricao: e.target.value })}
          />

          {secao.perguntas.length === 0 && (
            <p className="fb-muted" style={{ margin: "0 0 0.75rem" }}>
              Nenhuma pergunta nesta seção. Clique em “Pergunta” para adicionar.
            </p>
          )}
          {secao.perguntas.map((p, pIndex) => (
            <div key={p.id || `p-${sIndex}-${pIndex}`} className="fb-question">
              <div className="fb-question-row">
                <strong style={{ paddingTop: "0.75rem", minWidth: "1.5rem" }}>{pIndex + 1}.</strong>
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <input
                      className="form-input"
                      style={{ flex: 3, minWidth: 220 }}
                      value={p.texto}
                      placeholder="Pergunta"
                      onChange={(e) => updatePergunta(sIndex, pIndex, { texto: e.target.value })}
                    />
                    <select
                      className="form-select"
                      style={{ flex: 1, minWidth: 170 }}
                      value={p.tipo}
                      onChange={(e) => changeTipo(sIndex, pIndex, e.target.value as PerguntaTipo)}
                    >
                      {PERGUNTA_TIPOS.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <input
                    className="form-input"
                    value={p.ajuda}
                    placeholder="Texto de ajuda (opcional)"
                    onChange={(e) => updatePergunta(sIndex, pIndex, { ajuda: e.target.value })}
                  />

                  {(p.tipo === "escolha_unica" || p.tipo === "multipla_escolha") && (
                    <div>
                      {p.opcoes.map((opcao, oIndex) => (
                        <div key={oIndex} style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.35rem" }}>
                          <input type={p.tipo === "multipla_escolha" ? "checkbox" : "radio"} disabled />
                          <input
                            className="form-input"
                            value={opcao}
                            onChange={(e) =>
                              updatePergunta(sIndex, pIndex, {
                                opcoes: p.opcoes.map((o, i) => (i === oIndex ? e.target.value : o)),
                              })
                            }
                          />
                          <button
                            type="button"
                            className="fb-icon-btn"
                            title="Remover opção"
                            disabled={p.opcoes.length <= 2}
                            onClick={() => updatePergunta(sIndex, pIndex, { opcoes: p.opcoes.filter((_, i) => i !== oIndex) })}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        className="dashboard-btn-secondary"
                        onClick={() => updatePergunta(sIndex, pIndex, { opcoes: [...p.opcoes, `Opção ${p.opcoes.length + 1}`] })}
                      >
                        <Plus size={14} /> Opção
                      </button>
                    </div>
                  )}

                  {p.tipo === "escala" && (
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <span className="fb-muted">De</span>
                      <select
                        className="form-select"
                        style={{ width: 90 }}
                        value={p.escala_min}
                        onChange={(e) => updatePergunta(sIndex, pIndex, { escala_min: Number(e.target.value) })}
                      >
                        <option value={0}>0</option>
                        <option value={1}>1</option>
                      </select>
                      <span className="fb-muted">até</span>
                      <select
                        className="form-select"
                        style={{ width: 90 }}
                        value={p.escala_max}
                        onChange={(e) => updatePergunta(sIndex, pIndex, { escala_max: Number(e.target.value) })}
                      >
                        {[3, 4, 5, 7, 10].map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <label className="inline-check">
                    <input
                      type="checkbox"
                      checked={p.obrigatoria}
                      onChange={(e) => updatePergunta(sIndex, pIndex, { obrigatoria: e.target.checked })}
                    />
                    <span>Obrigatória</span>
                  </label>
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <button
                    type="button"
                    className="fb-icon-btn"
                    title="Subir"
                    disabled={pIndex === 0}
                    onClick={() => updateSecao(sIndex, { perguntas: mover(secao.perguntas, pIndex, -1) })}
                  >
                    <ArrowUp size={15} />
                  </button>
                  <button
                    type="button"
                    className="fb-icon-btn"
                    title="Descer"
                    disabled={pIndex === secao.perguntas.length - 1}
                    onClick={() => updateSecao(sIndex, { perguntas: mover(secao.perguntas, pIndex, 1) })}
                  >
                    <ArrowDown size={15} />
                  </button>
                  <button type="button" className="fb-icon-btn" title="Duplicar" onClick={() => duplicarPergunta(sIndex, pIndex)}>
                    <Copy size={15} />
                  </button>
                  <button type="button" className="fb-icon-btn" title="Remover" onClick={() => removePergunta(sIndex, pIndex)}>
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))}

          <button
            type="button"
            className="dashboard-btn-secondary"
            onClick={() => updateSecao(sIndex, { perguntas: [...secao.perguntas, novaPergunta()] })}
          >
            <Plus size={14} /> Pergunta
          </button>
        </div>
      ))}

      <button
        type="button"
        className="dashboard-btn-secondary"
        onClick={() => onChange([...secoes, { titulo: "", descricao: "", perguntas: [novaPergunta()] }])}
      >
        <Plus size={14} /> Nova seção
      </button>
    </div>
  );
}
