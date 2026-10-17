import type { AxiosRequestConfig } from "axios";
import { api } from "@/services/api";

export async function downloadBlob(url: string, filename: string, config?: AxiosRequestConfig) {
  const response = await api.get(url, { ...config, responseType: "blob" });
  const href = URL.createObjectURL(response.data as Blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(href);
}
