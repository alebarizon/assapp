export type EventoStatus =
  | "rascunho"
  | "inscricoes_abertas"
  | "cfp_aberto"
  | "em_avaliacao"
  | "encerrado"
  | "anais_publicados"
  | "cancelado";

export type SubmissaoStatus =
  | "rascunho"
  | "submetido"
  | "em_parecer"
  | "aceito"
  | "aceito_com_revisoes"
  | "rejeitado"
  | "retirado";

export interface CallForPapers {
  id: string;
  evento: string;
  titulo: string;
  instrucoes: string;
  data_abertura: string;
  data_fechamento: string;
  areas_tematicas: string[];
  max_submissoes_por_autor: number;
  anonimo: boolean;
  criterios: CriterioAvaliacao[];
  criterios_efetivos: CriterioAvaliacao[];
  nota_corte: string | null;
  exige_arquivo: boolean;
  aberta: boolean;
  submissoes_count?: number;
}

export interface CriterioAvaliacao {
  nome: string;
  peso: number;
}

export interface Coautor {
  nome: string;
  email: string;
  instituicao: string;
}

export type Recomendacao = "aceitar" | "aceitar_com_revisoes" | "rejeitar";

export const RECOMENDACOES: { value: Recomendacao; label: string }[] = [
  { value: "aceitar", label: "Aceitar" },
  { value: "aceitar_com_revisoes", label: "Aceitar com revisões" },
  { value: "rejeitar", label: "Rejeitar" },
];

export interface Parecer {
  id: string;
  submissao: string;
  parecerista: string;
  parecerista_email?: string;
  parecerista_nome?: string;
  recomendacao?: Recomendacao | "";
  recomendacao_display?: string;
  nota?: number;
  notas?: Record<string, number>;
  nota_ponderada?: string | null;
  prazo?: string | null;
  comentarios_autor?: string;
  comentarios_internos?: string;
  concluido: boolean;
  concluido_em?: string;
}

export interface SubmissaoTrabalho {
  id: string;
  cfp: string;
  autor: string;
  autor_email?: string;
  membro?: string;
  membro_nome?: string;
  autoria?: string;
  coautores?: Coautor[];
  titulo: string;
  resumo: string;
  palavras_chave: string[];
  area_tematica?: string;
  tem_arquivo?: boolean;
  status: SubmissaoStatus;
  status_display: string;
  submetido_em?: string;
  pareceres?: Parecer[];
  nota_media?: string | null;
  decisao_comentario?: string;
  decidido_em?: string | null;
  created_at: string;
}

export interface ChamadaAberta {
  id: string;
  evento_id: string;
  evento_titulo: string;
  evento_inicio: string;
  titulo: string;
  instrucoes: string;
  data_abertura: string;
  data_fechamento: string;
  areas_tematicas: string[];
  max_submissoes_por_autor: number;
  anonimo: boolean;
  exige_arquivo: boolean;
  minhas_enviadas: number;
}

export interface MinhaSubmissao {
  id: string;
  cfp: string;
  evento_id: string;
  evento_titulo: string;
  titulo: string;
  resumo: string;
  palavras_chave: string[];
  coautores: Coautor[];
  area_tematica: string;
  tem_arquivo: boolean;
  status: SubmissaoStatus;
  status_display: string;
  submetido_em: string | null;
  decidido_em: string | null;
  decisao_comentario: string;
  comentarios_pareceres: string[];
  certificado_codigo: string | null;
  created_at: string;
}

export interface MeuParecer {
  id: string;
  prazo: string | null;
  concluido: boolean;
  concluido_em: string | null;
  recomendacao: Recomendacao | "";
  recomendacao_display: string;
  notas: Record<string, number>;
  nota_ponderada: string | null;
  comentarios_autor: string;
  comentarios_internos: string;
  criterios: CriterioAvaliacao[];
  editavel: boolean;
  submissao: {
    id: string;
    titulo: string;
    resumo: string;
    palavras_chave: string[];
    area_tematica: string;
    tem_arquivo: boolean;
    evento_titulo: string;
    chamada_titulo: string;
    anonimo: boolean;
    autoria: string | null;
  };
}

export interface CandidatoParecer {
  id: string;
  nome: string;
  email: string;
  papel: string;
  pendentes: number;
}

export interface EmissaoCertificadosCientificos {
  autores: number;
  pareceristas: number;
  emails_enviados: number;
}

export type Licenca = "cc-by" | "cc-by-sa" | "cc-by-nc" | "cc-by-nc-nd" | "reservados";

export const LICENCAS: { value: Licenca; label: string }[] = [
  { value: "cc-by", label: "CC BY 4.0 (uso livre com atribuição)" },
  { value: "cc-by-sa", label: "CC BY-SA 4.0" },
  { value: "cc-by-nc", label: "CC BY-NC 4.0 (sem uso comercial)" },
  { value: "cc-by-nc-nd", label: "CC BY-NC-ND 4.0" },
  { value: "reservados", label: "Todos os direitos reservados" },
];

export interface AutorPublicado {
  nome: string;
  instituicao: string;
  orcid: string;
}

export interface TrabalhoPublicado {
  id: string;
  anais: string;
  submissao: string | null;
  slug: string;
  ordem: number;
  titulo: string;
  autores: AutorPublicado[];
  area_tematica: string;
  doi: string;
  tem_arquivo: boolean;
  url_publica: string;
  publicado_em: string;
}

