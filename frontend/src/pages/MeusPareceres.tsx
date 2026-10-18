import { useCallback, useEffect, useState } from "react";
import { Download } from "lucide-react";
import { concluirMeuParecer, downloadArquivoParecer, listMeusPareceres } from "@/services/eventos";
import type { MeuParecer, Recomendacao } from "@/types/eventos";
import { RECOMENDACOES } from "@/types/eventos";
import { apiErrorMessage } from "@/utils/apiError";

const NOTAS = [1, 2, 3, 4, 5];

function prazoTexto(p: MeuParecer): string {
  if (!p.prazo) return "";
  const data = new Date(`${p.prazo}T23:59`);
  const atrasado = !p.concluido && data < new Date();
  return ` · prazo ${data.toLocaleDateString("pt-BR")}${atrasado ? " (atrasado)" : ""}`;
}

export default function MeusPareceres() {
  const [pareceres, setPareceres] = useState<MeuParecer[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [aberto, setAberto] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    try {
      setPareceres(await listMeusPareceres());
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar pareceres."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const pendentes = pareceres.filter((p) => !p.concluido).length;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Meus pareceres</h1>
        <p className="dashboard-subtitle">
          {pendentes > 0 ? `${pendentes} trabalho(s) aguardando seu parecer` : "Trabalhos atribuídos a você para avaliação"}
        </p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : pareceres.length === 0 ? (
        <div className="dashboard-empty">Nenhum trabalho atribuído a você.</div>
      ) : (
        <div className="list-stack">
          {pareceres.map((p) => (
            <div key={p.id} className="list-card" style={{ alignItems: "flex-start", flexDirection: "column" }}>
              <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: "1rem" }}>
                <div>
                  <p className="list-card-title">{p.submissao.titulo}</p>
                  <p className="list-card-meta">
                    {p.submissao.evento_titulo}
                    {p.submissao.area_tematica && ` · ${p.submissao.area_tematica}`}
                    {prazoTexto(p)}
                  </p>
                  <p className="list-card-meta">
                    {p.submissao.autoria ? `Autoria: ${p.submissao.autoria}` : "Avaliação duplo-cega — autoria oculta"}
                  </p>
                </div>
                <span className={`status-badge status-badge-${p.concluido ? "aceito" : "pendente"}`}>
                  {p.concluido ? `Concluído${p.nota_ponderada ? ` · nota ${p.nota_ponderada}` : ""}` : "Pendente"}
                </span>
              </div>

              {aberto === p.id ? (
                <FormularioParecer
                  parecer={p}
                  onFechar={() => setAberto(null)}
                  onSalvo={(atualizado) => {
                    setPareceres((lista) => lista.map((x) => (x.id === atualizado.id ? atualizado : x)));
                    setAberto(null);
                  }}
                />
              ) : (
                <div className="filters-row" style={{ marginBottom: 0, marginTop: "0.5rem" }}>
                  <button type="button" className="dashboard-btn-edit" onClick={() => setAberto(p.id)}>
                    {p.concluido ? (p.editavel ? "Ver / revisar parecer" : "Ver parecer") : "Avaliar"}
                  </button>
                  {p.submissao.tem_arquivo && (
                    <button
                      type="button"
                      className="dashboard-btn-secondary"
                      onClick={() => void downloadArquivoParecer(p.id)}
                    >
                      <Download size={14} /> Baixar trabalho
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface FormProps {
  parecer: MeuParecer;
  onFechar: () => void;
  onSalvo: (p: MeuParecer) => void;
}

function FormularioParecer({ parecer: p, onFechar, onSalvo }: FormProps) {
  const [notas, setNotas] = useState<Record<string, number>>(p.notas ?? {});
  const [recomendacao, setRecomendacao] = useState<Recomendacao | "">(p.recomendacao);
  const [comentariosAutor, setComentariosAutor] = useState(p.comentarios_autor);
  const [comentariosInternos, setComentariosInternos] = useState(p.comentarios_internos);
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);

  const pesoTotal = p.criterios.reduce((t, c) => t + c.peso, 0);
  const completas = p.criterios.every((c) => notas[c.nome]);
  const previa = completas
    ? (p.criterios.reduce((t, c) => t + notas[c.nome] * c.peso, 0) / pesoTotal).toFixed(2)
    : null;

  const enviar = async () => {
    if (!recomendacao || !completas) {
      setErro("Dê nota a todos os critérios e escolha uma recomendação.");
      return;
    }
    setErro("");
    setSalvando(true);
    try {
      onSalvo(
        await concluirMeuParecer(p.id, {
          recomendacao,
          notas,
          comentarios_autor: comentariosAutor,
          comentarios_internos: comentariosInternos,
        })
      );
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível enviar o parecer."));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div style={{ width: "100%", marginTop: "0.75rem" }}>
      <p className="list-card-meta" style={{ whiteSpace: "pre-wrap" }}>{p.submissao.resumo}</p>
      {p.submissao.palavras_chave.length > 0 && (
        <p className="list-card-meta">Palavras-chave: {p.submissao.palavras_chave.join(", ")}</p>
      )}

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      <fieldset disabled={!p.editavel} style={{ border: "none", padding: 0, margin: "0.75rem 0 0" }}>
        <div className="form-group">
          <label className="form-label">Notas por critério (1 = insuficiente · 5 = excelente)</label>
          {p.criterios.map((c) => (
            <div
              key={c.nome}
              style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem", flexWrap: "wrap" }}
            >
              <span style={{ flex: "1 1 14rem" }}>
                {c.nome} <span className="list-card-meta">(peso {c.peso})</span>
              </span>
              <div style={{ display: "flex", gap: "0.25rem" }} role="radiogroup" aria-label={c.nome}>
                {NOTAS.map((n) => (
                  <button
                    key={n}
                    type="button"
                    role="radio"
                    aria-checked={notas[c.nome] === n}
                    className={notas[c.nome] === n ? "dashboard-btn-save" : "dashboard-btn-secondary"}
                    style={{ minWidth: "2.25rem", justifyContent: "center" }}
                    onClick={() => setNotas({ ...notas, [c.nome]: n })}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <p className="list-card-meta">Nota ponderada: {previa ?? "—"}</p>
        </div>

        <div className="form-group">
          <label className="form-label">Recomendação</label>
          <select
            className="form-select"
            value={recomendacao}
            onChange={(e) => setRecomendacao(e.target.value as Recomendacao)}
          >
            <option value="">Selecione</option>
            {RECOMENDACOES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Comentários aos autores (enviados sem identificar você)</label>
          <textarea
            className="form-input"
            rows={4}
            value={comentariosAutor}
            onChange={(e) => setComentariosAutor(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Comentários só para a comissão</label>
          <textarea
            className="form-input"
            rows={2}
            value={comentariosInternos}
            onChange={(e) => setComentariosInternos(e.target.value)}
          />
        </div>
      </fieldset>

      {!p.editavel && <p className="list-card-meta">A comissão já decidiu este trabalho; o parecer não pode mais ser alterado.</p>}

      <div className="form-actions">
        <button type="button" className="dashboard-btn-cancel" onClick={onFechar}>
          Fechar
        </button>
        {p.editavel && (
          <button type="button" className="dashboard-btn-save" onClick={() => void enviar()} disabled={salvando}>
            {salvando ? "Enviando..." : p.concluido ? "Atualizar parecer" : "Enviar parecer"}
          </button>
        )}
      </div>
    </div>
  );
}
