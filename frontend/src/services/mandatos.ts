import type { LoginResponse, Mandato, OnboardingEtapa, TransicaoMandato, User } from "@/types";
import { api } from "./api";
import { getCurrentUser as authGetCurrentUser, login as authLogin } from "./auth";

export async function login(email: string, password: string): Promise<LoginResponse> {
  return authLogin(email, password);
}

export async function getCurrentUser(): Promise<User> {
  return authGetCurrentUser();
}

export async function updatePerfilTecnico(perfil: User["perfil_tecnico"]): Promise<User> {
  const { data } = await api.patch<User>("/api/auth/me/", { perfil_tecnico: perfil });
  return data;
}

export async function listMandatos(): Promise<Mandato[]> {
  const { data } = await api.get<{ results?: Mandato[] } | Mandato[]>("/api/mandatos/mandatos/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getMandato(id: string): Promise<Mandato> {
  const { data } = await api.get<Mandato>(`/api/mandatos/mandatos/${id}/`);
  return data;
}

export async function getMandatoAtivo(): Promise<Mandato | null> {
  try {
    const { data } = await api.get<Mandato>("/api/mandatos/mandatos/ativo/");
    return data;
  } catch {
    return null;
  }
}

export async function createMandato(payload: Partial<Mandato>): Promise<Mandato> {
  const { data } = await api.post<Mandato>("/api/mandatos/mandatos/", payload);
  return data;
}

export async function iniciarTransicao(
  mandatoAnteriorId: string,
  mandatoNovoId: string,
  notas?: string
): Promise<TransicaoMandato> {
  const { data } = await api.post<TransicaoMandato>(
    `/api/mandatos/mandatos/${mandatoAnteriorId}/transicao/`,
    { mandato_novo_id: mandatoNovoId, notas_transicao: notas }
  );
  return data;
}

export async function getTransicaoEmAndamento(): Promise<TransicaoMandato | null> {
  try {
    const { data } = await api.get<TransicaoMandato>("/api/mandatos/transicoes/em_andamento/");
    return data;
  } catch {
    return null;
  }
}

export async function listOnboardingEtapas(transicaoId: string): Promise<OnboardingEtapa[]> {
  const { data } = await api.get<OnboardingEtapa[]>(
    `/api/mandatos/onboarding/?transicao=${transicaoId}`
  );
  return data;
}

export async function concluirEtapa(etapaId: string): Promise<OnboardingEtapa> {
  const { data } = await api.post<OnboardingEtapa>(
    `/api/mandatos/onboarding/${etapaId}/concluir/`,
    {}
  );
  return data;
}
