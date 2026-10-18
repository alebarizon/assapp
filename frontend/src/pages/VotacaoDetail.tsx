import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Lock, Play, Square, Trash2, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { acaoVotacao, deleteVotacao, getParticipacao, getVotacao, salvarVotacao } from "@/services/governanca";
import { BADGE_STATUS, dataHora, type Participacao, type Votacao } from "@/types/governanca";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";
import OpcoesEditor, { opcoesParaForm, opcoesParaPayload, type OpcaoForm } from "@/components/governanca/OpcoesEditor";

export default function VotacaoDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const editavel = podeEditar(user, "governanca");
  const [v, setV] = useState<Votacao | null>(null);
  const [part, setPart] = useState<Participacao | null>(null);
  const [opcoes, setOpcoes] = useState<OpcaoForm[]>([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const votacao = await getVotacao(id);
      setV(votacao);
      setOpcoes(opcoesParaForm(votacao.opcoes));
      if (votacao.status !== "rascunho") setPart(await getParticipacao(id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Votação não encontrada."));
    }
  }, [id]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const acao = async (nome: "abrir" | "encerrar" | "cancelar", confirmar: string) => {
    if (!window.confirm(confirmar)) return;
    setOcupado(true);
    setErro("");
    setAviso("");
    try {
      const r = await acaoVotacao(id, nome);
      if (nome === "abrir") setAviso(`Votação aberta para ${r.eleitores} eleitor(es). Eles votam pelo portal do associado.`);
      if (nome === "encerrar") setAviso("Votação encerrada. Resultado registrado na memória institucional.");
      await carregar();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível concluir a ação."));
    } finally {
      setOcupado(false);
    }
  };

  const salvarOpcoes = async () => {
    setOcupado(true);
    setErro("");
    try {
      const r = await salvarVotacao(id, { opcoes: opcoesParaPayload(opcoes) });
      setV(r);
      setOpcoes(opcoesParaForm(r.opcoes));
      setAviso("Opções salvas.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar opções."));
    } finally {
      setOcupado(false);
    }
  };

  if (!v) {
    return (
      <div className="dashboard-page">
        {erro ? <div className="alert-banner alert-banner-error">{erro}</div> : <div className="dashboard-loading"><div className="loading-spinner" /></div>}
      </div>
    );
  }

  const r = v.resultado;

  return (
    <div className="dashboard-page">
      <Link to="/app/governanca" className="dashboard-back-link" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Assembleias e votações
      </Link>
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title" style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            {v.titulo}
            <span className={`status-badge status-badge-${BADGE_STATUS[v.status]}`}>{v.status_display}</span>
          </h1>
          <p className="dashboard-subtitle">
            {v.tipo_display} · {v.censo_display} · até {v.max_escolhas} escolha(s)
            {v.permite_branco ? " · aceita branco" : ""}
            {v.fecha_em && ` · prazo ${dataHora(v.fecha_em)}`}
            {v.assembleia && (
              <>
                {" · "}
                <Link to={`/app/governanca/assembleias/${v.assembleia}`}>{v.assembleia_titulo}</Link>
              </>
            )}
          </p>
        </div>
        {editavel && (
          <div className="dashboard-header-actions">
            {v.status === "rascunho" && (
              <>
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={async () => {
                  if (!window.confirm("Excluir este rascunho?")) return;
                  await deleteVotacao(id);
                  navigate("/app/governanca");
                }}>
                  <Trash2 size={16} />
                </button>
                <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void acao("abrir", "Abrir a votação? O censo de eleitores será fixado agora e as opções não poderão mais mudar.")}>
                  <Play size={16} /> Abrir votação
                </button>
              </>
            )}
            {v.status === "aberta" && (
              <>
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void acao("cancelar", "Cancelar a votação? Ela será anulada e não terá resultado.")}>
                  <X size={16} /> Cancelar
                </button>
                <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void acao("encerrar", "Encerrar a votação e apurar o resultado?")}>
                  <Square size={16} /> Encerrar e apurar
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {aviso && <div className="highlight-banner">{aviso}</div>}
      {v.descricao && (
        <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem", whiteSpace: "pre-line" }}>
          {v.descricao}
        </div>
      )}

      {r && (
        <>
          <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0 0 0.75rem" }}>
            Resultado
          </h2>
          <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
            {r.opcoes.map((o) => (
              <div key={o.id} style={{ marginBottom: "0.75rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.92rem" }}>
                  <strong>
                    {o.titulo}
                    {r.vencedora === o.id && (
                      <span className="status-badge status-badge-ativa" style={{ marginLeft: 8 }}>
                        {v.tipo === "eleicao" ? "Eleita" : "Mais votada"}
                      </span>
                    )}
                  </strong>
                  <span>
                    {o.votos} voto(s) · {o.pct_validos}%
                  </span>
                </div>
                <div style={{ background: "#eef0ea", borderRadius: 6, height: 10, marginTop: 4 }}>
                  <div style={{ width: `${o.pct_validos}%`, background: "#1a5f4a", height: 10, borderRadius: 6 }} />
                </div>
              </div>
            ))}
            <p className="list-card-meta" style={{ marginBottom: 0 }}>
              Brancos: {r.brancos} · Participação: {r.votantes} de {r.eleitores} ({r.participacao_pct}%)
              {r.empate && " · Empate entre as mais votadas"}
            </p>
          </div>
        </>
      )}

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0 0 0.75rem" }}>
        {v.tipo === "eleicao" ? "Chapas / candidatos" : "Opções"}
      </h2>
      <div className="dashboard-content-panel page-form" style={{ marginBottom: "1.25rem" }}>
        {v.status === "rascunho" && editavel && v.tipo === "eleicao" ? (
          <>
            <OpcoesEditor opcoes={opcoes} onChange={setOpcoes} />
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void salvarOpcoes()}>
                Salvar opções
              </button>
            </div>
          </>
        ) : v.opcoes.length === 0 ? (
          <p className="list-card-meta" style={{ margin: 0 }}>
            Aprovo, Rejeito e Abstenção serão criadas ao abrir a votação.
          </p>
        ) : (
          <div className="list-stack">
            {v.opcoes.map((o) => (
              <div key={o.id} className="list-card" style={{ display: "block" }}>
                <p className="list-card-title">{o.titulo}</p>
                {o.integrantes && o.integrantes.length > 0 && (
                  <p className="list-card-meta">{o.integrantes.map((i) => (i.cargo ? `${i.nome} (${i.cargo})` : i.nome)).join(" · ")}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {part && (
        <>
          <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0 0 0.75rem", display: "flex", gap: 8, alignItems: "center" }}>
            <Lock size={16} /> Participação
          </h2>
          <div className="dashboard-content-panel">
            <p style={{ marginTop: 0 }}>
              <strong>{part.votantes}</strong> de <strong>{part.eleitores}</strong> eleitores já votaram ({part.participacao_pct}%).
              {v.status === "aberta" && " O resultado só aparece depois do encerramento."}
            </p>
            <div className="list-stack">
              {part.eleitores_lista.map((e) => (
                <div key={e.membro} className="list-card">
                  <span>{e.nome}</span>
                  <span className={`status-badge status-badge-${e.votou ? "ativa" : "rascunho"}`}>{e.votou ? "Votou" : "Não votou"}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
