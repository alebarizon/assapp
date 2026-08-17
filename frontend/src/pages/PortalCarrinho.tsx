import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, CheckCircle, Minus, Plus, Trash2 } from "lucide-react";
import {
  checkoutCart,
  clearCart,
  getCart,
  removeFromCart,
  updateCartItem,
} from "@/services/ecommerce";
import type { Cart } from "@/types/ecommerce";

export default function PortalCarrinho() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [checkingOut, setCheckingOut] = useState(false);
  const [paymentMode, setPaymentMode] = useState<"simulated" | "manual">("simulated");

  const load = async () => {
    setLoading(true);
    setErro("");
    try {
      setCart(await getCart());
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErro(detail || "Erro ao carregar carrinho.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const updateQty = async (itemId: string, quantity: number) => {
    try {
      setCart(await updateCartItem(itemId, quantity));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErro(detail || "Erro ao atualizar quantidade.");
    }
  };

  const remove = async (itemId: string) => {
    try {
      setCart(await removeFromCart(itemId));
    } catch {
      setErro("Erro ao remover item.");
    }
  };

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) return;
    setCheckingOut(true);
    setErro("");
    try {
      const order = await checkoutCart({ payment_method: paymentMode });
      if (paymentMode === "simulated") {
        setMsg(`Pedido ${order.order_number} concluído com sucesso!`);
      } else {
        setMsg(
          `Pedido ${order.order_number} registrado. Aguarde confirmação da tesouraria após o pagamento.`
        );
      }
      setCart(await getCart());
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErro(detail || "Erro no checkout.");
    } finally {
      setCheckingOut(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Carrinho</h1>
          <p className="dashboard-subtitle">
            {cart ? `${cart.item_count} item(ns) · Total R$ ${cart.total}` : "Seu carrinho"}
          </p>
        </div>
        <div className="dashboard-header-actions">
          <Link to="/app/portal/loja" className="dashboard-btn-cancel" style={{ textDecoration: "none" }}>
            Voltar à loja
          </Link>
        </div>
      </div>

      {msg && (
        <div className="alert-banner alert-banner-success" style={{ display: "flex", gap: "0.5rem" }}>
          <CheckCircle size={16} /> {msg}
        </div>
      )}
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
        ) : !cart || cart.items.length === 0 ? (
          <div className="dashboard-empty">
            Carrinho vazio.{" "}
            <Link to="/app/portal/loja">Ir à loja</Link>
          </div>
        ) : (
          <>
            <div className="list-stack">
              {cart.items.map((item) => (
                <div key={item.id} className="list-card">
                  <div>
                    <p className="list-card-title">{item.catalog_item.name}</p>
                    <p className="list-card-meta">
                      {item.catalog_item.item_type_display} · R$ {item.subtotal}
                    </p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <button
                      type="button"
                      className="dashboard-btn-cancel"
                      onClick={() => updateQty(item.id, item.quantity - 1)}
                    >
                      <Minus size={14} />
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      type="button"
                      className="dashboard-btn-cancel"
                      onClick={() => updateQty(item.id, item.quantity + 1)}
                    >
                      <Plus size={14} />
                    </button>
                    <button type="button" className="dashboard-btn-cancel" onClick={() => remove(item.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="page-form-container" style={{ marginTop: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label">Forma de pagamento</label>
                <select
                  className="form-select"
                  value={paymentMode}
                  onChange={(e) => setPaymentMode(e.target.value as "simulated" | "manual")}
                >
                  <option value="simulated">Pagamento imediato (demo / dev)</option>
                  <option value="manual">Transferência — aguardar confirmação</option>
                </select>
              </div>
              <div className="form-actions">
                <button
                  type="button"
                  className="dashboard-btn-cancel"
                  onClick={() => clearCart().then(load)}
                >
                  Limpar carrinho
                </button>
                <button
                  type="button"
                  className="dashboard-btn-save"
                  disabled={checkingOut}
                  onClick={handleCheckout}
                >
                  {checkingOut ? "Processando..." : `Finalizar — R$ ${cart.total}`}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
