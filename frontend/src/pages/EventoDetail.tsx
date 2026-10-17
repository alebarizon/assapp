/**
 * Detalhe do Evento — CFP, submissões, pareceres e geração de anais (H3)
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, ClipboardList, FilePlus, Send, UserCheck } from "lucide-react";
import { createFormulario, listFormularios } from "@/services/formularios";
import type { FormularioResumo } from "@/types/formularios";
import InscricoesCertificados from "@/components/eventos/InscricoesCertificados";
import { FORMULARIO_STATUS_BADGE, novaPergunta } from "@/types/formularios";
import type { EventoAcademico, SubmissaoTrabalho } from "@/types/eventos";
import { useAuth } from "@/contexts/AuthContext";
import { listMembros } from "@/services/membros";
import type { Membro } from "@/types/membros";
import {
  abrirCfp,
  atribuirParecerista,
  concluirParecer,
  createSubmissao,
  gerarAnais,
  getEvento,
  listSubmissoesEvento,
  submeterTrabalho,
} from "@/services/eventos";

export default function EventoDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [evento, setEvento] = useState<EventoAcademico | null>(null);
  const [submissoes, setSubmissoes] = useState<SubmissaoTrabalho[]>([]);
  const [membros, setMembros] = useState<Membro[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [aba, setAba] = useState<"cfp" | "submissoes" | "anais" | "avaliacao" | "inscricoes">("submissoes");
  const [totalInscricoes, setTotalInscricoes] = useState<number | null>(null);
  const [avaliacoes, setAvaliacoes] = useState<FormularioResumo[]>([]);

  const [showCfpForm, setShowCfpForm] = useState(false);
  const [showSubForm, setShowSubForm] = useState(false);
  const [cfpForm, setCfpForm] = useState({
    titulo: "",
    instrucoes: "Submissões em português ou inglês. Resumo de até 500 palavras.",
    data_abertura: "",
    data_fechamento: "",
    areas: "Cibercultura, Mídia Digital, Redes Sociais",
  });
  const [subForm, setSubForm] = useState({
    titulo: "",
    resumo: "",
    area_tematica: "",
    membro_id: "",
  });

  const carregar = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    const [ev, subs, mbs, forms] = await Promise.all([
      getEvento(id),
      listSubmissoesEvento(id),
      listMembros(),
      listFormularios({ evento: id }).catch(() => []),
    ]);
    setEvento(ev);
    setSubmissoes(subs);
    setMembros(mbs);
    setAvaliacoes(forms);
    setLoading(false);
  }, [id]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const handleCriarAvaliacao = async () => {
    if (!id || !evento) return;
    const escala = (texto: string) => ({ ...novaPergunta(), texto, tipo: "escala" as const, obrigatoria: true });
    const form = await createFormulario({
      titulo: `Avaliação — ${evento.titulo}`,
      evento: id,
      link_publico_ativo: true,
      pedir_identificacao: false,
      mensagem_confirmacao: "Obrigado por avaliar o evento!",
      secoes: [
        {
          titulo: "",
          descricao: "",
          perguntas: [
            escala("Avaliação geral do evento"),
            escala("Qualidade da programação científica"),
            escala("Organização e infraestrutura"),
            {
              ...novaPergunta(),
              texto: "Você participaria de uma próxima edição?",
              tipo: "escolha_unica",
              opcoes: ["Sim", "Talvez", "Não"],
            },
            { ...novaPergunta(), texto: "Sugestões e comentários", tipo: "texto_longo" },
          ],
        },
      ],
    });
    navigate(`/app/formularios/${form.id}`);
  };

  const handleAbrirCfp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    await abrirCfp(id, {
      titulo: cfpForm.titulo || `CFP — ${evento?.titulo}`,
      instrucoes: cfpForm.instrucoes,
      data_abertura: new Date(cfpForm.data_abertura).toISOString(),
      data_fechamento: new Date(cfpForm.data_fechamento).toISOString(),
      areas_tematicas: cfpForm.areas.split(",").map((a) => a.trim()),
    });
    setShowCfpForm(false);
    setMsg("Call for Papers aberto!");
    await carregar();
  };

  const handleNovaSubmissao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evento?.call_for_papers) return;
    const sub = await createSubmissao({
      cfp: evento.call_for_papers.id,
      titulo: subForm.titulo,
      resumo: subForm.resumo,
      area_tematica: subForm.area_tematica || undefined,
      membro_id: subForm.membro_id || undefined,
    });
    await submeterTrabalho(sub.id);
    setShowSubForm(false);
    setSubForm({ titulo: "", resumo: "", area_tematica: "", membro_id: "" });
    setMsg("Trabalho submetido!");
    await carregar();
  };

  const handleAtribuirParecer = async (submissaoId: string) => {
    if (!user?.id) return;
    await atribuirParecerista(submissaoId, user.id);
    setMsg("Parecerista atribuído (você).");
    await carregar();
  };

  const handleConcluirParecer = async (parecerId: string) => {
    const rec = prompt("Recomendação: aceitar / aceitar_com_revisoes / rejeitar", "aceitar");
    if (!rec || !["aceitar", "aceitar_com_revisoes", "rejeitar"].includes(rec)) return;
    await concluirParecer(parecerId, {
      recomendacao: rec as "aceitar" | "aceitar_com_revisoes" | "rejeitar",
      nota: 4,
      comentarios_autor: "Parecer registrado via AssApp.",
    });
    setMsg("Parecer concluído.");
    await carregar();
  };

  const handleGerarAnais = async () => {
    if (!id || !confirm("Gerar anais com trabalhos aceitos?")) return;
    await gerarAnais(id);
    setMsg("Anais publicados!");
    setAba("anais");
    await carregar();
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  if (!evento) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-error">Evento não encontrado.</div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <Link
        to="/app/eventos"
        className="dashboard-btn-secondary"
        style={{ marginBottom: "1.25rem", display: "inline-flex", textDecoration: "none", width: "fit-content" }}
      >
        <ArrowLeft size={16} /> Voltar
      </Link>

      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">{evento.titulo}</h1>
          <p className="dashboard-subtitle">
            {new Date(evento.data_inicio).toLocaleString("pt-BR")} — {evento.local || evento.modalidade}
          </p>
          {evento.descricao && (
            <p className="dashboard-subtitle" style={{ marginTop: "0.5rem" }}>
              {evento.descricao}
            </p>
          )}
        </div>
        <div className="dashboard-header-actions">
          <span className={`status-badge status-badge-${evento.status}`}>
            {evento.status_display}
          </span>
        </div>
      </div>

      <div className="filters-row">
        {!evento.call_for_papers && (
          <button type="button" className="dashboard-btn-new" onClick={() => setShowCfpForm(!showCfpForm)}>
            <FilePlus size={16} /> Abrir CFP
          </button>
        )}
        {evento.call_for_papers && (
          <button type="button" className="dashboard-btn-edit" onClick={() => setShowSubForm(!showSubForm)}>
            <Send size={16} /> Nova submissão
          </button>
        )}
        {submissoes.some((s) => s.status === "aceito" || s.status === "aceito_com_revisoes") && (
          <button type="button" className="dashboard-btn-save" onClick={handleGerarAnais}>
            <BookOpen size={16} /> Gerar anais
          </button>
        )}
      </div>

      {msg && (
        <div className="alert-banner alert-banner-success" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ flex: 1 }}>{msg}</span>
          <button
            type="button"
            onClick={() => setMsg("")}
            style={{ background: "none", border: "none", cursor: "pointer", color: "inherit" }}
          >
            ×
          </button>
        </div>
      )}

      {showCfpForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleAbrirCfp}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              Abrir Call for Papers
            </h3>
            <div className="form-group">
              <label className="form-label">Título do CFP</label>
              <input
                className="form-input"
                placeholder="Título do CFP"
                value={cfpForm.titulo}
                onChange={(e) => setCfpForm({ ...cfpForm, titulo: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Instruções</label>
              <textarea
                className="form-input"
                placeholder="Instruções"
                value={cfpForm.instrucoes}
                onChange={(e) => setCfpForm({ ...cfpForm, instrucoes: e.target.value })}
                rows={3}
              />
            </div>
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Abertura</label>
                <input
                  className="form-input"
                  required
                  type="datetime-local"
                  value={cfpForm.data_abertura}
                  onChange={(e) => setCfpForm({ ...cfpForm, data_abertura: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Fechamento</label>
                <input
                  className="form-input"
                  required
                  type="datetime-local"
                  value={cfpForm.data_fechamento}
                  onChange={(e) => setCfpForm({ ...cfpForm, data_fechamento: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Áreas temáticas (vírgula)</label>
              <input
                className="form-input"
                placeholder="Áreas temáticas (vírgula)"
                value={cfpForm.areas}
                onChange={(e) => setCfpForm({ ...cfpForm, areas: e.target.value })}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowCfpForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Abrir CFP
              </button>
            </div>
          </form>
        </div>
      )}

      {showSubForm && evento.call_for_papers && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleNovaSubmissao}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              Nova submissão
            </h3>
            <div className="form-group">
              <label className="form-label">Título do trabalho</label>
              <input
                className="form-input"
                required
                placeholder="Título do trabalho"
                value={subForm.titulo}
                onChange={(e) => setSubForm({ ...subForm, titulo: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Resumo</label>
              <textarea
                className="form-input"
                required
                placeholder="Resumo"
                value={subForm.resumo}
                rows={4}
                onChange={(e) => setSubForm({ ...subForm, resumo: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Área temática</label>
              <select
                className="form-select"
                value={subForm.area_tematica}
                onChange={(e) => setSubForm({ ...subForm, area_tematica: e.target.value })}
              >
                <option value="">Área temática</option>
                {evento.call_for_papers.areas_tematicas.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Autor membro (H3 — integração)</label>
              <select
                className="form-select"
                value={subForm.membro_id}
                onChange={(e) => setSubForm({ ...subForm, membro_id: e.target.value })}
              >
                <option value="">Autor membro (H3 — integração)</option>
                {membros.map((m) => (
                  <option key={m.id} value={m.id}>{m.nome_completo}</option>
                ))}
              </select>
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowSubForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Submeter
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-tabs">
        {(["submissoes", "cfp", "anais", "inscricoes", "avaliacao"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setAba(t)}
            className={`dashboard-tab${aba === t ? " active" : ""}`}
          >
            {t === "submissoes"
              ? `Submissões (${submissoes.length})`
              : t === "cfp"
                ? "CFP"
                : t === "anais"
                  ? "Anais"
                  : t === "inscricoes"
                    ? `Inscrições e certificados${totalInscricoes !== null ? ` (${totalInscricoes})` : ""}`
                    : `Avaliação (${avaliacoes.length})`}
          </button>
        ))}
      </div>

      {aba === "inscricoes" && (
        <InscricoesCertificados
          evento={evento}
          membros={membros}
          onEventoAtualizado={() => void getEvento(evento.id).then(setEvento)}
          onTotal={setTotalInscricoes}
        />
      )}

      {aba === "avaliacao" && (
        <div className="dashboard-content-panel">
          <div className="filters-row" style={{ justifyContent: "space-between" }}>
            <p className="list-card-meta" style={{ margin: 0 }}>
              Formulários vinculados a este evento (avaliação dos participantes, pesquisas).
            </p>
            <button type="button" className="dashboard-btn-new" onClick={handleCriarAvaliacao}>
              <ClipboardList size={14} /> Criar formulário de avaliação
            </button>
          </div>
          {avaliacoes.length === 0 ? (
            <div className="dashboard-empty">Nenhum formulário vinculado.</div>
          ) : (
            <div className="list-stack">
              {avaliacoes.map((f) => (
                <Link
                  key={f.id}
                  to={`/app/formularios/${f.id}`}
                  className="list-card"
                  style={{ display: "flex", justifyContent: "space-between", textDecoration: "none", color: "inherit" }}
                >
                  <div>
                    <p className="list-card-title">{f.titulo}</p>
                    <p className="list-card-meta">{f.respostas_enviadas} resposta(s)</p>
                  </div>
                  <span className={`status-badge status-badge-${FORMULARIO_STATUS_BADGE[f.status]}`}>
                    {f.status_display}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {aba === "cfp" && evento.call_for_papers && (
        <div className="dashboard-content-panel">
          <p className="list-card-title">{evento.call_for_papers.titulo}</p>
          <p className="list-card-meta">{evento.call_for_papers.instrucoes}</p>
          <p className="list-card-meta">
            {new Date(evento.call_for_papers.data_abertura).toLocaleDateString("pt-BR")} —{" "}
            {new Date(evento.call_for_papers.data_fechamento).toLocaleDateString("pt-BR")}
          </p>
          <p className="list-card-meta">Áreas: {evento.call_for_papers.areas_tematicas.join(", ")}</p>
          <p className="list-card-meta">
            Parecer duplo-cego: {evento.call_for_papers.anonimo ? "Sim" : "Não"}
          </p>
        </div>
      )}

      {aba === "submissoes" && (
        <div className="dashboard-content-panel">
          {submissoes.length === 0 ? (
            <div className="dashboard-empty">Nenhuma submissão ainda.</div>
          ) : (
            <div className="list-stack">
              {submissoes.map((s) => (
                <div key={s.id} className="list-card" style={{ alignItems: "flex-start", flexDirection: "column" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: "1rem" }}>
                    <div>
                      <p className="list-card-title">{s.titulo}</p>
                      <p className="list-card-meta">
                        {s.membro_nome ? `Membro: ${s.membro_nome}` : s.autor_email} · {s.area_tematica}
                      </p>
                      <p className="list-card-meta">{s.resumo}</p>
                    </div>
                    <span className={`status-badge status-badge-${s.status}`}>
                      {s.status_display}
                    </span>
                  </div>

                  <div className="filters-row" style={{ marginBottom: 0, marginTop: "0.75rem" }}>
                    {s.status === "submetido" && (
                      <button
                        type="button"
                        className="dashboard-btn-secondary"
                        onClick={() => handleAtribuirParecer(s.id)}
                      >
                        <UserCheck size={14} /> Atribuir parecerista
                      </button>
                    )}
                    {s.pareceres?.map((p) => (
                      <div key={p.id} className="list-card-meta" style={{ margin: 0 }}>
                        Parecer: {p.parecerista_email} —{" "}
                        {p.concluido ? (
                          <span className="status-badge status-badge-aceito">{p.recomendacao_display}</span>
                        ) : (
                          <button
                            type="button"
                            className="dashboard-btn-edit"
                            onClick={() => handleConcluirParecer(p.id)}
                          >
                            concluir
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {aba === "anais" && (
        <div className="dashboard-content-panel">
          {evento.anais ? (
            <div>
              <p className="list-card-title">{evento.anais.titulo}</p>
              <p className="list-card-meta">
                Publicado em{" "}
                {evento.anais.publicado_em &&
                  new Date(evento.anais.publicado_em).toLocaleDateString("pt-BR")}
              </p>
              <p className="list-card-meta">
                {evento.anais.metadata?.total_trabalhos ?? 0} trabalho(s) nos anais:
              </p>
              <div className="list-stack" style={{ marginTop: "0.75rem" }}>
                {evento.anais.metadata?.trabalhos?.map((t) => (
                  <div key={t.id} className="list-card">
                    <div>
                      <p className="list-card-title">{t.titulo}</p>
                      <p className="list-card-meta">{t.autor}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="dashboard-empty">
              Anais ainda não publicados. Aceite trabalhos e clique em &quot;Gerar anais&quot;.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
