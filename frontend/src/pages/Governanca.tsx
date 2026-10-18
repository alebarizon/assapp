import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Gavel, Plus, Vote } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { listAssembleias, listVotacoes, salvarAssembleia, salvarVotacao } from "@/services/governanca";
import {
  BADGE_STATUS,
  dataHora,
  type Assembleia,
  type CensoVotacao,
  type Modalidade,
  type TipoAssembleia,
  type TipoVotacao,
  type Votacao,
} from "@/types/governanca";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";
import OpcoesEditor, { type OpcaoForm, opcoesParaPayload } from "@/components/governanca/OpcoesEditor";

const ASSEMBLEIA_VAZIA = {
  titulo: "",
  tipo: "ordinaria" as TipoAssembleia,
  data_hora: "",
  modalidade: "presencial" as Modalidade,
  local: "",
  link_online: "",
  convocacao: "",
  pauta: "",
  quorum_minimo: "",
};

const VOTACAO_VAZIA = {
  titulo: "",
  descricao: "",
  tipo: "eleicao" as TipoVotacao,
  censo: "adimplentes" as CensoVotacao,
  assembleia: "",
  max_escolhas: "1",
  permite_branco: true,
  fecha_em: "",
};

export default function Governanca() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const editavel = podeEditar(user, "governanca");
  const [assembleias, setAssembleias] = useState<Assembleia[]>([]);
  const [votacoes, setVotacoes] = useState<Votacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [modal, setModal] = useState<"assembleia" | "votacao" | null>(null);
  const [formA, setFormA] = useState(ASSEMBLEIA_VAZIA);
  const [formV, setFormV] = useState(VOTACAO_VAZIA);
  const [opcoes, setOpcoes] = useState<OpcaoForm[]>([{ titulo: "", integrantes: "" }, { titulo: "", integrantes: "" }]);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    Promise.all([listAssembleias(), listVotacoes()])
      .then(([a, v]) => {
        setAssembleias(a);
        setVotacoes(v);
      })
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar.")))
      .finally(() => setLoading(false));
  }, []);

  const criarAssembleia = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      const a = await salvarAssembleia(null, {
        ...formA,
        data_hora: new Date(formA.data_hora).toISOString(),
        pauta: formA.pauta.split("\n").map((p) => p.trim()).filter(Boolean),
        quorum_minimo: formA.quorum_minimo ? Number(formA.quorum_minimo) : null,
      });
      navigate(`/app/governanca/assembleias/${a.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar assembleia."));
      setSalvando(false);
    }
  };

  const criarVotacao = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      const v = await salvarVotacao(null, {
        ...formV,
        assembleia: formV.assembleia || null,
        max_escolhas: Number(formV.max_escolhas) || 1,
        fecha_em: formV.fecha_em ? new Date(formV.fecha_em).toISOString() : null,
        opcoes: formV.tipo === "eleicao" ? opcoesParaPayload(opcoes) : [],
      });
      navigate(`/app/governanca/votacoes/${v.id}`);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar votação."));
      setSalvando(false);
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

  const assembleiasAbertas = assembleias.filter((a) => !["encerrada", "cancelada"].includes(a.status));

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Assembleias e votações</h1>
          <p className="dashboard-subtitle">Convocação, presença, quórum, eleições, deliberações e atas</p>
        </div>
        {editavel && (
          <div className="dashboard-header-actions">
            <button type="button" className="dashboard-btn-secondary" onClick={() => setModal("votacao")}>
              <Vote size={16} /> Nova votação
            </button>
            <button type="button" className="dashboard-btn-new" onClick={() => setModal("assembleia")}>
              <Plus size={16} /> Nova assembleia
            </button>
          </div>
        )}
      </div>

      {erro && !modal && <div className="alert-banner alert-banner-error">{erro}</div>}

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "0.5rem 0 0.75rem" }}>
        Assembleias
      </h2>
      <div className="dashboard-content-panel">
        {assembleias.length === 0 ? (
          <div className="dashboard-empty">Nenhuma assembleia cadastrada.</div>
        ) : (
          <div className="list-stack">
            {assembleias.map((a) => (
              <Link key={a.id} to={`/app/governanca/assembleias/${a.id}`} className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                  <Gavel size={20} style={{ marginTop: 2, color: "#9a6a0b" }} />
                  <div>
                    <p className="list-card-title">{a.titulo}</p>
                    <p className="list-card-meta">
                      {a.tipo_display} · {dataHora(a.data_hora)} · {a.modalidade_display}
                      {a.presentes > 0 && ` · ${a.presentes} presentes`}
                      {a.ata_publicada_em && " · ata publicada"}
                    </p>
                  </div>
                </div>
                <span className={`status-badge status-badge-${BADGE_STATUS[a.status]}`}>{a.status_display}</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", margin: "1.75rem 0 0.75rem" }}>
        Votações
      </h2>
      <div className="dashboard-content-panel">
        {votacoes.length === 0 ? (
          <div className="dashboard-empty">Nenhuma votação cadastrada.</div>
        ) : (
          <div className="list-stack">
            {votacoes.map((v) => (
              <Link key={v.id} to={`/app/governanca/votacoes/${v.id}`} className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                  <Vote size={20} style={{ marginTop: 2, color: "#9a6a0b" }} />
                  <div>
                    <p className="list-card-title">{v.titulo}</p>
                    <p className="list-card-meta">
                      {v.tipo_display} · {v.censo_display}
                      {v.assembleia_titulo && ` · ${v.assembleia_titulo}`}
                      {v.fecha_em && v.status === "aberta" && ` · até ${dataHora(v.fecha_em)}`}
                    </p>
                  </div>
                </div>
                <span className={`status-badge status-badge-${BADGE_STATUS[v.status]}`}>{v.status_display}</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {modal === "assembleia" && (
        <div className="dashboard-modal-overlay" onClick={() => setModal(null)}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 640 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">Nova assembleia</h2>
            </div>
            <form onSubmit={criarAssembleia}>
              <div className="dashboard-modal-content page-form">
                {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
                <div className="form-group">
                  <label className="form-label">Título</label>
                  <input className="form-input" required placeholder="Assembleia Geral Ordinária 2026" value={formA.titulo} onChange={(e) => setFormA({ ...formA, titulo: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Tipo</label>
                    <select className="form-select" value={formA.tipo} onChange={(e) => setFormA({ ...formA, tipo: e.target.value as TipoAssembleia })}>
                      <option value="ordinaria">Ordinária</option>
                      <option value="extraordinaria">Extraordinária</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Data e hora</label>
                    <input className="form-input" type="datetime-local" required value={formA.data_hora} onChange={(e) => setFormA({ ...formA, data_hora: e.target.value })} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Modalidade</label>
                    <select className="form-select" value={formA.modalidade} onChange={(e) => setFormA({ ...formA, modalidade: e.target.value as Modalidade })}>
                      <option value="presencial">Presencial</option>
                      <option value="online">Online</option>
                      <option value="hibrida">Híbrida</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Quórum mínimo (% dos aptos)</label>
                    <input className="form-input" type="number" min={0} max={100} placeholder="Sem quórum" value={formA.quorum_minimo} onChange={(e) => setFormA({ ...formA, quorum_minimo: e.target.value })} />
                  </div>
                </div>
                {formA.modalidade !== "online" && (
                  <div className="form-group">
                    <label className="form-label">Local</label>
                    <input className="form-input" value={formA.local} onChange={(e) => setFormA({ ...formA, local: e.target.value })} />
                  </div>
                )}
                {formA.modalidade !== "presencial" && (
                  <div className="form-group">
                    <label className="form-label">Link da reunião online</label>
                    <input className="form-input" type="url" value={formA.link_online} onChange={(e) => setFormA({ ...formA, link_online: e.target.value })} />
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Ordem do dia (um item por linha)</label>
                  <textarea className="form-input" rows={4} value={formA.pauta} onChange={(e) => setFormA({ ...formA, pauta: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Texto do edital de convocação</label>
                  <textarea className="form-input" rows={4} value={formA.convocacao} onChange={(e) => setFormA({ ...formA, convocacao: e.target.value })} />
                </div>
              </div>
              <div className="dashboard-modal-footer">
                <button type="button" className="dashboard-btn-secondary" onClick={() => setModal(null)}>
                  Cancelar
                </button>
                <button type="submit" className="dashboard-btn-new" disabled={salvando}>
                  {salvando ? "Salvando..." : "Criar rascunho"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modal === "votacao" && (
        <div className="dashboard-modal-overlay" onClick={() => setModal(null)}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 640 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">Nova votação</h2>
            </div>
            <form onSubmit={criarVotacao}>
              <div className="dashboard-modal-content page-form">
                {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
                <div className="form-group">
                  <label className="form-label">Título</label>
                  <input className="form-input" required value={formV.titulo} onChange={(e) => setFormV({ ...formV, titulo: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Tipo</label>
                    <select className="form-select" value={formV.tipo} onChange={(e) => setFormV({ ...formV, tipo: e.target.value as TipoVotacao })}>
                      <option value="eleicao">Eleição (chapas ou candidatos)</option>
                      <option value="deliberacao">Deliberação (aprovo / rejeito / abstenção)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Quem vota</label>
                    <select className="form-select" value={formV.censo} onChange={(e) => setFormV({ ...formV, censo: e.target.value as CensoVotacao })}>
                      <option value="adimplentes">Associados em dia</option>
                      <option value="ativos">Todos os associados ativos</option>
                    </select>
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Assembleia (opcional)</label>
                    <select className="form-select" value={formV.assembleia} onChange={(e) => setFormV({ ...formV, assembleia: e.target.value })}>
                      <option value="">Votação avulsa</option>
                      {assembleiasAbertas.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.titulo}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Prazo para votar (opcional)</label>
                    <input className="form-input" type="datetime-local" value={formV.fecha_em} onChange={(e) => setFormV({ ...formV, fecha_em: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Descrição / regras</label>
                  <textarea className="form-input" rows={3} value={formV.descricao} onChange={(e) => setFormV({ ...formV, descricao: e.target.value })} />
                </div>
                {formV.tipo === "eleicao" && (
                  <>
                    <OpcoesEditor opcoes={opcoes} onChange={setOpcoes} />
                    <div className="form-group">
                      <label className="form-label">Máximo de escolhas por eleitor</label>
                      <input className="form-input" type="number" min={1} value={formV.max_escolhas} onChange={(e) => setFormV({ ...formV, max_escolhas: e.target.value })} />
                    </div>
                  </>
                )}
                <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.9rem" }}>
                  <input type="checkbox" checked={formV.permite_branco} onChange={(e) => setFormV({ ...formV, permite_branco: e.target.checked })} />
                  Aceitar voto em branco
                </label>
                <p className="list-card-meta" style={{ margin: 0 }}>
                  O voto é secreto: o sistema registra quem votou, mas não em quem. O censo é fixado na abertura.
                </p>
              </div>
              <div className="dashboard-modal-footer">
                <button type="button" className="dashboard-btn-secondary" onClick={() => setModal(null)}>
                  Cancelar
                </button>
                <button type="submit" className="dashboard-btn-new" disabled={salvando}>
                  {salvando ? "Salvando..." : "Criar rascunho"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
