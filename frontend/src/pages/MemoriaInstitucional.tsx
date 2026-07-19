/**
 * Memória Institucional — H1
 *
 * Preservação ativa: cada registro documenta quem decidiu, o quê, por quê e em qual mandato.
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  Archive,
  BookMarked,
  Clock,
  Plus,
  Search,
  User,
} from "lucide-react";
import type { ContextoHistorico, TipoContexto } from "@/types/memoria";
import { TIPOS_CONTEXTO } from "@/types/memoria";
import type { Mandato } from "@/types";
import { getMandatoAtivo } from "@/services/mandatos";
import {
  arquivarContexto,
  createContexto,
  listContextos,
  listTimeline,
} from "@/services/memoria";
import type { TimelineEvento } from "@/types/memoria";

export default function MemoriaInstitucional() {
  const [mandatoAtivo, setMandatoAtivo] = useState<Mandato | null>(null);
  const [contextos, setContextos] = useState<ContextoHistorico[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvento[]>([]);
  const [loading, setLoading] = useState(true);
  const [aba, setAba] = useState<"registros" | "timeline">("registros");
  const [busca, setBusca] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const [form, setForm] = useState({
    tipo: "decisao" as TipoContexto,
    titulo: "",
    conteudo: "",
    decisao: "",
    motivo: "",
    tags: "",
  });

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const ativo = await getMandatoAtivo();
      setMandatoAtivo(ativo);
      if (ativo) {
        const [ctx, tl] = await Promise.all([
          listContextos({ mandato: ativo.id, q: busca || undefined, tipo: filtroTipo || undefined }),
          listTimeline(ativo.id),
        ]);
        setContextos(ctx);
        setTimeline(tl);
      }
    } catch {
      setErro("Erro ao carregar memória institucional.");
    } finally {
      setLoading(false);
    }
  }, [busca, filtroTipo]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mandatoAtivo) return;
    setSalvando(true);
    setErro("");
    try {
      await createContexto({
        mandato: mandatoAtivo.id,
        tipo: form.tipo,
        titulo: form.titulo,
        conteudo: form.conteudo,
        decisao: form.decisao || undefined,
        motivo: form.motivo || undefined,
        tags: form.tags
          ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
          : [],
      });
      setForm({ tipo: "decisao", titulo: "", conteudo: "", decisao: "", motivo: "", tags: "" });
      setShowForm(false);
      await carregar();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: Record<string, string[]> } })?.response?.data?.motivo?.[0];
      setErro(msg || "Erro ao salvar registro.");
    } finally {
      setSalvando(false);
    }
  };

  const handleArquivar = async (id: string) => {
    if (!confirm("Arquivar este registro? Ele permanece acessível com filtro de arquivados.")) return;
    await arquivarContexto(id);
    await carregar();
  };

  if (loading && !mandatoAtivo) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  if (!mandatoAtivo) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-empty">
          Nenhum mandato ativo. Configure um mandato antes de registrar memória institucional.
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
          <BookMarked size={16} />
          <span className="dashboard-subtitle" style={{ margin: 0 }}>
            H1 — Preservação Ativa de Memória
          </span>
        </div>
        <h1 className="dashboard-title">Memória Institucional</h1>
        <p className="dashboard-subtitle">
          Mandato: <strong>{mandatoAtivo.titulo}</strong> — registre decisões com contexto para a
          próxima diretoria.
        </p>
      </div>

      <div className="highlight-banner">
        <p className="highlight-banner-label">O que registrar aqui?</p>
        <p className="highlight-banner-meta">
          Decisões da diretoria, processos que funcionaram (ou não), contratos, fornecedores,
          regras de eventos — sempre com o <strong>motivo</strong> da decisão, para que a próxima
          gestão não precise reinventar tudo.
        </p>
      </div>

      <div className="dashboard-tabs">
        {(["registros", "timeline"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setAba(t)}
            className={`dashboard-tab${aba === t ? " active" : ""}`}
          >
            {t === "registros" ? "Registros" : "Timeline"}
          </button>
        ))}
      </div>

      {aba === "registros" && (
        <>
          <div className="filters-row">
            <div style={{ position: "relative", flex: 1, minWidth: "12rem" }}>
              <Search
                size={16}
                style={{ position: "absolute", left: "0.75rem", top: "0.7rem", color: "#a0a0a0" }}
              />
              <input
                className="form-input"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar registros..."
                style={{ paddingLeft: "2.25rem", width: "100%" }}
              />
            </div>
            <select
              className="form-select"
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
            >
              <option value="">Todos os tipos</option>
              {TIPOS_CONTEXTO.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="dashboard-btn-new"
              onClick={() => setShowForm(!showForm)}
            >
              <Plus size={16} /> Novo registro
            </button>
          </div>

          {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

          {showForm && (
            <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
              <form className="page-form" onSubmit={handleSubmit}>
                <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
                  Novo registro institucional
                </h3>

                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Tipo</label>
                    <select
                      className="form-select"
                      value={form.tipo}
                      onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoContexto })}
                    >
                      {TIPOS_CONTEXTO.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tags (separadas por vírgula)</label>
                    <input
                      className="form-input"
                      value={form.tags}
                      onChange={(e) => setForm({ ...form, tags: e.target.value })}
                      placeholder="financeiro, anuidade"
                    />
                  </div>
                </div>

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
                  <label className="form-label">Contexto / descrição *</label>
                  <textarea
                    className="form-input"
                    required
                    rows={3}
                    value={form.conteudo}
                    onChange={(e) => setForm({ ...form, conteudo: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">O que foi decidido?</label>
                  <input
                    className="form-input"
                    value={form.decisao}
                    onChange={(e) => setForm({ ...form, decisao: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Por quê? * {form.tipo === "decisao" && "(obrigatório para decisões — H1)"}
                  </label>
                  <textarea
                    className="form-input"
                    required={form.tipo === "decisao"}
                    rows={2}
                    value={form.motivo}
                    onChange={(e) => setForm({ ...form, motivo: e.target.value })}
                    placeholder="Explique o raciocínio para a próxima diretoria..."
                  />
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="dashboard-btn-cancel"
                    onClick={() => setShowForm(false)}
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                    {salvando ? "Salvando..." : "Salvar registro"}
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="dashboard-content-panel">
            {contextos.length === 0 ? (
              <div className="dashboard-empty">
                Nenhum registro ainda. Comece documentando uma decisão recente da diretoria.
              </div>
            ) : (
              <div className="list-stack">
                {contextos.map((ctx) => (
                  <ContextoCard key={ctx.id} contexto={ctx} onArquivar={handleArquivar} />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {aba === "timeline" && (
        <div className="dashboard-content-panel">
          {timeline.length === 0 ? (
            <div className="dashboard-empty">
              Timeline vazia — registros aparecem aqui automaticamente.
            </div>
          ) : (
            <div className="list-stack">
              {timeline.map((ev) => (
                <div key={ev.id} className="list-card" style={{ alignItems: "flex-start" }}>
                  <div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        marginBottom: "0.35rem",
                      }}
                    >
                      <Clock size={12} />
                      <span className="list-card-meta" style={{ margin: 0 }}>
                        {new Date(ev.data_evento).toLocaleString("pt-BR")}
                      </span>
                      <span className="status-badge">{ev.tipo}</span>
                    </div>
                    <p className="list-card-title">{ev.titulo}</p>
                    {ev.descricao && <p className="list-card-meta">{ev.descricao}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ContextoCard({
  contexto,
  onArquivar,
}: {
  contexto: ContextoHistorico;
  onArquivar: (id: string) => void;
}) {
  return (
    <div className="list-card" style={{ alignItems: "flex-start" }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.35rem" }}>
          <span className={`status-badge status-badge-${contexto.tipo}`}>
            {contexto.tipo_display}
          </span>
          {contexto.tags?.map((tag) => (
            <span key={tag} className="status-badge">
              {tag}
            </span>
          ))}
        </div>
        <p className="list-card-title">{contexto.titulo}</p>
        <p className="list-card-meta">{contexto.conteudo}</p>

        {contexto.decisao && (
          <div className="highlight-banner" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
            <p className="highlight-banner-label">Decisão</p>
            <p className="highlight-banner-meta" style={{ margin: 0 }}>
              {contexto.decisao}
            </p>
          </div>
        )}

        {contexto.motivo && (
          <div className="alert-banner alert-banner-info" style={{ marginTop: "0.5rem", marginBottom: 0 }}>
            <strong>Por quê</strong>
            <p style={{ margin: "0.25rem 0 0" }}>{contexto.motivo}</p>
          </div>
        )}

        <div
          className="list-card-meta"
          style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.75rem" }}
        >
          {contexto.autor_nome && (
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <User size={12} /> {contexto.autor_nome}
            </span>
          )}
          <span>{new Date(contexto.created_at).toLocaleDateString("pt-BR")}</span>
        </div>
      </div>

      {!contexto.arquivado && (
        <button
          type="button"
          className="dashboard-btn-secondary"
          onClick={() => onArquivar(contexto.id)}
          title="Arquivar"
        >
          <Archive size={16} />
        </button>
      )}
    </div>
  );
}
