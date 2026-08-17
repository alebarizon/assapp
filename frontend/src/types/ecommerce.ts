export type CatalogItemType =
  | "anuidade"
  | "inscricao"
  | "curso"
  | "material"
  | "digital";

export type OrderStatus = "pending" | "paid" | "fulfilled" | "cancelled";

export interface CatalogItem {
  id: string;
  name: string;
  slug: string;
  description?: string;
  item_type: CatalogItemType;
  item_type_display: string;
  price: string;
  currency: string;
  inventory_count?: number | null;
  image_url?: string;
  is_active: boolean;
  anuidade_ano?: number | null;
  tipo_filiacao?: string | null;
  evento?: string | null;
  evento_titulo?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: string;
  catalog_item: CatalogItem;
  quantity: number;
  subtotal: string;
  created_at: string;
}

export interface Cart {
  id: string;
  membro_nome: string;
  items: CartItem[];
  total: string;
  item_count: number;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  catalog_item: string;
  catalog_item_name: string;
  item_type: CatalogItemType;
  item_type_display: string;
  quantity: number;
  price_at_purchase: string;
  subtotal: string;
  fulfillment_ref?: Record<string, unknown> | null;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  membro?: string | null;
  membro_nome?: string | null;
  membro_email?: string | null;
  total_amount: string;
  currency: string;
  status: OrderStatus;
  status_display: string;
  payment_method?: string;
  payment_method_display?: string;
  paid_at?: string | null;
  notes?: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface EcommerceResumo {
  itens_ativos: number;
  pedidos_pendentes: number;
  pedidos_pagos_mes: number;
}

export const CATALOG_ITEM_TYPES: { value: CatalogItemType; label: string }[] = [
  { value: "anuidade", label: "Anuidade" },
  { value: "inscricao", label: "Inscrição em evento" },
  { value: "curso", label: "Curso / workshop" },
  { value: "material", label: "Material físico" },
  { value: "digital", label: "Conteúdo digital" },
];

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending: "Pendente",
  paid: "Pago",
  fulfilled: "Concluído",
  cancelled: "Cancelado",
};
