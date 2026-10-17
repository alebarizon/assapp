import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Award, Download, Trash2, UserPlus } from "lucide-react";
import {
  createInscricao,
  deleteInscricao,
  downloadCertificadoInscricao,
  emitirCertificados,
  listInscricoes,
  marcarPresencas,
  updateEvento,
} from "@/services/eventos";
import { apiErrorMessage } from "@/utils/apiError";
import type { EventoAcademico, InscricaoEvento } from "@/types/eventos";
import type { Membro } from "@/types/membros";
import "./Eventos.css";

interface Props {
  evento: EventoAcademico;
  membros: Membro[];
  onEventoAtualizado: () => void;
  onTotal?: (total: number) => void;
}

export default function InscricoesCertificados({ evento, membros, onEventoAtualizado, onTotal }: Props) {
  const [inscricoes, setInscricoes] = useState<InscricaoEvento[]>([]);
  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set());
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [novo, setNovo] = useState({ membro: "", nome: "", email: "" });
  const [cargaHoraria, setCargaHoraria] = useState(evento.carga_horaria ? String(evento.carga_horaria) : "");
  const [notificar, setNotificar] = useState(true);
  const [emitindo, setEmitindo] = useState(false);

  const load = useCallback(async () => {
    try {
      const lista = await listInscricoes(evento.id);
      setInscricoes(lista);
      onTotal?.(lista.length);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar inscrições."));
    }
  }, [evento.id, onTotal]);

  useEffect(() => {
    void load();
  }, [load]);

  const presentes = inscricoes.filter((i) => i.presente).length;
  const pendentesEmissao = inscricoes.filter((i) => i.presente && !i.certificado_codigo).length;
  const emitidos = inscricoes.filter((i) => i.certificado_codigo).length;
  const todasSelecionadas = inscricoes.length > 0 && selecionadas.size === inscricoes.length;
  const membrosDisponiveis = useMemo(() => {
    const inscritos = new Set(inscricoes.map((i) => i.membro).filter(Boolean));
    return membros.filter((m) => !inscritos.has(m.id));
  }, [membros, inscricoes]);

  const run = async (fn: () => Promise<void>, fallback: string) => {
    setErro("");
    setAviso("");
    try {
      await fn();
    } catch (err) {
      setErro(apiErrorMessage(err, fallback));
    }
  };

  const toggle = (id: string) =>
    setSelecionadas((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  const presenca = (presente: boolean, ids = Array.from(selecionadas)) =>
    run(async () => {
      await marcarPresencas(evento.id, ids, presente);
      setSelecionadas(new Set());
      await load();
    }, "Erro ao registrar presença.");

  const adicionar = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      await createInscricao({
        evento: evento.id,
        confirmada: true,
        ...(novo.membro ? { membro: novo.membro } : { nome: novo.nome.trim(), email: novo.email.trim() }),
      });
      setNovo({ membro: "", nome: "", email: "" });
      setShowForm(false);
      await load();
    }, "Erro ao inscrever.");
  };

  const remover = (i: InscricaoEvento) => {
    if (!window.confirm(`Remover a inscrição de ${i.nome}?`)) return;
    void run(async () => {
      await deleteInscricao(i.id);
      await load();
    }, "Erro ao remover.");
  };

  const salvarConfig = (payload: Partial<EventoAcademico>) =>
    run(async () => {
      await updateEvento(evento.id, payload);
      onEventoAtualizado();
    }, "Erro ao salvar configuração.");

  const emitir = () =>
    run(async () => {
      setEmitindo(true);
      try {
        const r = await emitirCertificados(evento.id, notificar);
        const partes = [`${r.emitidos} certificado(s) emitido(s)`];
        if (notificar) partes.push(`${r.emails_enviados} e-mail(s) enviado(s)`);
        if (r.inscritos_sem_presenca) partes.push(`${r.inscritos_sem_presenca} inscrito(s) sem presença registrada`);
        await load();
        setAviso(`${partes.join(" · ")}.`);
      } finally {
        setEmitindo(false);
      }
    }, "Erro ao emitir certificados.");

  return (
    <div className="dashboard-content-panel">
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {aviso && <div className="highlight-banner">{aviso}</div>}

      <div className="list-card" style={{ flexDirection: "column", alignItems: "stretch", gap: "0.75rem", marginBottom: "1rem" }}>
        <p className="list-card-title" style={{ margin: 0 }}>
          <Award size={16} style={{ verticalAlign: "-3px" }} /> Certificados de participação
        </p>
        <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", alignItems: "center" }}>
          <label className="inline-check">
            <input
              type="checkbox"
              checked={evento.certificado_habilitado !== false}
              onChange={(e) => void salvarConfig({ certificado_habilitado: e.target.checked })}
            />
            Emitir certificados para este evento
          </label>
          <label style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.875rem" }}>
            Carga horária (h)
            <input
              className="form-input"
              type="number"
              min={1}
              max={999}
              value={cargaHoraria}
              onChange={(e) => setCargaHoraria(e.target.value)}
              onBlur={() => {
                const valor = cargaHoraria ? Number(cargaHoraria) : null;
                if (valor !== (evento.carga_horaria ?? null)) void salvarConfig({ carga_horaria: valor });
              }}
              style={{ width: "6rem" }}
            />
          </label>
        </div>
        <p className="list-card-meta" style={{ margin: 0 }}>
          {presentes} presente(s) de {inscricoes.length} inscrito(s) · {emitidos} certificado(s) emitido(s). O certificado
          traz um QR code para verificação pública em /site/certificados.
        </p>
        {evento.certificado_habilitado !== false && (
          <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
            <button type="button" className="dashboard-btn-new" disabled={!pendentesEmissao || emitindo} onClick={() => void emitir()}>
              <Award size={14} /> {emitindo ? "Emitindo..." : `Emitir certificados (${pendentesEmissao})`}
            </button>
            <label className="inline-check">
              <input type="checkbox" checked={notificar} onChange={(e) => setNotificar(e.target.checked)} />
              Enviar por e-mail aos participantes
            </label>
          </div>
        )}
      </div>

      <div className="filters-row" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button type="button" className="dashboard-btn-secondary" disabled={!selecionadas.size} onClick={() => void presenca(true)}>
            Marcar presença ({selecionadas.size})
          </button>
          <button type="button" className="dashboard-btn-secondary" disabled={!selecionadas.size} onClick={() => void presenca(false)}>
            Remover presença
          </button>
        </div>
        <button type="button" className="dashboard-btn-new" onClick={() => setShowForm((v) => !v)}>
          <UserPlus size={14} /> Inscrever participante
        </button>
      </div>

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1rem" }}>
          <form className="page-form" onSubmit={adicionar}>
            <div className="form-group">
              <label className="form-label">Associado</label>
              <select className="form-select" value={novo.membro} onChange={(e) => setNovo({ ...novo, membro: e.target.value })}>
                <option value="">— Participante externo (informe nome e e-mail) —</option>
                {membrosDisponiveis.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome_completo}
                  </option>
                ))}
              </select>
            </div>
            {!novo.membro && (
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Nome *</label>
                  <input className="form-input" required value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">E-mail *</label>
                  <input className="form-input" type="email" required value={novo.email} onChange={(e) => setNovo({ ...novo, email: e.target.value })} />
                </div>
              </div>
            )}
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Inscrever
              </button>
            </div>
          </form>
        </div>
      )}

      {inscricoes.length === 0 ? (
        <div className="dashboard-empty">Nenhuma inscrição registrada.</div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="evento-insc-table">
            <thead>
              <tr>
                <th style={{ width: 32 }}>
                  <input
                    type="checkbox"
                    aria-label="Selecionar todas"
                    checked={todasSelecionadas}
                    onChange={() => setSelecionadas(todasSelecionadas ? new Set() : new Set(inscricoes.map((i) => i.id)))}
                  />
                </th>
                <th>Participante</th>
                <th>Presença</th>
                <th>Certificado</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {inscricoes.map((i) => (
                <tr key={i.id}>
                  <td>
                    <input type="checkbox" aria-label={`Selecionar ${i.nome}`} checked={selecionadas.has(i.id)} onChange={() => toggle(i.id)} />
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{i.nome}</div>
                    <div className="list-card-meta" style={{ margin: 0 }}>
                      {i.email}
                      {i.membro ? " · associado" : ""}
                    </div>
                  </td>
                  <td>
                    <button
                      type="button"
                      className={`status-badge status-badge-${i.presente ? "ativo" : "arquivado"}`}
                      style={{ cursor: "pointer" }}
                      onClick={() => void presenca(!i.presente, [i.id])}
                      title="Clique para alternar"
                    >
                      {i.presente ? "Presente" : "Sem registro"}
                    </button>
                  </td>
                  <td>
                    {i.certificado_codigo ? (
                      <span style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>{i.certificado_codigo}</span>
                    ) : (
                      <span className="list-card-meta">—</span>
                    )}
                  </td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    {i.certificado_codigo && (
                      <button
                        type="button"
                        className="dashboard-btn-secondary"
                        title="Baixar PDF"
                        onClick={() => void run(() => downloadCertificadoInscricao(i), "Erro ao baixar.")}
                      >
                        <Download size={14} />
                      </button>
                    )}{" "}
                    <button type="button" className="dashboard-btn-secondary" title="Remover inscrição" onClick={() => remover(i)}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
