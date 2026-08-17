import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, Plus, ShoppingCart } from "lucide-react";
import { addToCart, listLojaItems } from "@/services/ecommerce";
import type { CatalogItem } from "@/types/ecommerce";

export default function PortalLoja() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [adding, setAdding] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setItems(await listLojaItems());
      } catch {
        setErro("Erro ao carregar a loja.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleAdd = async (item: CatalogItem) => {
    setAdding(item.id);
    setErro("");
    try {
      await addToCart(item.id, 1);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setErro(data?.detail || data?.catalog_item || "Não foi possível adicionar ao carrinho.");
    } finally {
      setAdding(null);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Loja</h1>
          <p className="dashboard-subtitle">Anuidades, eventos, cursos e materiais da associação</p>
        </div>
        <div className="dashboard-header-actions">
          <Link to="/app/portal/carrinho" className="dashboard-btn-edit" style={{ textDecoration: "none" }}>
            <ShoppingCart size={16} /> Carrinho
          </Link>
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      <div className="dashboard-content-panel">
        {loading ? (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
            <p>Carregando...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="dashboard-empty">Nenhum item disponível no momento.</div>
        ) : (
          <div className="list-stack">
            {items.map((item) => (
              <div key={item.id} className="list-card">
                <div>
                  <p className="list-card-title">{item.name}</p>
                  <p className="list-card-meta">
                    {item.item_type_display} · R$ {item.price}
                  </p>
                  {item.description && (
                    <p style={{ margin: "0.35rem 0 0", fontSize: "0.875rem" }}>{item.description}</p>
                  )}
                </div>
                <button
                  type="button"
                  className="dashboard-btn-new"
                  disabled={adding === item.id}
                  onClick={() => handleAdd(item)}
                >
                  <Plus size={16} />
                  {adding === item.id ? "..." : "Adicionar"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
