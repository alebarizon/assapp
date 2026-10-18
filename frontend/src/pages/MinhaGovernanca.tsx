import { useCallback, useEffect, useState } from "react";
import { CheckCircle, Download, Gavel, Vote } from "lucide-react";
import { baixarMinhaAta, getMinhaGovernanca, marcarPresenca, votar } from "@/services/governanca";
import { BADGE_STATUS, dataHora, type MinhaAssembleia, type MinhaVotacao } from "@/types/governanca";
import { apiErrorMessage } from "@/utils/apiError";

function Cedula({ v, onVotou }: { v: MinhaVotacao; onVotou: (comprovante: string) => void }) {
  const [escolhas, setEscolhas] = useState<number[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");
  const multipla = v.max_escolhas > 1;

  const alternar = (id: number) => {
    if (!multipla) return setEscolhas([id]);
    setEscolhas((atual) =>
      atual.includes(id) ? atual.filter((x) => x !== id) : atual.length < v.max_escolhas ? [...atual, id] : atual,
    );
  };

  const confirmar = async () => {
    const resumo = escolhas.length
      ? v.opcoes.filter((o) => escolhas.includes(o.id!)).map((o) => o.titulo).join(", ")
      : "voto em branco";
    if (!window.confirm(`Confirmar seu voto: ${resumo}? O voto não pode ser alterado.`)) return;
    setEnviando(true);
    setErro("");
    try {
      const r = await votar(v.id, escolhas);
      onVotou(r.comprovante);
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível registrar o voto."));
      setEnviando(false);
    }
  };

  return (
    <div className="page-form">
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      <p className="list-card-meta" style={{ marginTop: 0 }}>
        {multipla ? `Escolha até ${v.max_escolhas} opções.` : "Escolha uma opção."} Voto secreto.
      </p>
      <div className="list-stack">
        {v.opcoes.map((o) => (
          <label key={o.id} className="list-card" style={{ cursor: "pointer", justifyContent: "flex-start", gap: "0.75rem" }}>
            <input
              type={multipla ? "checkbox" : "radio"}
              name={`voto-${v.id}`}
              checked={escolhas.includes(o.id!)}
              onChange={() => alternar(o.id!)}
            />
            <span>
              <strong>{o.titulo}</strong>
              {o.integrantes && o.integrantes.length > 0 && (
                <span className="list-card-meta" style={{ display: "block" }}>
                  {o.integrantes.map((i) => (i.cargo ? `${i.nome} (${i.cargo})` : i.nome)).join(" · ")}
                </span>
              )}
            </span>
          </label>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: "0.75rem" }}>
        {v.permite_branco && escolhas.length > 0 && (
          <button type="button" className="dashboard-btn-secondary" onClick={() => setEscolhas([])}>
            Limpar (votar em branco)
          </button>
        )}
        <button
          type="button"
          className="dashboard-btn-new"
          disabled={enviando || (!v.permite_branco && escolhas.length === 0)}
          onClick={() => void confirmar()}
        >
          {escolhas.length === 0 && v.permite_branco ? "Votar em branco" : "Confirmar voto"}
        </button>
      </div>
    </div>
  );
}

export default function MinhaGovernanca() {
  const [assembleias, setAssembleias] = useState<MinhaAssembleia[]>([]);
  const [votacoes, setVotacoes] = useState<MinhaVotacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [comprovantes, setComprovantes] = useState<Record<string, string>>({});

  const carregar = useCallback(async () => {
    try {
      const r = await getMinhaGovernanca();
      setAssembleias(r.assembleias);
      setVotacoes(r.votacoes);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const presenca = async (id: string) => {
    setErro("");
    try {
      await marcarPresenca(id);
      await carregar();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível registrar a presença."));
    }
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Assembleias e votações</h1>
        <p className="dashboard-subtitle">Convocações, presença, eleições e atas da associação</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0.5rem 0 0.75rem" }}>
        Votações
      </h2>
      {votacoes.length === 0 ? (
        <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
          <div className="dashboard-empty">Nenhuma votação para você no momento.</div>
        </div>
      ) : (
        votacoes.map((v) => (
          <div key={v.id} className="dashboard-content-panel" style={{ marginBottom: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap", marginBottom: "0.5rem" }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Vote size={18} />
                <strong>{v.titulo}</strong>
              </div>
              <span className={`status-badge status-badge-${BADGE_STATUS[v.status]}`}>{v.status_display}</span>
            </div>
            {v.descricao && <p style={{ whiteSpace: "pre-line", marginTop: 0 }}>{v.descricao}</p>}
            {v.fecha_em && v.status === "aberta" && <p className="list-card-meta">Vote até {dataHora(v.fecha_em)}.</p>}

            {comprovantes[v.id] ? (
              <div className="highlight-banner" style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <CheckCircle size={16} /> Voto registrado. Comprovante: <code>{comprovantes[v.id]}</code> — guarde este código.
              </div>
            ) : v.pode_votar ? (
              <Cedula v={v} onVotou={(c) => {
                setComprovantes((atual) => ({ ...atual, [v.id]: c }));
                void carregar();
              }} />
            ) : v.status === "encerrada" && v.resultado ? (
              <div>
                {v.resultado.opcoes.map((o) => (
                  <p key={o.id} style={{ margin: "0.25rem 0" }}>
                    {o.titulo}: <strong>{o.votos}</strong> voto(s) ({o.pct_validos}%)
                    {v.resultado?.vencedora === o.id && (
                      <span className="status-badge status-badge-ativa" style={{ marginLeft: 8 }}>
                        {v.tipo === "eleicao" ? "Eleita" : "Mais votada"}
                      </span>
                    )}
                  </p>
                ))}
                <p className="list-card-meta">
                  {v.ja_votou ? "Você votou. " : "Você não votou. "}
                  Participação: {v.resultado.participacao_pct}%.
                </p>
              </div>
            ) : (
              <p className="list-card-meta">{v.ja_votou ? "Seu voto já foi registrado. O resultado sai no encerramento." : "Votação fora do prazo."}</p>
            )}
          </div>
        ))
      )}

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "1.5rem 0 0.75rem" }}>
        Assembleias
      </h2>
      <div className="dashboard-content-panel">
        {assembleias.length === 0 ? (
          <div className="dashboard-empty">Nenhuma assembleia convocada.</div>
        ) : (
          <div className="list-stack">
            {assembleias.map((a) => (
              <div key={a.id} className="list-card" style={{ display: "block" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <Gavel size={18} style={{ marginTop: 2 }} />
                    <div>
                      <p className="list-card-title">{a.titulo}</p>
                      <p className="list-card-meta">
                        {a.tipo_display} · {dataHora(a.data_hora)} · {a.modalidade_display}
                        {a.local && ` · ${a.local}`}
                        {a.presente && " · você esteve presente"}
                      </p>
                    </div>
                  </div>
                  <span className={`status-badge status-badge-${BADGE_STATUS[a.status]}`}>{a.status_display}</span>
                </div>
                {a.pauta.length > 0 && a.status !== "encerrada" && (
                  <ol style={{ margin: "0.5rem 0 0", fontSize: "0.9rem" }}>
                    {a.pauta.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ol>
                )}
                <div style={{ display: "flex", gap: 8, marginTop: "0.6rem", flexWrap: "wrap" }}>
                  {a.link_online && ["convocada", "em_andamento"].includes(a.status) && (
                    <a className="dashboard-btn-secondary" href={a.link_online} target="_blank" rel="noreferrer">
                      Entrar na reunião
                    </a>
                  )}
                  {a.pode_marcar_presenca && (
                    <button type="button" className="dashboard-btn-new" onClick={() => void presenca(a.id)}>
                      Confirmar presença
                    </button>
                  )}
                  {a.ata_publicada_em && (
                    <button type="button" className="dashboard-btn-secondary" onClick={() => void baixarMinhaAta(a.id)}>
                      <Download size={14} /> Ata (PDF)
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