export interface AnaisPublicacao {
  id: string;
  evento: string;
  titulo: string;
  issn?: string | null;
  isbn: string;
  url_publicacao?: string;
  licenca: Licenca;
  licenca_display: string;
  apresentacao: string;
  editores: string;
  cidade: string;
  publicado_em?: string;
  metadata?: {
    total_trabalhos: number;
    trabalhos: Array<{ id: string; titulo: string; autor: string }>;
  };
  trabalhos: TrabalhoPublicado[];
}

export interface PublicTrabalhoResumo {
  slug: string;
  ordem: number;
  titulo: string;
  autores: AutorPublicado[];
  area_tematica: string;
  palavras_chave: string[];
  doi: string;
}

interface EventoRef {
  titulo: string;
  slug: string;
  data_inicio: string;
  local: string | null;
}

export interface PublicAnais {
  titulo: string;
  issn: string | null;
  isbn: string;
  licenca: Licenca;
  licenca_display: string;
  licenca_url: string | null;
  apresentacao: string;
  editores: string;
  cidade: string;
  publicado_em: string;
  evento: EventoRef;
  trabalhos: PublicTrabalhoResumo[];
}

export interface PublicTrabalho extends PublicTrabalhoResumo {
  resumo: string;
  publicado_em: string;
  tem_arquivo_final: boolean;
  url: string;
  associacao: string;
  citacoes: { abnt: string; apa: string; bibtex: string };
  anais: {
    titulo: string;
    issn: string | null;
    isbn: string;
    licenca: Licenca;
    licenca_display: string;
    licenca_url: string | null;
    cidade: string;
  };
  evento: EventoRef;
}

export interface EventoAcademico {
  id: string;
  titulo: string;
  slug: string;
  descricao?: string;
  data_inicio: string;
  data_fim: string;
  local?: string;
  modalidade: string;
  status: EventoStatus;
  status_display: string;
  valor_inscricao?: string;
  capacidade_max?: number;
  mandato?: string;
  mandato_titulo?: string;
  tem_cfp?: boolean;
  submissoes_count?: number;
  inscricoes_count?: number;
  call_for_papers?: CallForPapers;
  anais?: AnaisPublicacao;
  certificado_habilitado?: boolean;
  carga_horaria?: number | null;
  publicado_site?: boolean;
  resumo?: string;
  capa_url?: string | null;
  item_loja?: ItemLojaEvento | null;
  created_at: string;
}

export interface ItemLojaEvento {
  id: string;
  slug: string;
  price: string;
  member_price: string | null;
  is_active: boolean;
}

export type TipoAtividade =
  | "abertura"
  | "palestra"
  | "mesa"
  | "sessao_trabalhos"
  | "minicurso"
  | "intervalo"
  | "outro";

export const TIPOS_ATIVIDADE: { value: TipoAtividade; label: string }[] = [
  { value: "abertura", label: "Abertura / encerramento" },
  { value: "palestra", label: "Palestra / conferência" },
  { value: "mesa", label: "Mesa-redonda" },
  { value: "sessao_trabalhos", label: "Sessão de trabalhos" },
  { value: "minicurso", label: "Minicurso / oficina" },
  { value: "intervalo", label: "Intervalo" },
  { value: "outro", label: "Outro" },
];

export interface AtividadeProgramacao {
  id: string;
  evento: string;
  titulo: string;
  tipo: TipoAtividade;
  tipo_display: string;
  inicio: string;
  fim: string;
  sala: string;
  responsaveis: string;
  descricao: string;
  link_transmissao: string;
}

export interface SituacaoInscricao {
  aberta: boolean;
  esgotada: boolean;
  vagas_restantes: number | null;
  price: string | null;
  member_price: string | null;
  catalog_item_slug: string | null;
}

export interface PublicEvento {
  id: string;
  titulo: string;
  slug: string;
  resumo: string;
  data_inicio: string;
  data_fim: string;
  local: string | null;
  modalidade: string;
  modalidade_display: string;
  status: EventoStatus;
  capa_url: string | null;
  inscricao: SituacaoInscricao;
  descricao?: string | null;
  carga_horaria?: number | null;
  certificado_habilitado?: boolean;
  programacao?: Omit<AtividadeProgramacao, "evento">[];
  chamada?: {
    titulo: string;
    instrucoes: string;
    data_abertura: string;
    data_fechamento: string;
    areas_tematicas: string[];
    max_submissoes_por_autor: number;
    anonimo: boolean;
    aberta: boolean;
  } | null;
  anais?: { titulo: string; issn: string | null; url_publicacao: string | null; total_trabalhos: number } | null;
}

export interface InscricaoEvento {
  id: string;
  evento: string;
  membro: string | null;
  nome: string;
  email: string;
  confirmada: boolean;
  pago_em: string | null;
  presente: boolean;
  certificado_codigo: string | null;
  certificado_emitido_em: string | null;
  created_at: string;
}

export interface EmissaoCertificados {
  emitidos: number;
  emails_enviados: number;
  inscritos_sem_presenca: number;
}

export interface ResumoEventos {
  total: number;
  cfp_abertos: number;
  em_avaliacao: number;
  submissoes_pendentes: number;
  pareceres_pendentes: number;
}

export const STATUS_EVENTO: Record<EventoStatus, string> = {
  rascunho: "Rascunho",
  inscricoes_abertas: "Inscrições Abertas",
  cfp_aberto: "CFP Aberto",
  em_avaliacao: "Em Avaliação",
  encerrado: "Encerrado",
  anais_publicados: "Anais Publicados",
  cancelado: "Cancelado",
};
