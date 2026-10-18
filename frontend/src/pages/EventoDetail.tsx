/**
 * Detalhe do Evento — chamada de trabalhos, submissões, pareceres e geração de anais
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ClipboardList, FilePlus, Send } from "lucide-react";
import { createFormulario, listFormularios } from "@/services/formularios";
import type { FormularioResumo } from "@/types/formularios";
import InscricoesCertificados from "@/components/eventos/InscricoesCertificados";
import HotsiteEvento from "@/components/eventos/HotsiteEvento";
import ProgramacaoEvento from "@/components/eventos/ProgramacaoEvento";
import ChamadaTrabalhos from "@/components/eventos/ChamadaTrabalhos";
import SubmissoesComissao from "@/components/eventos/SubmissoesComissao";
import AnaisEvento from "@/components/eventos/AnaisEvento";
import { podeEditar } from "@/utils/roles";
import { FORMULARIO_STATUS_BADGE, novaPergunta } from "@/types/formularios";
import type { EventoAcademico, SubmissaoTrabalho } from "@/types/eventos";
import { useAuth } from "@/contexts/AuthContext";
import { listMembros } from "@/services/membros";
import type { Membro } from "@/types/membros";
import {
  createSubmissao,
  getEvento,
  listSubmissoesEvento,
  submeterTrabalho,
} from "@/services/eventos";

export default function EventoDetail() {
  const { id } = useParams<{ id: string }>();
  const { user, tenantSchema } = useAuth();
  const navigate = useNavigate();
  const [evento, setEvento] = useState<EventoAcademico | null>(null);
  const [submissoes, setSubmissoes] = useState<SubmissaoTrabalho[]>([]);
  const [membros, setMembros] = useState<Membro[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [aba, setAba] = useState<
    "cfp" | "submissoes" | "anais" | "avaliacao" | "inscricoes" | "site" | "programacao"
  >("submissoes");
  const [totalInscricoes, setTotalInscricoes] = useState<number | null>(null);
  const [avaliacoes, setAvaliacoes] = useState<FormularioResumo[]>([]);

  const [showSubForm, setShowSubForm] = useState(false);
  const editor = podeEditar(user, "eventos");
  const [subForm, setSubForm] = useState({
    titulo: "",
    resumo: "",
    area_tematica: "",
    membro_id: "",
  });

  const carregar = useCallback(async () => {
    if (!id) return;
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
        {editor && !evento.call_for_papers && (
          <button type="button" className="dashboard-btn-new" onClick={() => setAba("cfp")}>
            <FilePlus size={16} /> Abrir chamada de trabalhos
          </button>
        )}
        {editor && evento.call_for_papers && (
          <button type="button" className="dashboard-btn-edit" onClick={() => setShowSubForm(!showSubForm)}>
            <Send size={16} /> Registrar trabalho recebido
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

      {showSubForm && evento.call_for_papers && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleNovaSubmissao}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              Registrar trabalho recebido
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
              <label className="form-label">Autor associado</label>
              <select
                className="form-select"
                value={subForm.membro_id}
                onChange={(e) => setSubForm({ ...subForm, membro_id: e.target.value })}
              >
                <option value="">Selecione o associado</option>
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
        {(["submissoes", "cfp", "programacao", "site", "anais", "inscricoes", "avaliacao"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setAba(t)}
            className={`dashboard-tab${aba === t ? " active" : ""}`}
          >
            {t === "submissoes"
              ? `Submissões (${submissoes.length})`
              : t === "cfp"
                ? "Chamada"
                : t === "programacao"
                ? "Programação"
                : t === "site"
                ? "Site e inscrição"
                : t === "anais"
                  ? "Anais"
                  : t === "inscricoes"
                    ? `Inscrições e certificados${totalInscricoes !== null ? ` (${totalInscricoes})` : ""}`
                    : `Avaliação (${avaliacoes.length})`}
          </button>
        ))}
      </div>

      {aba === "site" && <HotsiteEvento evento={evento} onAtualizado={setEvento} />}

      {aba === "programacao" && <ProgramacaoEvento evento={evento} />}

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

      {aba === "cfp" && (
        <ChamadaTrabalhos
          key={evento.call_for_papers?.id ?? "nova"}
          evento={evento}
          podeEditar={editor}
          onSalvo={() => {
            setMsg("Chamada de trabalhos salva.");
            void carregar();
          }}
        />
      )}

      {aba === "submissoes" && (
        <SubmissoesComissao
          evento={evento}
          submissoes={submissoes}
          podeEditar={editor}
          onAtualizar={() => void carregar()}
          onMensagem={setMsg}
        />
      )}

      {aba === "anais" && (
        <AnaisEvento
          evento={evento}
          temAceitos={submissoes.some((s) => s.status === "aceito" || s.status === "aceito_com_revisoes")}
          podeEditar={editor}
          tenantSchema={tenantSchema}
          onAtualizado={() => void carregar()}
        />
      )}
    </div>
  );
}
