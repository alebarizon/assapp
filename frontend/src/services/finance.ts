import { api } from "./api";

export type TxType = "income" | "expense";

export interface Transaction {
  id: string;
  user_email?: string | null;
  mandato?: string | null;
  description: string;
  amount: string;
  type: TxType;
  type_display: string;
  category: string;
  category_display: string;
  occurred_at: string;
  referencia?: string | null;
  created_at: string;
}

export interface FinancialDashboard {
  period: {
    month: number;
    year: number;
    month_name: string;
    start_date: string;
    end_date: string;
  };
  total_income: string;
  total_expense: string;
  balance: string;
  is_negative: boolean;
  generated_at: string;
}

export interface CategoryOption {
  value: string;
  label: string;
}

export const INCOME_CATEGORIES: CategoryOption[] = [
  { value: "anuidade", label: "Anuidade" },
  { value: "evento", label: "Evento / inscrição" },
  { value: "doacao", label: "Doação" },
  { value: "patrocinio", label: "Patrocínio" },
  { value: "outros", label: "Outros" },
];

export const EXPENSE_CATEGORIES: CategoryOption[] = [
  { value: "administrativa", label: "Administrativa" },
  { value: "evento", label: "Evento" },
  { value: "comunicacao", label: "Comunicação / publicação" },
  { value: "impostos", label: "Impostos / taxas" },
  { value: "outros", label: "Outros" },
];

export async function getDashboard(month: number, year: number): Promise<FinancialDashboard> {
  const { data } = await api.get<FinancialDashboard>("/api/finance/dashboard/", {
    params: { month, year },
  });
  return data;
}

export async function listTransactions(params?: {
  type?: TxType;
  category?: string;
  start_date?: string;
  end_date?: string;
}): Promise<Transaction[]> {
  const { data } = await api.get<{ results?: Transaction[] } | Transaction[]>(
    "/api/finance/transactions/",
    { params }
  );
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createTransaction(payload: {
  description: string;
  amount: number;
  type: TxType;
  category: string;
  occurred_at: string;
}): Promise<Transaction> {
  const { data } = await api.post<Transaction>("/api/finance/transactions/", payload);
  return data;
}

export async function updateTransaction(
  id: string,
  payload: Partial<{
    description: string;
    amount: number;
    type: TxType;
    category: string;
    occurred_at: string;
  }>
): Promise<Transaction> {
  const { data } = await api.patch<Transaction>(`/api/finance/transactions/${id}/`, payload);
  return data;
}

export async function deleteTransaction(id: string): Promise<void> {
  await api.delete(`/api/finance/transactions/${id}/`);
}

export async function sendReportEmail(payload: {
  month: number;
  year: number;
  recipient_email?: string;
}): Promise<{ detail: string; recipient: string }> {
  const { data } = await api.post("/api/finance/send-report-email/", payload);
  return data;
}
