import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Download, FileText, Megaphone, Play, Square, Trash2, UserPlus, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  acaoAssembleia,
  addPresenca,
  baixarAta,
  deleteAssembleia,
  getAssembleia,
  getPresencas,
  removePresenca,
  salvarAssembleia,
  type AcaoAssembleia,
  type ListaPresenca,
} from "@/services/governanca";
import { listMembros } from "@/services/membros";
import { BADGE_STATUS, dataHora, type Assembleia } from "@/types/governanca";
import type { Membro } from "@/types/membros";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";

export default function AssembleiaDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const editavel = podeEditar(user, "governanca");
  const [a, setA] = useState<Assembleia | null>(null);
  const [lista, setLista] = useState<ListaPresenca | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [busca, setBusca] = useState("");
  const [sugestoes, setSugestoes] = useState<Membro[]>([]);
  const [ata, setAta] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const [assembleia, presencas] = await Promise.all([getAssembleia(id), getPresencas(id)]);
      setA(assembleia);
      setAta(assembleia.ata);
      setLista(presencas);
    } catch (err) {
      setErro(apiErrorMessage(err, "Assembleia não encontrada."));
    }
  }, [id]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useEffect(() => {
    if (busca.trim().length < 2) {
      setSugestoes([]);
      return;
    }
    const t = setTimeout(() => {
      listMembros({ q: busca, ativo: true }).then((m) => setSugestoes(m.slice(0, 8))).catch(() => setSugestoes([]));
    }, 300);
    return () => clearTimeout(t);
  }, [busca]);

  const executar = async (acao: AcaoAssembleia, confirmar?: string) => {
    if (confirmar && !window.confirm(confirmar)) return;
    setOcupado(true);
    setErro("");
    setAviso("");
    try {
      const r = await acaoAssembleia(id, acao);
      setA(r);
      setAta(r.ata);
      if (acao === "convocar") setAviso(`Assembleia convocada. ${r.emails_enviados ?? 0} e-mail(s) de convocação enviados.`);
      if (acao === "publicar-ata") setAviso("Ata publicada e registrada na memória institucional do mandato.");
      setLista(await getPresencas(id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível concluir a ação."));
    } finally {
      setOcupado(false);
    }
  };

  const salvarAta = async () => {
    setOcupado(true);
    setErro("");
    try {
      setA(await salvarAssembleia(id, { ata }));
      setAviso("Ata salva.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar a ata."));
    } finally {
      setOcupado(false);
    }
  };

  const presenca = async (fn: () => Promise<ListaPresenca>) => {
    setErro("");
    try {
      setLista(await fn());
      setBusca("");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro na lista de presença."));
    }
  };

  if (!a) {
    return (
      <div className="dashboard-page">
        {erro ? <div className="alert-banner alert-banner-error">{erro}</div> : <div className="dashboard-loading"><div className="loading-spinner" /></div>}
      </div>
    );
  }

  const listaAberta = editavel && (a.status === "convocada" || a.status === "em_andamento");
  const q = lista?.quorum;
  const presentes = new Set(lista?.presencas.map((p) => p.membro));

  return (
    <div className="dashboard-page">
      <Link to="/app/governanca" className="dashboard-back-link" style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: "0.75rem" }}>
        <ArrowLeft size={16} /> Assembleias e votações
      </Link>
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title" style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
            {a.titulo}
            <span className={`status-badge status-badge-${BADGE_STATUS[a.status]}`}>{a.status_display}</span>
          </h1>
          <p className="dashboard-subtitle">
            {a.tipo_display} · {dataHora(a.data_hora)} · {a.modalidade_display}
            {a.local && ` · ${a.local}`}
          </p>
        </div>
        {editavel && (
          <div className="dashboard-header-actions">
            {a.status === "rascunho" && (
              <>
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={async () => {
                  if (!window.confirm("Excluir este rascunho?")) return;
                  await deleteAssembleia(id);
                  navigate("/app/governanca");
                }}>
                  <Trash2 size={16} />
                </button>
                <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void executar("convocar", "Convocar a assembleia e enviar o edital por e-mail a todos os associados ativos?")}>
                  <Megaphone size={16} /> Convocar
                </button>
              </>
            )}
            {a.status === "convocada" && (
              <>
                <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void executar("cancelar", "Cancelar a assembleia?")}>
                  <X size={16} /> Cancelar
                </button>
                <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void executar("iniciar")}>
                  <Play size={16} /> Iniciar assembleia
                </button>
              </>
            )}
            {a.status === "em_andamento" && (
              <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={() => void executar("encerrar", "Encerrar a assembleia? A lista de presença será fechada.")}>
                <Square size={16} /> Encerrar
              </button>
            )}
          </div>
        )}
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {aviso && <div className="highlight-banner">{aviso}</div>}

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        {a.link_online && (
          <p style={{ marginTop: 0 }}>
            <strong>Link online:</strong>{" "}
            <a href={a.link_online} target="_blank" rel="noreferrer">
              {a.link_online}
            </a>
          </p>
        )}
        {a.pauta.length > 0 && (
          <>
            <strong>Ordem do dia</strong>
            <ol style={{ margin: "0.4rem 0 0.9rem" }}>
              {a.pauta.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ol>
          </>
        )}
        {a.convocacao && <p style={{ whiteSpace: "pre-line" }}>{a.convocacao}</p>}
        <p className="list-card-meta" style={{ marginBottom: 0 }}>
          {a.convocada_em ? `Convocada em ${dataHora(a.convocada_em)}` : "Ainda não convocada"}
          {a.votacoes.length > 0 && " · Votações: "}
          {a.votacoes.map((v, i) => (
            <span key={v.id}>
              {i > 0 && ", "}
              <Link to={`/app/governanca/votacoes/${v.id}`}>{v.titulo}</Link> ({v.status_display.toLowerCase()})
            </span>
          ))}
        </p>
      </div>

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0 0 0.75rem" }}>
        Presença e quórum
      </h2>
      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        {q && (
          <p style={{ marginTop: 0 }}>
            <strong>{q.presentes}</strong> presente(s) · <strong>{q.presentes_aptos}</strong> de <strong>{q.aptos}</strong> aptos a votar
            (em dia) — {q.pct}%
            {q.minimo !== null && (
              <span className={`status-badge status-badge-${q.atingido ? "ativa" : "pendente"}`} style={{ marginLeft: 8 }}>
                Quórum de {q.minimo}% {q.atingido ? "atingido" : "não atingido"}
              </span>
            )}
          </p>
        )}
        {listaAberta && (
          <div className="page-form" style={{ position: "relative", marginBottom: "0.9rem" }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <UserPlus size={16} />
              <input className="form-input" placeholder="Registrar presença: buscar associado por nome ou e-mail" value={busca} onChange={(e) => setBusca(e.target.value)} />
            </div>
            {sugestoes.length > 0 && (
              <div className="list-stack" style={{ marginTop: 6 }}>
                {sugestoes.map((m) => (
                  <div key={m.id} className="list-card">
                    <span>
                      {m.nome_completo} <span className="list-card-meta">{m.email}</span>
                    </span>
                    {presentes.has(m.id) ? (
                      <span className="list-card-meta">já presente</span>
                    ) : (
                      <div style={{ display: "flex", gap: 6 }}>
                        <button type="button" className="dashboard-btn-secondary" onClick={() => void presenca(() => addPresenca(id, m.id, "presencial"))}>
                          Presencial
                        </button>
                        {a.modalidade !== "presencial" && (
                          <button type="button" className="dashboard-btn-secondary" onClick={() => void presenca(() => addPresenca(id, m.id, "online"))}>
                            Online
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {lista && lista.presencas.length > 0 ? (
          <div className="list-stack">
            {lista.presencas.map((p) => (
              <div key={p.id} className="list-card">
                <span>
                  {p.membro_nome} <span className="list-card-meta">· {p.forma_display} · {dataHora(p.registrada_em)}</span>
                </span>
                {listaAberta && (
                  <button type="button" className="dashboard-btn-danger" style={{ padding: "0.4rem 0.6rem" }} title="Remover" onClick={() => void presenca(() => removePresenca(id, p.membro))}>
                    <X size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="dashboard-empty">Nenhuma presença registrada.</div>
        )}
        {a.modalidade !== "presencial" && a.status === "em_andamento" && (
          <p className="list-card-meta" style={{ marginBottom: 0 }}>Associados também podem confirmar presença online pelo portal.</p>
        )}
      </div>

      {(a.status === "encerrada" || a.ata) && (
        <>
          <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0 0 0.75rem", display: "flex", gap: 8, alignItems: "center" }}>
            <FileText size={18} /> Ata
          </h2>
          <div className="dashboard-content-panel page-form">
            {a.ata_publicada_em ? (
              <>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>{a.ata}</pre>
                <p className="list-card-meta">
                  Publicada em {dataHora(a.ata_publicada_em)} · SHA-256 <code>{a.ata_hash}</code>
                </p>
              </>
            ) : (
              <textarea className="form-input" rows={16} value={ata} disabled={!editavel} onChange={(e) => setAta(e.target.value)} placeholder="Gere o rascunho a partir da presença, pauta e votações, e ajuste o texto." />
            )}
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: "0.75rem", flexWrap: "wrap" }}>
              {editavel && !a.ata_publicada_em && (
                <>
                  <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={() => void executar("gerar-ata", ata ? "Substituir o texto atual pelo rascunho gerado?" : undefined)}>
                    Gerar rascunho
                  </button>
                  <button type="button" className="dashboard-btn-secondary" disabled={ocupado || ata === a.ata} onClick={() => void salvarAta()}>
                    Salvar
                  </button>
                  {a.status === "encerrada" && (
                    <button type="button" className="dashboard-btn-new" disabled={ocupado || !a.ata || ata !== a.ata} onClick={() => void executar("publicar-ata", "Publicar a ata? Depois de publicada ela não pode ser alterada.")}>
                      Publicar ata
                    </button>
                  )}
                </>
              )}
              {a.ata && (
                <button type="button" className="dashboard-btn-secondary" onClick={() => void baixarAta(id)}>
                  <Download size={14} /> PDF
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
