import React, { useEffect, useState } from "react";
import { AlertCircle, Package, Plus, Search, Trash2 } from "lucide-react";
import { listEventos } from "@/services/eventos";
import {
  createCatalogItem,
  deleteCatalogItem,
  getEcommerceResumo,
  listCatalogItems,
  updateCatalogItem,
} from "@/services/ecommerce";
import type { CatalogItem, CatalogItemType, EcommerceResumo } from "@/types/ecommerce";
import { CATALOG_ITEM_TYPES } from "@/types/ecommerce";
import { TIPOS_FILIACAO as FILIACAO_OPTS } from "@/types/membros";

export default function EcommerceCatalog() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [resumo, setResumo] = useState<EcommerceResumo | null>(null);
  const [eventos, setEventos] = useState<{ id: string; titulo: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<CatalogItem | null>(null);
  const [salvando, setSalvando] = useState(false);

  const [form, setForm] = useState({
    name: "",
    description: "",
    item_type: "material" as CatalogItemType,
    price: "",
    inventory_count: "",
    image_url: "",
    is_active: true,
    anuidade_ano: String(new Date().getFullYear()),
    tipo_filiacao: "",
    evento: "",
  });

  const load = async () => {
    setLoading(true);
    setErro("");
    try {
      const [lista, kpis, evs] = await Promise.all([
        listCatalogItems({ search: busca || undefined }),
        getEcommerceResumo(),
        listEventos(),
      ]);
      setItems(lista);
      setResumo(kpis);
      setEventos(evs.map((e) => ({ id: e.id, titulo: e.titulo })));
    } catch {
      setErro("Erro ao carregar catálogo.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [busca]);

  const resetForm = () => {
    setForm({
      name: "",
      description: "",
      item_type: "material",
      price: "",
      inventory_count: "",
      image_url: "",
      is_active: true,
      anuidade_ano: String(new Date().getFullYear()),
      tipo_filiacao: "",
      evento: "",
    });
    setEditing(null);
  };

  const openEdit = (item: CatalogItem) => {
    setEditing(item);
    setForm({
      name: item.name,
      description: item.description ?? "",
      item_type: item.item_type,
      price: item.price,
      inventory_count: item.inventory_count != null ? String(item.inventory_count) : "",
      image_url: item.image_url ?? "",
      is_active: item.is_active,
      anuidade_ano: item.anuidade_ano ? String(item.anuidade_ano) : "",
      tipo_filiacao: item.tipo_filiacao ?? "",
      evento: item.evento ?? "",
    });
    setShowForm(true);
  };

  const buildPayload = () => {
    const payload: Record<string, unknown> = {
      name: form.name,
      description: form.description || null,
      item_type: form.item_type,
      price: form.price,
      image_url: form.image_url || null,
      is_active: form.is_active,
      currency: "BRL",
    };
    if (form.item_type === "material") {
      payload.inventory_count = form.inventory_count ? Number(form.inventory_count) : 0;
    } else if (form.inventory_count) {
      payload.inventory_count = Number(form.inventory_count);
    } else {
      payload.inventory_count = null;
    }
    if (form.item_type === "anuidade") {
      payload.anuidade_ano = Number(form.anuidade_ano);
      payload.tipo_filiacao = form.tipo_filiacao || null;
      payload.evento = null;
    } else if (form.item_type === "inscricao") {
      payload.evento = form.evento || null;
      payload.anuidade_ano = null;
    } else {
      payload.anuidade_ano = null;
      payload.evento = null;
    }
    return payload;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      const payload = buildPayload();
      if (editing) {
        await updateCatalogItem(editing.slug, payload);
      } else {
        await createCatalogItem(payload);
      }
      setShowForm(false);
      resetForm();
      await load();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao salvar item.";
      setErro(String(msg));
    } finally {
      setSalvando(false);
    }
  };

  const handleDelete = async (item: CatalogItem) => {
    if (!confirm(`Remover "${item.name}" do catálogo?`)) return;
    try {
      await deleteCatalogItem(item.slug);
      await load();
    } catch {
      setErro("Erro ao remover item.");
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Catálogo</h1>
          <p className="dashboard-subtitle">
            Anuidades, inscrições, cursos e materiais — vitrine unificada da associação
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button
            type="button"
            className="dashboard-btn-new"
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
          >
            <Plus size={16} /> Novo item
          </button>
        </div>
      </div>

      {resumo && (
        <div className="stats-grid">
          <div className="stat-widget clients-widget">
            <div className="stat-icon">
              <Package size={20} />
            </div>
            <div className="stat-content">
              <p className="stat-label">Itens ativos</p>
              <p className="stat-value">{resumo.itens_ativos}</p>
            </div>
          </div>
          <div className="stat-widget finance-widget">
            <div className="stat-content">
              <p className="stat-label">Pedidos pendentes</p>
              <p className="stat-value">{resumo.pedidos_pendentes}</p>
            </div>
          </div>
        </div>
      )}

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
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
            placeholder="Buscar no catálogo..."
            style={{ paddingLeft: "2.25rem", width: "100%" }}
          />
        </div>
      </div>

      {showForm && (
        <div className="page-form-container" style={{ marginBottom: "1.25rem" }}>
          <form className="page-form" onSubmit={handleSubmit}>
            <h3 className="page-form-title" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
              {editing ? "Editar item" : "Novo item do catálogo"}
            </h3>
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Nome *</label>
                <input
                  className="form-input"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tipo *</label>
                <select
                  className="form-select"
                  value={form.item_type}
                  onChange={(e) =>
                    setForm({ ...form, item_type: e.target.value as CatalogItemType })
                  }
                >
                  {CATALOG_ITEM_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Preço (R$) *</label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                />
              </div>
              {form.item_type === "material" && (
                <div className="form-group">
                  <label className="form-label">Estoque *</label>
                  <input
                    className="form-input"
                    type="number"
                    min="0"
                    required
                    value={form.inventory_count}
                    onChange={(e) => setForm({ ...form, inventory_count: e.target.value })}
                  />
                </div>
              )}
              {form.item_type === "anuidade" && (
                <>
                  <div className="form-group">
                    <label className="form-label">Ano da anuidade *</label>
                    <input
                      className="form-input"
                      type="number"
                      required
                      value={form.anuidade_ano}
                      onChange={(e) => setForm({ ...form, anuidade_ano: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tipo de filiação (opcional)</label>
                    <select
                      className="form-select"
                      value={form.tipo_filiacao}
                      onChange={(e) => setForm({ ...form, tipo_filiacao: e.target.value })}
                    >
                      <option value="">Qualquer</option>
                      {FILIACAO_OPTS.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              )}
              {form.item_type === "inscricao" && (
                <div className="form-group">
                  <label className="form-label">Evento *</label>
                  <select
                    className="form-select"
                    required
                    value={form.evento}
                    onChange={(e) => setForm({ ...form, evento: e.target.value })}
                  >
                    <option value="">Selecione...</option>
                    {eventos.map((ev) => (
                      <option key={ev.id} value={ev.id}>
                        {ev.titulo}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="form-group">
                <label className="form-label">URL da imagem</label>
                <input
                  className="form-input"
                  value={form.image_url}
                  onChange={(e) => setForm({ ...form, image_url: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Descrição</label>
              <textarea
                className="form-input"
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <label className="inline-check">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              <span>Item visível na loja</span>
            </label>
            <div className="form-actions">
              <button
                type="button"
                className="dashboard-btn-cancel"
                onClick={() => {
                  setShowForm(false);
                  resetForm();
                }}
              >
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Salvando..." : "Salvar"}
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
        ) : items.length === 0 ? (
          <div className="dashboard-empty">Nenhum item no catálogo.</div>
        ) : (
          <div className="list-stack">
            {items.map((item) => (
              <div key={item.id} className="list-card">
                <div>
                  <p className="list-card-title">{item.name}</p>
                  <p className="list-card-meta">
                    {item.item_type_display} · R$ {item.price}
                    {item.anuidade_ano ? ` · ${item.anuidade_ano}` : ""}
                    {item.evento_titulo ? ` · ${item.evento_titulo}` : ""}
                    {!item.is_active ? " · inativo" : ""}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    type="button"
                    className="dashboard-btn-edit"
                    onClick={() => openEdit(item)}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    className="dashboard-btn-cancel"
                    onClick={() => handleDelete(item)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
