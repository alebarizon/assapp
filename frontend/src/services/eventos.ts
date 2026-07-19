import type {
  AnaisPublicacao,
  CallForPapers,
  EventoAcademico,
  Parecer,
  ResumoEventos,
  SubmissaoTrabalho,
} from "@/types/eventos";
import { api } from "./api";

function unwrapList<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getResumoEventos(): Promise<ResumoEventos> {
  const { data } = await api.get<ResumoEventos>("/api/eventos/eventos/resumo/");
  return data;
}

export async function listEventos(): Promise<EventoAcademico[]> {
  const { data } = await api.get("/api/eventos/eventos/");
  return unwrapList(data);
}

export async function getEvento(id: string): Promise<EventoAcademico> {
  const { data } = await api.get<EventoAcademico>(`/api/eventos/eventos/${id}/`);
  return data;
}

export async function createEvento(payload: Partial<EventoAcademico>): Promise<EventoAcademico> {
  const { data } = await api.post<EventoAcademico>("/api/eventos/eventos/", payload);
  return data;
}

export async function abrirCfp(
  eventoId: string,
  payload: {
    titulo: string;
    instrucoes: string;
    data_abertura: string;
    data_fechamento: string;
    areas_tematicas?: string[];
  }
): Promise<CallForPapers> {
  const { data } = await api.post<CallForPapers>(
    `/api/eventos/eventos/${eventoId}/abrir_cfp/`,
    payload
  );
  return data;
}

export async function listSubmissoesEvento(eventoId: string): Promise<SubmissaoTrabalho[]> {
  const { data } = await api.get<SubmissaoTrabalho[]>(
    `/api/eventos/eventos/${eventoId}/submissoes/`
  );
  return data;
}

export async function createSubmissao(payload: {
  cfp: string;
  titulo: string;
  resumo: string;
  area_tematica?: string;
  palavras_chave?: string[];
  membro_id?: string;
}): Promise<SubmissaoTrabalho> {
  const { data } = await api.post<SubmissaoTrabalho>("/api/eventos/submissoes/", payload);
  return data;
}

export async function submeterTrabalho(id: string): Promise<SubmissaoTrabalho> {
  const { data } = await api.post<SubmissaoTrabalho>(
    `/api/eventos/submissoes/${id}/submeter/`,
    {}
  );
  return data;
}

export async function atribuirParecerista(
  submissaoId: string,
  pareceristaId: string
): Promise<Parecer> {
  const { data } = await api.post<Parecer>(
    `/api/eventos/submissoes/${submissaoId}/atribuir_parecerista/`,
    { parecerista_id: pareceristaId }
  );
  return data;
}

export async function concluirParecer(
  parecerId: string,
  payload: {
    recomendacao: "aceitar" | "aceitar_com_revisoes" | "rejeitar";
    nota?: number;
    comentarios_autor?: string;
  }
): Promise<Parecer> {
  const { data } = await api.post<Parecer>(
    `/api/eventos/pareceres/${parecerId}/concluir/`,
    payload
  );
  return data;
}

export async function gerarAnais(
  eventoId: string,
  titulo?: string
): Promise<AnaisPublicacao> {
  const { data } = await api.post<AnaisPublicacao>(
    `/api/eventos/eventos/${eventoId}/gerar_anais/`,
    { titulo }
  );
  return data;
}
