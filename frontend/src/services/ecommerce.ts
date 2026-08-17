import type {
  Cart,
  CatalogItem,
  CatalogItemType,
  EcommerceResumo,
  Order,
  OrderStatus,
} from "@/types/ecommerce";
import { api } from "./api";

function unwrapList<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getEcommerceResumo(): Promise<EcommerceResumo> {
  const { data } = await api.get<EcommerceResumo>("/api/ecommerce/resumo/");
  return data;
}

export async function listCatalogItems(params?: {
  is_active?: boolean;
  item_type?: CatalogItemType;
  search?: string;
}): Promise<CatalogItem[]> {
  const { data } = await api.get("/api/ecommerce/catalog/", { params });
  return unwrapList(data);
}

export async function listLojaItems(): Promise<CatalogItem[]> {
  const { data } = await api.get<CatalogItem[]>("/api/ecommerce/catalog/loja/");
  return data;
}

export async function createCatalogItem(payload: Partial<CatalogItem>): Promise<CatalogItem> {
  const { data } = await api.post<CatalogItem>("/api/ecommerce/catalog/", payload);
  return data;
}

export async function updateCatalogItem(
  slug: string,
  payload: Partial<CatalogItem>
): Promise<CatalogItem> {
  const { data } = await api.patch<CatalogItem>(`/api/ecommerce/catalog/${slug}/`, payload);
  return data;
}

export async function deleteCatalogItem(slug: string): Promise<void> {
  await api.delete(`/api/ecommerce/catalog/${slug}/`);
}

export async function listOrders(params?: { status?: OrderStatus }): Promise<Order[]> {
  const { data } = await api.get("/api/ecommerce/orders/", { params });
  return unwrapList(data);
}

export async function confirmOrderPayment(orderId: string): Promise<Order> {
  const { data } = await api.post<Order>(`/api/ecommerce/orders/${orderId}/confirmar-pagamento/`, {});
  return data;
}

export async function getCart(): Promise<Cart> {
  const { data } = await api.get<Cart>("/api/ecommerce/cart/");
  return data;
}

export async function addToCart(catalogItemId: string, quantity = 1): Promise<Cart> {
  const { data } = await api.post<Cart>("/api/ecommerce/cart/add/", {
    catalog_item: catalogItemId,
    quantity,
  });
  return data;
}

export async function updateCartItem(itemId: string, quantity: number): Promise<Cart> {
  const { data } = await api.patch<Cart>(`/api/ecommerce/cart/update/${itemId}/`, { quantity });
  return data;
}

export async function removeFromCart(itemId: string): Promise<Cart> {
  const { data } = await api.delete<Cart>(`/api/ecommerce/cart/remove/${itemId}/`);
  return data;
}

export async function clearCart(): Promise<Cart> {
  const { data } = await api.post<Cart>("/api/ecommerce/cart/clear/", {});
  return data;
}

export async function checkoutCart(payload?: {
  notes?: string;
  payment_method?: "simulated" | "manual";
}): Promise<Order> {
  const { data } = await api.post<Order>("/api/ecommerce/cart/checkout/", payload ?? {});
  return data;
}
