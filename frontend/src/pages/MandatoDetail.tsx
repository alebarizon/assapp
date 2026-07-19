/**
 * MandatoDetail — H1: cargos, timeline e snapshots do ciclo de gestão
 */
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Clock } from "lucide-react";
import type { Mandato, MandatoSnapshot } from "@/types";
import type { TimelineEvento } from "@/types/memoria";
import { getMandato } from "@/services/mandatos";
import { listTimeline } from "@/services/memoria";

function resumoSnapshot(dados: Record<string, unknown>): string {
  const parts: string[] = [];
  const membros = dados.membros as { ativos?: number; inadimplentes?: number } | undefined;
  if (membros) {
    parts.push(`${membros.ativos ?? 0} ativos / ${membros.inadimplentes ?? 0} inadimpl.`);
  }
  const anuidades = dados.anuidades as {
    pagas?: number;
    pendentes?: number;
    vencidas?: number;
  } | undefined;
  if (anuidades) {
    parts.push(
      `anuidades ${anuidades.pagas ?? 0}p / ${anuidades.pendentes ?? 0}pend / ${anuidades.vencidas ?? 0}venc`
    );
  }
  const financeiro = dados.financeiro as { saldo?: string } | null | undefined;
  if (financeiro?.saldo != null) {
    parts.push(`saldo mês R$ ${financeiro.saldo}`);
  }
  const eventos = dados.eventos as { ativos?: number } | undefined;
  if (eventos) {
    parts.push(`${eventos.ativos ?? 0} eventos ativos`);
  }
  const cargos = dados.cargos as unknown[] | undefined;
  if (Array.isArray(cargos)) {
    parts.push(`${cargos.length} cargos`);
  }
  return parts.length ? parts.join(" · ") : Object.keys(dados).join(", ");
}

export default function MandatoDetail() {
  const { id } = useParams<{ id: string }>();
  const [mandato, setMandato] = useState<Mandato | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [snapAberto, setSnapAberto] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [m, tl] = await Promise.all([getMandato(id), listTimeline(id)]);
        if (!cancelled) {
          setMandato(m);
          setTimeline(tl);
        }
      } catch {
        if (!cancelled) setError("Erro ao carregar mandato.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando mandato...</p>
        </div>
      </div>
    );
  }

  if (error || !mandato) {
    return (
      <div className="dashboard-page">
        <Link
          to="/app/mandatos"
          className="dashboard-btn-secondary"
          style={{ marginBottom: "1.25rem", display: "inline-flex", textDecoration: "none", width: "fit-content" }}
        >
          <ArrowLeft size={16} /> Voltar
        </Link>
        <div className="dashboard-error">{error || "Mandato não encontrado."}</div>
      </div>
    );
  }

  const cargos = mandato.cargos ?? [];
  const snapshots = mandato.snapshots ?? [];

  return (
    <div className="dashboard-page">
      <Link
        to="/app/mandatos"
        className="dashboard-btn-secondary"
        style={{ marginBottom: "1.25rem", display: "inline-flex", textDecoration: "none", width: "fit-content" }}
      >
        <ArrowLeft size={16} /> Voltar para lista
      </Link>

      <div className="dashboard-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <h1 className="dashboard-title" style={{ margin: 0 }}>
            {mandato.titulo}
          </h1>
          <span className={`status-badge status-badge-${mandato.status}`}>
            {mandato.status_display}
          </span>
        </div>
        <p className="dashboard-subtitle">
          #{mandato.numero_sequencial} · {mandato.data_inicio}
          {mandato.data_fim ? ` — ${mandato.data_fim}` : " — em exercício"}
        </p>
        {mandato.descricao && <p className="list-card-meta">{mandato.descricao}</p>}
      </div>

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
        Cargos da diretoria
      </h2>
      <div className="dashboard-content-panel" style={{ marginBottom: "1.5rem" }}>
        {cargos.length === 0 ? (
          <div className="dashboard-empty">Nenhum cargo vinculado.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Cargo</th>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {cargos.map((c) => (
                <tr key={c.id}>
                  <td>{c.cargo_custom || c.cargo_display}</td>
                  <td>{c.usuario_nome || "—"}</td>
                  <td>{c.usuario_email || "—"}</td>
                  <td>
                    <span
                      className={`status-badge status-badge-${c.ativo ? "ativa" : "pendente"}`}
                    >
                      {c.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
        Timeline institucional
      </h2>
      <div className="dashboard-content-panel" style={{ marginBottom: "1.5rem" }}>
        {timeline.length === 0 ? (
          <div className="dashboard-empty">
            Timeline vazia — registros de memória deste mandato aparecem aqui.
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

      <h2 className="dashboard-title" style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
        Snapshots (H1)
      </h2>
      <div className="dashboard-content-panel">
        {snapshots.length === 0 ? (
          <div className="dashboard-empty">Nenhum snapshot capturado ainda.</div>
        ) : (
          <div className="list-stack">
            {snapshots.map((s: MandatoSnapshot) => (
              <div key={s.id} className="list-card" style={{ flexDirection: "column", alignItems: "stretch" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.75rem",
                    flexWrap: "wrap",
                    alignItems: "flex-start",
                  }}
                >
                  <div>
                    <p className="list-card-title">
                      v{s.versao} · {s.tipo}
                      {s.integridade_ok === false ? " · integridade falhou" : ""}
                    </p>
                    <p className="list-card-meta">
                      {new Date(s.created_at).toLocaleString("pt-BR")} · {resumoSnapshot(s.dados || {})}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    onClick={() => setSnapAberto(snapAberto === s.id ? null : s.id)}
                  >
                    {snapAberto === s.id ? "Ocultar chaves" : "Ver chaves"}
                  </button>
                </div>
                {snapAberto === s.id && (
                  <pre
                    style={{
                      margin: "0.75rem 0 0",
                      fontSize: "0.75rem",
                      overflow: "auto",
                      maxHeight: "12rem",
                      background: "#f0efeb",
                      padding: "0.75rem",
                      borderRadius: "6px",
                    }}
                  >
                    {JSON.stringify(
                      Object.fromEntries(
                        Object.entries(s.dados || {}).map(([k, v]) => {
                          if (k === "decisoes_recentes" && Array.isArray(v)) {
                            return [k, `${v.length} itens`];
                          }
                          if (k === "eventos" && v && typeof v === "object") {
                            const ev = v as { ativos?: number; itens?: unknown[] };
                            return [k, { ativos: ev.ativos, itens: ev.itens?.length ?? 0 }];
                          }
                          return [k, v];
                        })
                      ),
                      null,
                      2
                    )}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
