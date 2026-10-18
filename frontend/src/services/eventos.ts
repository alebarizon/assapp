import type {
  AtividadeProgramacao,
  AnaisPublicacao,
  CallForPapers,
  CandidatoParecer,
  ChamadaAberta,
  Coautor,
  CriterioAvaliacao,
  EmissaoCertificados,
  EmissaoCertificadosCientificos,
  MeuParecer,
  MinhaSubmissao,
  PublicAnais,
  PublicTrabalho,
  TrabalhoPublicado,
  Recomendacao,
  EventoAcademico,
  InscricaoEvento,
  Parecer,
  PublicEvento,
  ResumoEventos,
  SubmissaoTrabalho,
} from "@/types/eventos";
import { downloadBlob } from "@/utils/download";
import { api } from "./api";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

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

export async function salvarItemLojaEvento(
  id: string,
  payload: { price: string; member_price: string | null; is_active: boolean }
): Promise<EventoAcademico> {
  const { data } = await api.post<EventoAcademico>(`/api/eventos/eventos/${id}/item-loja/`, payload);
  return data;
}

export async function enviarCapaEvento(id: string, arquivo: File): Promise<EventoAcademico> {
  const form = new FormData();
  form.append("capa", arquivo);
  const { data } = await api.post<EventoAcademico>(`/api/eventos/eventos/${id}/capa/`, form, MULTIPART);
  return data;
}

export async function removerCapaEvento(id: string): Promise<EventoAcademico> {
  const { data } = await api.delete<EventoAcademico>(`/api/eventos/eventos/${id}/capa/`);
  return data;
}

export async function listProgramacao(eventoId: string): Promise<AtividadeProgramacao[]> {
  const { data } = await api.get("/api/eventos/programacao/", { params: { evento: eventoId } });
  return unwrapList(data);
}

export async function salvarAtividade(
  payload: Omit<AtividadeProgramacao, "id" | "tipo_display"> & { id?: string }
): Promise<AtividadeProgramacao> {
  const { id, ...dados } = payload;
  const { data } = id
    ? await api.patch<AtividadeProgramacao>(`/api/eventos/programacao/${id}/`, dados)
    : await api.post<AtividadeProgramacao>("/api/eventos/programacao/", dados);
  return data;
}

export async function deleteAtividade(id: string): Promise<void> {
  await api.delete(`/api/eventos/programacao/${id}/`);
}

export async function listPublicEventos(schema: string): Promise<PublicEvento[]> {
  const { data } = await api.get("/api/eventos/public/", { params: { schema } });
  return unwrapList(data);
}

export async function getPublicEvento(schema: string, slug: string): Promise<PublicEvento> {
  const { data } = await api.get<PublicEvento>(`/api/eventos/public/${slug}/`, { params: { schema } });
  return data;
}

export async function getPublicAnais(schema: string, slug: string): Promise<PublicAnais> {
  const { data } = await api.get<PublicAnais>(`/api/eventos/public/${slug}/anais/`, { params: { schema } });
  return data;
}

export async function getPublicTrabalho(schema: string, slug: string, trabalho: string): Promise<PublicTrabalho> {
  const { data } = await api.get<PublicTrabalho>(`/api/eventos/public/${slug}/anais/${trabalho}/`, {
    params: { schema },
  });
  return data;
}

export function publicTrabalhoPdfUrl(schema: string, slug: string, trabalho: string): string {
  const base = import.meta.env.VITE_API_URL ?? "";
  return `${base}/api/eventos/public/${slug}/anais/${trabalho}/pdf/?schema=${encodeURIComponent(schema)}`;
}

export async function editarAnais(eventoId: string, payload: Partial<AnaisPublicacao>): Promise<AnaisPublicacao> {
  const { data } = await api.patch<AnaisPublicacao>(`/api/eventos/eventos/${eventoId}/anais/`, payload);
  return data;
}

export async function atualizarTrabalhoPublicado(
  id: string,
  payload: { doi?: string; ordem?: number; arquivo?: File }
): Promise<TrabalhoPublicado> {
  const form = new FormData();
  if (payload.doi !== undefined) form.append("doi", payload.doi);
  if (payload.ordem !== undefined) form.append("ordem", String(payload.ordem));
  if (payload.arquivo) form.append("arquivo", payload.arquivo);
  const { data } = await api.patch<TrabalhoPublicado>(`/api/eventos/trabalhos-publicados/${id}/`, form, MULTIPART);
  return data;
}

