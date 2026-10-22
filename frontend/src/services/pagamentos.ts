import type {
  Cobranca,
  ConfiguracaoPagamento,
  DisponibilidadePagamento,
  MetodoPagamento,
} from "@/types/pagamentos";
import { api } from "./api";

export async function getDisponibilidadePagamento(): Promise<DisponibilidadePagamento> {
  const { data } = await api.get<DisponibilidadePagamento>("/api/pagamentos/disponibilidade/");
  return data;
}

export async function cobrarPedido(pedidoId: string, metodo: MetodoPagamento): Promise<Cobranca> {
  const { data } = await api.post<Cobranca>(`/api/pagamentos/pedidos/${pedidoId}/cobrar/`, { metodo });
  return data;
}

export async function cobrarAnuidade(anuidadeId: string, metodo: MetodoPagamento): Promise<Cobranca> {
  const { data } = await api.post<Cobranca>(`/api/pagamentos/anuidades/${anuidadeId}/cobrar/`, { metodo });
  return data;
}

export async function getCobranca(id: string): Promise<Cobranca> {
  const { data } = await api.get<Cobranca>(`/api/pagamentos/cobrancas/${id}/`);
  return data;
}

export async function simularPagamento(id: string): Promise<Cobranca> {
  const { data } = await api.post<Cobranca>(`/api/pagamentos/cobrancas/${id}/simular-pagamento/`, {});
  return data;
}

export async function getConfiguracaoPagamento(): Promise<ConfiguracaoPagamento> {
  const { data } = await api.get<ConfiguracaoPagamento>("/api/pagamentos/configuracao/");
  return data;
}

export async function salvarConfiguracaoPagamento(
  payload: Partial<ConfiguracaoPagamento> & { api_key?: string }
): Promise<ConfiguracaoPagamento> {
  const { data } = await api.put<ConfiguracaoPagamento>("/api/pagamentos/configuracao/", payload);
  return data;
}

export async function testarConfiguracaoPagamento(): Promise<{ ok: boolean; saldo?: number; conta?: string }> {
  const { data } = await api.post("/api/pagamentos/configuracao/testar/", {});
  return data;
}
