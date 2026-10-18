import type { AxiosRequestConfig } from "axios";
import { api } from "@/services/api";

function nomeDoCabecalho(disposition?: string): string | null {
  const match = disposition?.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  return match ? decodeURIComponent(match[1]) : null;
}

/** `filename` vazio usa o nome enviado pelo servidor (Content-Disposition). */
export async function downloadBlob(url: string, filename: string, config?: AxiosRequestConfig) {
  const response = await api.get(url, { ...config, responseType: "blob" });
  filename = filename || nomeDoCabecalho(response.headers["content-disposition"]) || "arquivo";
  const href = URL.createObjectURL(response.data as Blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(href);
}
