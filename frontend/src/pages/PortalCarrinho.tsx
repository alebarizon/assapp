import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, CheckCircle, CreditCard, Minus, Plus, Trash2 } from "lucide-react";
import {
  checkoutCart,
  clearCart,
  getCart,
  listOrders,
  removeFromCart,
  updateCartItem,
} from "@/services/ecommerce";
import { cobrarPedido, getDisponibilidadePagamento } from "@/services/pagamentos";
import PagamentoModal from "@/components/pagamentos/PagamentoModal";
import type { Cart, Order } from "@/types/ecommerce";
import type { DisponibilidadePagamento } from "@/types/pagamentos";
import { formatBRL, temPrecoSocio } from "@/utils/tenantSite";

export default function PortalCarrinho() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [checkingOut, setCheckingOut] = useState(false);
  const [paymentMode, setPaymentMode] = useState<"simulated" | "manual" | "online">("manual");
  const [disponibilidade, setDisponibilidade] = useState<DisponibilidadePagamento | null>(null);
  const [pendentes, setPendentes] = useState<Order[]>([]);
  const [pagando, setPagando] = useState<Order | null>(null);

  const carregarPendentes = () =>
    listOrders({ status: "pending" })
      .then(setPendentes)
      .catch(() => setPendentes([]));

  useEffect(() => {
    getDisponibilidadePagamento()
      .then((d) => {
        setDisponibilidade(d);
        setPaymentMode(d.habilitado ? "online" : d.demo ? "simulated" : "manual");
      })
      .catch(() => setDisponibilidade(null));
    void carregarPendentes();
  }, []);

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
      if (order.status !== "pending") {
        setMsg(`Pedido ${order.order_number} concluído com sucesso!`);
      } else if (paymentMode === "online") {
        setPagando(order);
        void carregarPendentes();
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
            {cart ? `${cart.item_count} item(ns) · Total ${formatBRL(cart.total)}` : "Seu carrinho"}
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
                      {item.catalog_item.item_type_display} · {formatBRL(item.subtotal)}
                      {cart.adimplente && temPrecoSocio(item.catalog_item) && " · preço de sócio"}
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

            {Number(cart.total_cheio) > Number(cart.total) && (
              <div className="alert-banner alert-banner-success" style={{ marginTop: "1rem" }}>
                Você economiza {formatBRL(Number(cart.total_cheio) - Number(cart.total))} por estar com a anuidade em
                dia.
              </div>
            )}
            {!cart.adimplente && cart.items.some((i) => temPrecoSocio(i.catalog_item)) && (
              <div className="alert-banner alert-banner-info" style={{ marginTop: "1rem" }}>
                Com a anuidade em dia, este carrinho sairia por{" "}
                {formatBRL(
                  cart.items.reduce(
                    (soma, i) =>
                      soma +
                      i.quantity *
                        Number(temPrecoSocio(i.catalog_item) ? i.catalog_item.member_price : i.catalog_item.price),
                    0
                  )
                )}
                . <Link to="/app/portal/perfil">Regularizar minha anuidade</Link>
              </div>
            )}

            <div className="page-form-container" style={{ marginTop: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label">Forma de pagamento</label>
                <select
                  className="form-select"
                  value={paymentMode}
                  onChange={(e) => setPaymentMode(e.target.value as "simulated" | "manual" | "online")}
                >
                  {disponibilidade?.habilitado && <option value="online">Pagar online — Pix, cartão ou boleto</option>}
                  {disponibilidade?.demo && <option value="simulated">Pagamento imediato (demonstração)</option>}
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
                  {checkingOut ? "Processando..." : `Finalizar — ${formatBRL(cart.total)}`}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {pendentes.length > 0 && (
        <div className="dashboard-content-panel" style={{ marginTop: "1.25rem" }}>
          <h3 className="list-card-title" style={{ marginTop: 0 }}>
            Pedidos aguardando pagamento
          </h3>
          <div className="list-stack">
            {pendentes.map((pedido) => (
              <div key={pedido.id} className="list-card">
                <div>
                  <p className="list-card-title">{pedido.order_number}</p>
                  <p className="list-card-meta">
                    {pedido.items.map((i) => i.catalog_item_name).join(", ")} · {formatBRL(pedido.total_amount)}
                  </p>
                </div>
                {disponibilidade?.habilitado ? (
                  <button type="button" className="dashboard-btn-new" onClick={() => setPagando(pedido)}>
                    <CreditCard size={16} /> Pagar
                  </button>
                ) : (
                  <span className="list-card-meta">Aguardando confirmação da tesouraria</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {pagando && disponibilidade && (
        <PagamentoModal
          titulo={`Pedido ${pagando.order_number} — ${formatBRL(pagando.total_amount)}`}
          mensagemPago="Pagamento confirmado. Seu pedido foi concluído — inscrições e cursos já estão liberados."
          gerar={(metodo) => cobrarPedido(pagando.id, metodo)}
          disponibilidade={disponibilidade}
          onClose={() => {
            setPagando(null);
            void carregarPendentes();
          }}
          onPago={() => void carregarPendentes()}
        />
      )}
    </div>
  );
}
