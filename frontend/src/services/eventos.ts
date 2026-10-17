import type {
  AnaisPublicacao,
  CallForPapers,
  EmissaoCertificados,
  EventoAcademico,
  InscricaoEvento,
  Parecer,
  ResumoEventos,
  SubmissaoTrabalho,
} from "@/types/eventos";
import { downloadBlob } from "@/utils/download";
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

export async function updateEvento(id: string, payload: Partial<EventoAcademico>): Promise<void> {
  await api.patch(`/api/eventos/eventos/${id}/`, payload);
}

export async function listInscricoes(eventoId: string): Promise<InscricaoEvento[]> {
  const { data } = await api.get("/api/eventos/inscricoes/", { params: { evento: eventoId } });
  return unwrapList(data);
}

export async function createInscricao(payload: {
  evento: string;
  membro?: string;
  nome?: string;
  email?: string;
  confirmada?: boolean;
}): Promise<InscricaoEvento> {
  const { data } = await api.post<InscricaoEvento>("/api/eventos/inscricoes/", payload);
  return data;
}

export async function deleteInscricao(id: string): Promise<void> {
  await api.delete(`/api/eventos/inscricoes/${id}/`);
}

export async function marcarPresencas(eventoId: string, inscricoes: string[], presente: boolean): Promise<void> {
  await api.post(`/api/eventos/eventos/${eventoId}/presencas/`, { inscricoes, presente });
}

export async function emitirCertificados(eventoId: string, notificar: boolean): Promise<EmissaoCertificados> {
  const { data } = await api.post<EmissaoCertificados>(`/api/eventos/eventos/${eventoId}/emitir-certificados/`, {
    notificar,
  });
  return data;
}

export async function downloadCertificadoInscricao(inscricao: InscricaoEvento) {
  await downloadBlob(`/api/eventos/inscricoes/${inscricao.id}/certificado/`, `certificado-${inscricao.certificado_codigo}.pdf`);
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
