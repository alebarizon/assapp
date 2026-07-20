import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("assapp_access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem("assapp_access", token);
  } else {
    localStorage.removeItem("assapp_access");
  }
}

export function getTenantSchema(): string | null {
  return localStorage.getItem("assapp_tenant_schema");
}

export function setTenantSchema(schema: string) {
  localStorage.setItem("assapp_tenant_schema", schema);
}
