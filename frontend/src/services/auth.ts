import type {
  LoginResponse,
  RegisterPayload,
  SaasPlan,
  SetupPayload,
  SetupResponse,
  TenantStatus,
  User,
} from "@/types";
import { api } from "./api";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/api/auth/simple/login/", {
    email,
    password,
  });
  return data;
}

export async function register(payload: RegisterPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/api/auth/register/", payload);
  return data;
}

export async function listPlans(): Promise<SaasPlan[]> {
  const { data } = await api.get<SaasPlan[]>("/api/auth/plans/");
  return data;
}

export async function getTenantStatus(): Promise<TenantStatus> {
  const { data } = await api.get<TenantStatus>("/api/auth/tenant-status/");
  return data;
}

export async function completeSetup(payload: SetupPayload): Promise<SetupResponse> {
  const { data } = await api.post<SetupResponse>("/api/auth/setup/", payload);
  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/api/auth/me/");
  return data;
}