export async function removerArquivoTrabalhoPublicado(id: string): Promise<TrabalhoPublicado> {
  const { data } = await api.post<TrabalhoPublicado>(`/api/eventos/trabalhos-publicados/${id}/remover-arquivo/`, {});
  return data;
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
    max_submissoes_por_autor?: number;
    anonimo?: boolean;
    criterios?: CriterioAvaliacao[];
    nota_corte?: string | null;
    exige_arquivo?: boolean;
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
  pareceristaId: string,
  prazo?: string | null
): Promise<Parecer> {
  const { data } = await api.post<Parecer>(
    `/api/eventos/submissoes/${submissaoId}/atribuir_parecerista/`,
    { parecerista_id: pareceristaId, prazo: prazo || null }
  );
  return data;
}

export async function removerParecer(parecerId: string): Promise<void> {
  await api.delete(`/api/eventos/pareceres/${parecerId}/`);
}

export async function listCandidatosParecer(): Promise<CandidatoParecer[]> {
  const { data } = await api.get<CandidatoParecer[]>("/api/eventos/eventos/pareceristas/");
  return data;
}

export async function decidirSubmissao(
  submissaoId: string,
  payload: { decisao: Recomendacao; comentario: string; notificar: boolean }
): Promise<SubmissaoTrabalho> {
  const { data } = await api.post<SubmissaoTrabalho>(`/api/eventos/submissoes/${submissaoId}/decidir/`, payload);
  return data;
}

export async function downloadArquivoSubmissao(submissaoId: string) {
  await downloadBlob(`/api/eventos/submissoes/${submissaoId}/arquivo/`, "");
}

export async function emitirCertificadosCientificos(
  eventoId: string,
  notificar: boolean
): Promise<EmissaoCertificadosCientificos> {
  const { data } = await api.post<EmissaoCertificadosCientificos>(
    `/api/eventos/eventos/${eventoId}/emitir-certificados-cientificos/`,
    { notificar }
  );
  return data;
}

// Autor (portal)

export async function listMinhasChamadas(): Promise<ChamadaAberta[]> {
  const { data } = await api.get<ChamadaAberta[]>("/api/eventos/my/chamadas/");
  return data;
}

export async function listMinhasSubmissoes(): Promise<MinhaSubmissao[]> {
  const { data } = await api.get("/api/eventos/my/submissoes/");
  return unwrapList(data);
}

export interface RascunhoTrabalho {
  cfp: string;
  titulo: string;
  resumo: string;
  area_tematica: string;
  palavras_chave: string[];
  coautores: Coautor[];
  arquivo?: File | null;
}

export async function salvarMinhaSubmissao(payload: RascunhoTrabalho, id?: string): Promise<MinhaSubmissao> {
  const form = new FormData();
  const { arquivo, palavras_chave, coautores, ...campos } = payload;
  Object.entries(campos).forEach(([k, v]) => form.append(k, v));
  form.append("palavras_chave", JSON.stringify(palavras_chave));
  form.append("coautores", JSON.stringify(coautores));
  if (arquivo) form.append("arquivo", arquivo);
  const { data } = id
    ? await api.patch<MinhaSubmissao>(`/api/eventos/my/submissoes/${id}/`, form, MULTIPART)
    : await api.post<MinhaSubmissao>("/api/eventos/my/submissoes/", form, MULTIPART);
  return data;
}

export async function excluirMinhaSubmissao(id: string): Promise<void> {
  await api.delete(`/api/eventos/my/submissoes/${id}/`);
}

export async function enviarMinhaSubmissao(id: string): Promise<MinhaSubmissao> {
  const { data } = await api.post<MinhaSubmissao>(`/api/eventos/my/submissoes/${id}/submeter/`, {});
  return data;
}

export async function downloadMeuArquivo(id: string) {
  await downloadBlob(`/api/eventos/my/submissoes/${id}/arquivo/`, "");
}

// Parecerista

export async function listMeusPareceres(): Promise<MeuParecer[]> {
  const { data } = await api.get("/api/eventos/my/pareceres/");
  return unwrapList(data);
}

export async function concluirMeuParecer(
  id: string,
  payload: {
    recomendacao: Recomendacao;
    notas: Record<string, number>;
    comentarios_autor: string;
    comentarios_internos: string;
  }
): Promise<MeuParecer> {
  const { data } = await api.post<MeuParecer>(`/api/eventos/my/pareceres/${id}/concluir/`, payload);
  return data;
}

export async function downloadArquivoParecer(id: string) {
  await downloadBlob(`/api/eventos/my/pareceres/${id}/arquivo/`, "");
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
