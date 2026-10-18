import { useEffect, useState } from "react";
import { Award, Download, Trash2, UserCheck } from "lucide-react";
import {
  atribuirParecerista,
  decidirSubmissao,
  downloadArquivoSubmissao,
  emitirCertificadosCientificos,
  listCandidatosParecer,
  removerParecer,
} from "@/services/eventos";
import type {
  CandidatoParecer,
  EventoAcademico,
  Recomendacao,
  SubmissaoTrabalho,
} from "@/types/eventos";
import { RECOMENDACOES } from "@/types/eventos";
import { apiErrorMessage } from "@/utils/apiError";

const DECIDIDOS = new Set(["aceito", "aceito_com_revisoes", "rejeitado"]);

interface Props {
  evento: EventoAcademico;
  submissoes: SubmissaoTrabalho[];
  podeEditar: boolean;
  onAtualizar: () => void;
  onMensagem: (msg: string) => void;
}

export default function SubmissoesComissao({ evento, submissoes, podeEditar, onAtualizar, onMensagem }: Props) {
  const [candidatos, setCandidatos] = useState<CandidatoParecer[]>([]);
  const [filtro, setFiltro] = useState("");
  const [erro, setErro] = useState("");
  const [emitindo, setEmitindo] = useState(false);

  useEffect(() => {
    if (podeEditar) listCandidatosParecer().then(setCandidatos).catch(() => setCandidatos([]));
  }, [podeEditar]);

  const executar = async (acao: () => Promise<unknown>, sucesso: string) => {
    setErro("");
    try {
      await acao();
      onMensagem(sucesso);
      onAtualizar();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível concluir a ação."));
    }
  };

  const emitir = async () => {
    if (!confirm("Emitir certificados para autores de trabalhos aceitos e pareceristas, enviando por e-mail?")) return;
    setEmitindo(true);
    setErro("");
    try {
      const r = await emitirCertificadosCientificos(evento.id, true);
      onMensagem(
        `Certificados emitidos: ${r.autores} de autoria e ${r.pareceristas} de parecerista (${r.emails_enviados} e-mail(s)).`
      );
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível emitir os certificados."));
    } finally {
      setEmitindo(false);
    }
  };

  const notaCorte = evento.call_for_papers?.nota_corte ? Number(evento.call_for_papers.nota_corte) : null;
  const visiveis = filtro ? submissoes.filter((s) => s.status === filtro) : submissoes;
  const temAceitos = submissoes.some((s) => s.status === "aceito" || s.status === "aceito_com_revisoes");

  return (
    <div className="dashboard-content-panel">
      <div className="filters-row" style={{ justifyContent: "space-between" }}>
        <select className="form-select" style={{ width: "auto" }} value={filtro} onChange={(e) => setFiltro(e.target.value)}>
          <option value="">Todas as situações</option>
          <option value="submetido">Aguardando parecerista</option>
          <option value="em_parecer">Em parecer</option>
          <option value="aceito">Aceitos</option>
          <option value="aceito_com_revisoes">Aceitos com revisões</option>
          <option value="rejeitado">Rejeitados</option>
        </select>
        {podeEditar && temAceitos && (
          <button type="button" className="dashboard-btn-save" onClick={emitir} disabled={emitindo}>
            <Award size={14} /> {emitindo ? "Emitindo..." : "Emitir certificados de autores e pareceristas"}
          </button>
        )}
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {visiveis.length === 0 ? (
        <div className="dashboard-empty">Nenhuma submissão.</div>
      ) : (
        <div className="list-stack">
          {visiveis.map((s) => (
            <CartaoSubmissao
              key={s.id}
              submissao={s}
              candidatos={candidatos}
              notaCorte={notaCorte}
              podeEditar={podeEditar}
              executar={executar}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CartaoProps {
  submissao: SubmissaoTrabalho;
  candidatos: CandidatoParecer[];
  notaCorte: number | null;
  podeEditar: boolean;
  executar: (acao: () => Promise<unknown>, sucesso: string) => Promise<void>;
}

function CartaoSubmissao({ submissao: s, candidatos, notaCorte, podeEditar, executar }: CartaoProps) {
  const [parecerista, setParecerista] = useState("");
  const [prazo, setPrazo] = useState("");
  const [decisao, setDecisao] = useState<Recomendacao>("aceitar");
  const [comentario, setComentario] = useState("");
  const [decidindo, setDecidindo] = useState(false);

  const decidido = DECIDIDOS.has(s.status);
  const jaAtribuidos = new Set(s.pareceres?.map((p) => p.parecerista));
  const disponiveis = candidatos.filter((c) => !jaAtribuidos.has(c.id) && c.email !== s.autor_email);
  const media = s.nota_media ? Number(s.nota_media) : null;

  return (
    <div className="list-card" style={{ alignItems: "flex-start", flexDirection: "column", gap: "0.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: "1rem" }}>
        <div>
          <p className="list-card-title">{s.titulo}</p>
          <p className="list-card-meta">
            {s.autoria || s.autor_email} · {s.area_tematica || "sem área"}
            {s.palavras_chave.length > 0 && ` · ${s.palavras_chave.join(", ")}`}
          </p>
          <p className="list-card-meta" style={{ whiteSpace: "pre-wrap" }}>{s.resumo}</p>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <span className={`status-badge status-badge-${s.status}`}>{s.status_display}</span>
          {media !== null && (
            <p className="list-card-meta" style={{ marginTop: "0.35rem" }}>
              Média <strong>{s.nota_media}</strong>
              {notaCorte !== null && (media >= notaCorte ? " · acima do corte" : " · abaixo do corte")}
            </p>
          )}
        </div>
      </div>

      {s.tem_arquivo && (
        <button type="button" className="dashboard-btn-secondary" onClick={() => void downloadArquivoSubmissao(s.id)}>
          <Download size={14} /> Baixar trabalho
        </button>
      )}

      {s.pareceres && s.pareceres.length > 0 && (
        <div style={{ width: "100%" }}>
          {s.pareceres.map((p) => (
            <div key={p.id} className="list-card-meta" style={{ margin: "0.25rem 0" }}>
              <strong>{p.parecerista_nome}</strong>
              {p.concluido ? (
                <>
                  {" "}— {p.recomendacao_display}
                  {p.nota_ponderada && ` · nota ${p.nota_ponderada}`}
                  {p.notas && Object.keys(p.notas).length > 0 && (
                    <span> ({Object.entries(p.notas).map(([k, v]) => `${k}: ${v}`).join("; ")})</span>
                  )}
                  {p.comentarios_autor && <div>Ao autor: {p.comentarios_autor}</div>}
                  {p.comentarios_internos && <div>Só para a comissão: {p.comentarios_internos}</div>}
                </>
              ) : (
                <>
                  {" "}— aguardando parecer{p.prazo && ` (prazo ${new Date(`${p.prazo}T12:00`).toLocaleDateString("pt-BR")})`}
                  {podeEditar && !decidido && (
                    <button
                      type="button"
                      className="dashboard-btn-cancel"
                      style={{ marginLeft: "0.5rem", padding: "0.1rem 0.4rem" }}
                      aria-label="Remover parecerista"
                      onClick={() => void executar(() => removerParecer(p.id), "Parecerista removido.")}
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {podeEditar && !decidido && (
        <div className="filters-row" style={{ marginBottom: 0, width: "100%" }}>
          <select
            className="form-select"
            style={{ flex: 1, minWidth: "12rem" }}
            value={parecerista}
            onChange={(e) => setParecerista(e.target.value)}
          >
            <option value="">Escolher parecerista…</option>
            {disponiveis.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome} · {c.papel}{c.pendentes ? ` · ${c.pendentes} pendente(s)` : ""}
              </option>
            ))}
          </select>
          <input
            className="form-input"
            style={{ width: "auto" }}
            type="date"
            aria-label="Prazo do parecer"
            value={prazo}
            onChange={(e) => setPrazo(e.target.value)}
          />
          <button
            type="button"
            className="dashboard-btn-secondary"
            disabled={!parecerista}
            onClick={() =>
              void executar(async () => {
                await atribuirParecerista(s.id, parecerista, prazo);
                setParecerista("");
              }, "Parecerista atribuído e avisado por e-mail.")
            }
          >
            <UserCheck size={14} /> Atribuir
          </button>
          <button type="button" className="dashboard-btn-edit" onClick={() => setDecidindo(!decidindo)}>
            Decidir
          </button>
        </div>
      )}

      {decidindo && !decidido && (
        <div style={{ width: "100%" }}>
          <div className="form-group">
            <label className="form-label">Decisão da comissão</label>
            <select className="form-select" value={decisao} onChange={(e) => setDecisao(e.target.value as Recomendacao)}>
              {RECOMENDACOES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Mensagem da comissão (vai na carta ao autor)</label>
            <textarea
              className="form-input"
              rows={3}
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
            />
          </div>
          <p className="list-card-meta">
            A carta inclui os comentários dos pareceres destinados ao autor, sem identificar os pareceristas.
          </p>
          <div className="form-actions">
            <button type="button" className="dashboard-btn-cancel" onClick={() => setDecidindo(false)}>
              Cancelar
            </button>
            <button
              type="button"
              className="dashboard-btn-save"
              onClick={() =>
                void executar(
                  () => decidirSubmissao(s.id, { decisao, comentario, notificar: true }),
                  "Decisão registrada e carta enviada ao autor."
                )
              }
            >
              Registrar decisão e enviar carta
            </button>
          </div>
        </div>
      )}

      {decidido && s.decidido_em && (
        <p className="list-card-meta">
          Decidido em {new Date(s.decidido_em).toLocaleDateString("pt-BR")}
          {s.decisao_comentario && ` — ${s.decisao_comentario}`}
        </p>
      )}
    </div>
  );
}
