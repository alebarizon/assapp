export type PerfilTecnico = "iniciante" | "intermediario" | "avancado";

export type MandatoStatus =
  | "planejado"
  | "ativo"
  | "transicao"
  | "encerrado"
  | "arquivado";

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  perfil_tecnico: PerfilTecnico;
  is_active: boolean;
  membro_id?: string | null;
  membro_nome?: string | null;
}

export interface Mandato {
  id: string;
  titulo: string;
  descricao?: string;
  data_inicio: string;
  data_fim?: string;
  status: MandatoStatus;
  status_display: string;
  numero_sequencial: number;
  cargos_count?: number;
  encerrado_em?: string;
  observacoes_encerramento?: string;
  created_at: string;
  updated_at?: string;
  cargos?: CargoMandato[];
  snapshots?: MandatoSnapshot[];
}

export interface CargoMandato {
  id: string;
  mandato: string;
  usuario: string;
  usuario_email?: string;
  usuario_nome?: string;
  cargo: string;
  cargo_display: string;
  cargo_custom?: string | null;
  data_inicio: string;
  data_fim?: string | null;
  ativo: boolean;
}

export interface MandatoSnapshot {
  id: string;
  mandato: string;
  tipo: string;
  versao: number;
  dados: Record<string, unknown>;
  hash: string;
  created_at: string;
  integridade_ok?: boolean;
}

export interface OnboardingEtapa {
  id: string;
  codigo: string;
  titulo: string;
  descricao?: string;
  ordem: number;
  obrigatoria: boolean;
  concluida: boolean;
  concluida_em?: string;
  perfil_minimo: PerfilTecnico;
  dados_contexto?: Record<string, unknown>;
  visivel?: boolean;
}

export interface TransicaoMandato {
  id: string;
  mandato_anterior: string;
  mandato_anterior_titulo: string;
  mandato_novo: string;
  mandato_novo_titulo: string;
  status: string;
  progresso_percentual: number;
  notas_transicao?: string;
  etapas_onboarding: OnboardingEtapa[];
}

export interface LoginResponse {
  user: User;
  tenant_schema: string;
  access: string;
  refresh: string;
  setup_completed?: boolean;
  tenant?: TenantStatus;
}

export interface TenantStatus {
  schema_name: string;
  setup_completed: boolean;
  plan_slug?: string | null;
  name?: string | null;
  cnpj?: string | null;
  city?: string | null;
  state?: string | null;
  description?: string | null;
  is_sistema?: boolean;
}

export interface SaasPlan {
  slug: string;
  name: string;
  description: string;
  price_label: string;
  trial_days: number;
}

export interface RegisterPayload {
  first_name: string;
  last_name?: string;
  email: string;
  password: string;
  association_name: string;
  tenant_slug: string;
  plan_slug: string;
  cnpj?: string;
  phone?: string;
  city?: string;
  state?: string;
}

export interface SetupPayload {
  association_name?: string;
  description?: string;
  city?: string;
  state?: string;
  cnpj?: string;
  mandato: {
    titulo: string;
    data_inicio: string;
    data_fim?: string;
    descricao?: string;
  };
  cargos: Array<{
    cargo: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    cargo_custom?: string;
  }>;
}

export interface SetupResponse {
  detail: string;
  setup_completed: boolean;
  mandato_id: string;
  tenant: TenantStatus;
}
