import type { ModuloPainel, NivelAcesso, PerfilAcesso } from "@/types";

export interface UsuarioEquipe {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  nome: string;
  perfis: PerfilAcesso[];
  is_active: boolean;
  last_login: string | null;
  date_joined: string;
  convite_pendente: boolean;
  cargos: string[];
  perfis_sugeridos: PerfilAcesso[];
  is_self: boolean;
  email_enviado?: boolean;
}

export interface ConvitePayload {
  email: string;
  first_name: string;
  last_name: string;
  perfis: PerfilAcesso[];
}

export interface PerfisInfo {
  perfis: { value: PerfilAcesso; label: string }[];
  modulos: { value: ModuloPainel; label: string }[];
  matriz: Record<PerfilAcesso, Partial<Record<ModuloPainel, NivelAcesso>>>;
  sugestao_por_cargo: Record<string, PerfilAcesso>;
}
