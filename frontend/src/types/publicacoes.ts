export type TipoPublicacao = "dossie" | "ebook" | "boletim" | "livro" | "relatorio" | "outro";
export type AcessoPublicacao = "publico" | "associados" | "venda";
export type MotivoAcesso =
  | "publico"
  | "equipe"
  | "adimplente"
  | "comprado"
  | "requer_adimplencia"
  | "requer_compra";

export interface AutorPublicacao {
  nome: string;
  instituicao?: string;
  orcid?: string;
}

export interface PublicacaoBase {
  id: string;
  tipo: TipoPublicacao;
  tipo_display: string;
  titulo: string;
  slug: string;
  subtitulo: string;
  resumo: string;
  autores: AutorPublicacao[];
  palavras_chave: string[];
  ano: number | null;
  edicao: string;
  isbn: string;
  issn: string;
  acesso: AcessoPublicacao;
  acesso_display: string;
  capa_url: string | null;
  tem_arquivo: boolean;
  publicado_em: string | null;
  preco: string | null;
  preco_socio: string | null;
}

export interface Publicacao extends PublicacaoBase {
  arquivo_nome: string;
  publicada: boolean;
  downloads: number;
  catalog_item: string | null;
  vendas: number;
  created_at: string;
  updated_at: string;
}

export interface MinhaPublicacao extends PublicacaoBase {
  liberado: boolean;
  motivo: MotivoAcesso;
  motivo_display: string;
  catalog_item: string | null;
  preco_final: string | null;
}

export const TIPOS_PUBLICACAO: { value: TipoPublicacao; label: string }[] = [
  { value: "dossie", label: "Dossiê" },
  { value: "ebook", label: "E-book" },
  { value: "boletim", label: "Boletim" },
  { value: "livro", label: "Livro" },
  { value: "relatorio", label: "Relatório técnico" },
  { value: "outro", label: "Outro" },
];

export const ACESSOS_PUBLICACAO: { value: AcessoPublicacao; label: string; ajuda: string }[] = [
  { value: "publico", label: "Aberto a todos", ajuda: "Qualquer visitante do site baixa o arquivo." },
  {
    value: "associados",
    label: "Associados em dia",
    ajuda: "Liberado no portal para quem está com a anuidade em dia. Com preço, os demais podem comprar.",
  },
  { value: "venda", label: "Venda na loja", ajuda: "Só quem comprar tem acesso; o sócio pode ter preço menor." },
];
