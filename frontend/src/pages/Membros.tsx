/**
 * Gestão de Membros — Sprint 4
 * Quadro de associados, filiações e anuidades.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle,
  Plus,
  RefreshCw,
  Search,
  Users,
} from "lucide-react";
import type { Membro, ResumoMembros } from "@/types/membros";
import { TIPOS_FILIACAO } from "@/types/membros";
import {
  atualizarAnuidadesVencidas,
  createMembro,
  gerarAnuidadesLote,
  getResumoMembros,
  listMembros,
} from "@/services/membros";

export default function Membros() {
  const [membros, setMembros] = useState<Membro[]>([]);
  const [resumo, setResumo] = useState<ResumoMembros | null>(null);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  const [form, setForm] = useState({
    nome_completo: "",
    email: "",
    cpf: "",
    instituicao: "",
    area_atuacao: "",
    tipo_filiacao: "efetivo" as const,
    consentimento_lgpd: false,
  });

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const [lista, kpis] = await Promise.all([
        listMembros({ q: busca || undefined, status_filiacao: filtroStatus || undefined }),
        getResumoMembros(),
      ]);
      setMembros(lista);
      setResumo(kpis);
    } catch {
      setErro("Erro ao carregar membros.");
    } finally {
      setLoading(false);
    }
  }, [busca, filtroStatus]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      await createMembro(form);
      setShowForm(false);
      setForm({
        nome_completo: "",
        email: "",
        cpf: "",
        instituicao: "",
        area_atuacao: "",
        tipo_filiacao: "efetivo",
        consentimento_lgpd: false,
      });
      await carregar();
      setMsg("Membro cadastrado com filiação ativa.");
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const first = data ? Object.values(data)[0]?.[0] : null;
      setErro(first || "Erro ao cadastrar membro.");
    } finally {
      setSalvando(false);
    }
  };

  const handleGerarAnuidades = async () => {
    const ano = new Date().getFullYear();
    if (!confirm(`Gerar anuidades de ${ano} para todas as filiações ativas?`)) return;
    const r = await gerarAnuidadesLote(ano);
    setMsg(`${r.criadas} anuidade(s) gerada(s), ${r.ignoradas} já existente(s).`);
    await carregar();
  };

  const handleAtualizarVencidas = async () => {
    const r = await atualizarAnuidadesVencidas();
    setMsg(
      `${r.anuidades_vencidas} anuidade(s) vencida(s), ${r.filiacoes_inadimplentes} filiação(ões) inadimplente(s).`
    );
    await carregar();
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Membros</h1>
          <p className="dashboard-subtitle">Quadro de associados, filiações e anuidades</p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-secondary" onClick={handleAtualizarVencidas}>
            <RefreshCw size={16} /> Atualizar vencidas
          </button>
          <button type="button" className="dashboard-btn-edit" onClick={handleGerarAnuidades}>
            Gerar anuidades {new Date().getFullYear()}
          </button>
          <button type="button" className="dashboard-btn-new" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> Novo membro
          </button>
        </div>
      </div>

      {resumo && (
        <div className="stats-grid">
          <div className="stat-widget clients-widget">
            <div className="stat-icon">
              <Users size={20} />
            </div>
            <div className="stat-content">
              <p className="stat-label">Total</p>
              <p className="stat-value">{resumo.total_membros}</p>
            </div>
          </div>
          <div className="stat-widget revenue-widget">
            <div className="stat-content">
              <p className="stat-label">Ativos</p>
              <p className="stat-value">{resumo.filiacoes_ativas}</p>
            </div>
          </div>
          <div className="stat-widget support-widget">
            <div className="stat-content">
              <p className="stat-label">Inadimplentes</p>
              <p className="stat-value">{resumo.filiacoes_inadimplentes}</p>
            </div>
          </div>
          <div className="stat-widget finance-widget">
            <div className="stat-content">
              <p className="stat-label">Anuid. pendentes</p>
              <p className="stat-value">{resumo.anuidades_pendentes}</p>
            </div>
          </div>
          <div className="stat-widget appointments-widget">
            <div className="stat-content">
              <p className="stat-label">Anuid. vencidas</p>
              <p className="stat-value">{resumo.anuidades_vencidas}</p>
            </div>
          </div>
        </div>
      )}

      {msg && (
        <div className="alert-banner alert-banner-success" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <CheckCircle size={16} /> {msg}
          <button type="button" onClick={() => setMsg("")} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "inherit" }}>
            ×
          </button>
        </div>
      )}
      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

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
            placeholder="Buscar por nome, e-mail, CPF..."
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
        <select
          className="form-select"
          value={filtroStatus}
          onChange={(e) => setFiltroStatus(e.target.value)}
        >
          <option value="">Todos os status</option>
          <option value="ativa">Ativos</option>
          <option value="inadimplente">Inadimplentes</option>
          <option value="suspensa">Suspensos</option>
        </select>
      </div>

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleSubmit}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              Novo associado
            </h3>
            <div className="form-row-2">
              <Field label="Nome completo *" value={form.nome_completo} onChange={(v) => setForm({ ...form, nome_completo: v })} required />
              <Field label="E-mail *" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
              <Field label="CPF" value={form.cpf} onChange={(v) => setForm({ ...form, cpf: v })} />
              <Field label="Instituição" value={form.instituicao} onChange={(v) => setForm({ ...form, instituicao: v })} />
              <Field label="Área de atuação" value={form.area_atuacao} onChange={(v) => setForm({ ...form, area_atuacao: v })} />
              <div className="form-group">
                <label className="form-label">Tipo de filiação</label>
                <select
                  className="form-select"
                  value={form.tipo_filiacao}
                  onChange={(e) => setForm({ ...form, tipo_filiacao: e.target.value as typeof form.tipo_filiacao })}
                >
                  {TIPOS_FILIACAO.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <label className="inline-check">
              <input
                type="checkbox"
                checked={form.consentimento_lgpd}
                onChange={(e) => setForm({ ...form, consentimento_lgpd: e.target.checked })}
              />
              <span>Associado consentiu com o tratamento de dados (LGPD) *</span>
            </label>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Salvando..." : "Cadastrar"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-content-panel">
        {loading ? (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
            <p>Carregando...</p>
          </div>
        ) : membros.length === 0 ? (
          <div className="dashboard-empty">Nenhum membro encontrado.</div>
        ) : (
          <div className="list-stack">
            {membros.map((m) => (
              <div key={m.id} className="list-card">
                <div>
                  <Link to={`/app/membros/${m.id}`} className="list-card-title" style={{ textDecoration: "none", color: "inherit" }}>
                    {m.nome_completo}
                  </Link>
                  <p className="list-card-meta">
                    {m.email} · {m.instituicao || "—"} · {m.filiacao_tipo || "—"}
                  </p>
                </div>
                <StatusBadge status={m.filiacao_status} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  if (!status) return <span className="list-card-meta">—</span>;
  const slug = status
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "_");
  return <span className={`status-badge status-badge-${slug}`}>{status}</span>;
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <input
        className="form-input"
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
