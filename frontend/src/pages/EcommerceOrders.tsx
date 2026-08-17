import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, ShoppingBag } from "lucide-react";
import { confirmOrderPayment, listOrders } from "@/services/ecommerce";
import type { Order, OrderStatus } from "@/types/ecommerce";
import { ORDER_STATUS_LABELS } from "@/types/ecommerce";

export default function EcommerceOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [filtro, setFiltro] = useState<OrderStatus | "">("");
  const [confirmando, setConfirmando] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setErro("");
    try {
      const lista = await listOrders(filtro ? { status: filtro } : undefined);
      setOrders(lista);
    } catch {
      setErro("Erro ao carregar pedidos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [filtro]);

  const handleConfirm = async (order: Order) => {
    if (!confirm(`Confirmar pagamento do pedido ${order.order_number}?`)) return;
    setConfirmando(order.id);
    try {
      await confirmOrderPayment(order.id);
      setMsg(`Pedido ${order.order_number} confirmado.`);
      await load();
    } catch {
      setErro("Erro ao confirmar pagamento.");
    } finally {
      setConfirmando(null);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Pedidos</h1>
          <p className="dashboard-subtitle">Compras dos associados na loja Gesttora</p>
        </div>
      </div>

      {msg && (
        <div className="alert-banner alert-banner-success" style={{ display: "flex", gap: "0.5rem" }}>
          <CheckCircle size={16} /> {msg}
          <button
            type="button"
            onClick={() => setMsg("")}
            style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer" }}
          >
            ×
          </button>
        </div>
      )}
      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}

      <div className="filters-row">
        <select
          className="form-select"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value as OrderStatus | "")}
        >
          <option value="">Todos os status</option>
          {(Object.keys(ORDER_STATUS_LABELS) as OrderStatus[]).map((s) => (
            <option key={s} value={s}>
              {ORDER_STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      <div className="dashboard-content-panel">
        {loading ? (
          <div className="dashboard-loading">
            <div className="loading-spinner" />
            <p>Carregando...</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="dashboard-empty">Nenhum pedido encontrado.</div>
        ) : (
          <div className="list-stack">
            {orders.map((order) => (
              <div key={order.id} className="list-card">
                <div style={{ flex: 1 }}>
                  <p className="list-card-title">
                    <ShoppingBag size={16} style={{ display: "inline", marginRight: 6 }} />
                    {order.order_number}
                  </p>
                  <p className="list-card-meta">
                    {order.membro_nome || "—"} · {order.membro_email || ""} · R${" "}
                    {order.total_amount} · {order.status_display}
                    {order.paid_at ? ` · pago em ${new Date(order.paid_at).toLocaleDateString("pt-BR")}` : ""}
                  </p>
                  {order.items.length > 0 && (
                    <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.1rem", fontSize: "0.85rem" }}>
                      {order.items.map((it) => (
                        <li key={it.id}>
                          {it.catalog_item_name} ×{it.quantity} — R$ {it.subtotal}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                {order.status === "pending" && (
                  <button
                    type="button"
                    className="dashboard-btn-save"
                    disabled={confirmando === order.id}
                    onClick={() => handleConfirm(order)}
                  >
                    {confirmando === order.id ? "Confirmando..." : "Confirmar pagamento"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
