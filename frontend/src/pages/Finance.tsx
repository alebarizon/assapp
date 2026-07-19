import React, { useEffect, useState } from "react";
import { Mail, Plus, Trash2, TrendingDown, TrendingUp } from "lucide-react";
import {
  createTransaction,
  deleteTransaction,
  EXPENSE_CATEGORIES,
  getDashboard,
  INCOME_CATEGORIES,
  listTransactions,
  sendReportEmail,
  type FinancialDashboard,
  type Transaction,
  type TxType,
  updateTransaction,
} from "@/services/finance";

const MONTHS = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export default function Finance() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [dashboard, setDashboard] = useState<FinancialDashboard | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [formType, setFormType] = useState<TxType>("income");
  const [form, setForm] = useState({
    description: "",
    amount: "",
    category: "anuidade",
    occurred_at: new Date().toISOString().slice(0, 16),
  });
  const [emailTo, setEmailTo] = useState("");
  const [showEmail, setShowEmail] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const lastDay = new Date(year, month, 0).getDate();
      const start = `${year}-${String(month).padStart(2, "0")}-01`;
      const end = `${year}-${String(month).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}T23:59:59`;
      const [dash, txs] = await Promise.all([
        getDashboard(month, year),
        listTransactions({ start_date: start, end_date: end }),
      ]);
      setDashboard(dash);
      setTransactions(txs);
    } catch {
      setError("Erro ao carregar financeiro.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [month, year]);

  const categories = formType === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;

  const openNew = (type: TxType) => {
    setEditing(null);
    setFormType(type);
    setForm({
      description: "",
      amount: "",
      category: type === "income" ? "anuidade" : "administrativa",
      occurred_at: new Date().toISOString().slice(0, 16),
    });
    setShowForm(true);
  };

  const openEdit = (tx: Transaction) => {
    setEditing(tx);
    setFormType(tx.type);
    setForm({
      description: tx.description,
      amount: tx.amount,
      category: tx.category,
      occurred_at: tx.occurred_at.slice(0, 16),
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      description: form.description,
      amount: Number(form.amount),
      type: formType,
      category: form.category,
      occurred_at: new Date(form.occurred_at).toISOString(),
    };
    if (editing) {
      await updateTransaction(editing.id, payload);
    } else {
      await createTransaction(payload);
    }
    setShowForm(false);
    await load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Excluir este lançamento?")) return;
    await deleteTransaction(id);
    await load();
  };

  const handleEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await sendReportEmail({
        month,
        year,
        recipient_email: emailTo || undefined,
      });
      setMsg(`Relatório enviado para ${res.recipient}`);
      setShowEmail(false);
    } catch {
      setMsg("Falha ao enviar e-mail (verifique SMTP).");
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando financeiro...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Financeiro</h1>
          <p className="dashboard-subtitle">OSC — receitas, despesas e anuidades espelhadas</p>
        </div>
        <div className="dashboard-header-actions" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <select
            className="form-select"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="form-select"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {[year - 1, year, year + 1].map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <button type="button" className="dashboard-btn-new" onClick={() => openNew("income")}>
            <Plus size={16} /> Receita
          </button>
          <button type="button" className="dashboard-btn-secondary" onClick={() => openNew("expense")}>
            <TrendingDown size={16} /> Despesa
          </button>
          <button type="button" className="dashboard-btn-secondary" onClick={() => setShowEmail(true)}>
            <Mail size={16} /> Enviar fechamento
          </button>
        </div>
      </div>

      {error && <div className="alert-banner alert-banner-error">{error}</div>}
      {msg && <div className="alert-banner alert-banner-info">{msg}</div>}

      {dashboard && (
        <div className="stats-grid">
          <div className="stat-widget">
            <div className="stat-icon">
              <TrendingUp size={24} />
            </div>
            <div className="stat-content">
              <p className="stat-label">Receitas</p>
              <p className="stat-value">R$ {dashboard.total_income}</p>
            </div>
          </div>
          <div className="stat-widget">
            <div className="stat-icon">
              <TrendingDown size={24} />
            </div>
            <div className="stat-content">
              <p className="stat-label">Despesas</p>
              <p className="stat-value">R$ {dashboard.total_expense}</p>
            </div>
          </div>
          <div className="stat-widget">
            <div className="stat-content">
              <p className="stat-label">Saldo líquido</p>
              <p className="stat-value" style={{ color: dashboard.is_negative ? "#b42318" : undefined }}>
                R$ {dashboard.balance}
              </p>
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleSave}>
            <h3 className="page-form-title">
              {editing ? "Editar" : "Nova"} {formType === "income" ? "receita" : "despesa"}
            </h3>
            <div className="form-group">
              <label className="form-label">Descrição</label>
              <input
                className="form-input"
                required
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Valor</label>
                <input
                  className="form-input"
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Categoria</label>
                <select
                  className="form-select"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                >
                  {categories.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Data</label>
              <input
                className="form-input"
                type="datetime-local"
                required
                value={form.occurred_at}
                onChange={(e) => setForm({ ...form, occurred_at: e.target.value })}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowForm(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Salvar
              </button>
            </div>
          </form>
        </div>
      )}

      {showEmail && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleEmail}>
            <h3 className="page-form-title">Enviar fechamento por e-mail</h3>
            <div className="form-group">
              <label className="form-label">Destinatário</label>
              <input
                className="form-input"
                type="email"
                placeholder="tesouraria@associacao.org"
                value={emailTo}
                onChange={(e) => setEmailTo(e.target.value)}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowEmail(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save">
                Enviar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-content-panel">
        {transactions.length === 0 ? (
          <div className="dashboard-empty">Nenhum lançamento neste período.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th>Valor</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>{new Date(tx.occurred_at).toLocaleDateString("pt-BR")}</td>
                  <td>
                    <button
                      type="button"
                      className="dashboard-btn-secondary"
                      style={{ padding: "0.35rem 0.75rem" }}
                      onClick={() => openEdit(tx)}
                    >
                      {tx.description}
                    </button>
                  </td>
                  <td>
                    <span className={`status-badge status-badge-${tx.type === "income" ? "ativa" : "pendente"}`}>
                      {tx.type_display}
                    </span>
                  </td>
                  <td>{tx.category_display}</td>
                  <td>R$ {tx.amount}</td>
                  <td>
                    <button
                      type="button"
                      className="dashboard-btn-danger"
                      style={{ padding: "0.35rem 0.6rem" }}
                      onClick={() => handleDelete(tx.id)}
                      aria-label="Excluir"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
