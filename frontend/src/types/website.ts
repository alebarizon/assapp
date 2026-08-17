export interface AssocieSeCategory {
  label: string;
  hint?: string;
}

export interface WebsiteConfig {
  id: string;
  site_title: string;
  site_tagline: string;
  site_description: string;
  primary_color: string;
  secondary_color: string;
  logo_url: string;
  favicon_url: string;
  hero_title: string;
  hero_subtitle: string;
  hero_image_url: string;
  hero_cta_label: string;
  hero_cta_link: string;
  about_title: string;
  about_text: string;
  associe_se_title: string;
  associe_se_lead: string;
  associe_se_categories: AssocieSeCategory[];
  associe_se_cta_label: string;
  associe_se_cta_link: string;
  contact_email: string;
  contact_phone: string;
  contact_address: string;
  social_links: { label: string; url: string }[];
  is_published: boolean;
}

export interface SitePage {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  page_type: "noticia" | "institucional";
  page_type_display: string;
  is_published: boolean;
  is_featured: boolean;
  published_at?: string | null;
}

export interface PublicSitePayload {
  schema: string;
  tenant_name: string;
  config: WebsiteConfig;
  news: SitePage[];
  associe_se_items?: PublicCatalogItem[];
  diretoria?: {
    titulo?: string;
    data_inicio?: string;
    data_fim?: string;
    cargos?: Array<{
      cargo: string;
      cargo_display?: string;
      usuario_nome?: string;
    }>;
  } | null;
}

export interface PublicCatalogItem {
  id: string;
  name: string;
  slug: string;
  description?: string;
  item_type: string;
  item_type_display: string;
  price: string;
  currency: string;
  tipo_filiacao?: string;
  anuidade_ano?: number | null;
}
