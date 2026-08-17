import { useEffect, useState } from "react";
import { ExternalLink, Globe, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  createSitePage,
  deleteSitePage,
  getWebsiteConfig,
  listSitePages,
  updateSitePage,
  updateWebsiteConfig,
} from "@/services/website";
import type { AssocieSeCategory, SitePage, WebsiteConfig } from "@/types/website";
import { buildAssocieSeCtaLink, buildTenantSiteQuery } from "@/utils/tenantSite";

type Tab = "geral" | "hero" | "associe" | "contato" | "paginas";

const emptyPage = (): Partial<SitePage> => ({
  title: "",
  slug: "",
  summary: "",
  content: "",
  page_type: "noticia",
  is_published: false,
  is_featured: false,
});

export default function WebsiteAdmin() {
  const { tenantSchema } = useAuth();
  const schema = tenantSchema || "demo";
  const siteUrl = `/site${buildTenantSiteQuery(schema)}`;
  const lojaPreview = buildAssocieSeCtaLink(schema, "auto:loja");

  const [tab, setTab] = useState<Tab>("geral");
  const [config, setConfig] = useState<WebsiteConfig | null>(null);
  const [pages, setPages] = useState<SitePage[]>([]);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  const [pageForm, setPageForm] = useState<Partial<SitePage> | null>(null);

  const load = async () => {
    setLoading(true);
    setErro("");
    try {
      const [cfg, pgs] = await Promise.all([getWebsiteConfig(), listSitePages()]);
      setConfig(cfg);
      setPages(pgs);
    } catch {
      setErro("Erro ao carregar CMS do website.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const saveConfig = async (patch: Partial<WebsiteConfig>) => {
    if (!config) return;
    setSalvando(true);
    setMsg("");
    try {
      const updated = await updateWebsiteConfig({ ...config, ...patch });
      setConfig(updated);
      setMsg("Configuração salva.");
    } catch {
      setErro("Falha ao salvar configuração.");
    } finally {
      setSalvando(false);
    }
  };

  const handleConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    await saveConfig(config);
  };

  const updateCategory = (index: number, field: keyof AssocieSeCategory, value: string) => {
    if (!config) return;
    const cats = [...(config.associe_se_categories ?? [])];
    cats[index] = { ...cats[index], [field]: value };
    setConfig({ ...config, associe_se_categories: cats });
  };

  const addCategory = () => {
    if (!config) return;
    setConfig({
      ...config,
      associe_se_categories: [...(config.associe_se_categories ?? []), { label: "", hint: "" }],
    });
  };

  const removeCategory = (index: number) => {
    if (!config) return;
    const cats = [...(config.associe_se_categories ?? [])];
    cats.splice(index, 1);
    setConfig({ ...config, associe_se_categories: cats });
  };

  const savePage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pageForm?.title) return;
    setSalvando(true);
    setMsg("");
    try {
      if (pageForm.id) {
        await updateSitePage(pageForm.slug!, pageForm);
      } else {
        await createSitePage(pageForm);
      }
      setPageForm(null);
      await load();
      setMsg("Página salva.");
    } catch {
      setErro("Falha ao salvar página.");
    } finally {
      setSalvando(false);
    }
  };

  const handleDeletePage = async (slug: string) => {
    if (!confirm("Excluir esta página?")) return;
    await deleteSitePage(slug);
    await load();
  };

  if (loading && !config) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando website…</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="dashboard-page">
        <p className="dashboard-error">{erro || "Configuração indisponível."}</p>
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "geral", label: "Identidade" },
    { id: "hero", label: "Hero" },
    { id: "associe", label: "Associe-se" },
    { id: "contato", label: "Contato" },
    { id: "paginas", label: "Páginas / Notícias" },
  ];

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">
            <Globe size={22} style={{ verticalAlign: "middle", marginRight: 8 }} />
            Website da associação
          </h1>
          <p className="dashboard-subtitle">
            Site público editável — eventos, publicações e certificados ficam para módulos futuros
          </p>
        </div>
        <div className="dashboard-header-actions">
          <a
            href={siteUrl}
            target="_blank"
            rel="noreferrer"
            className="dashboard-btn-secondary"
            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          >
            <ExternalLink size={16} />
            Ver site
          </a>
        </div>
      </div>

      {msg && <p className="dashboard-success">{msg}</p>}
      {erro && <p className="dashboard-error">{erro}</p>}

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "dashboard-btn-primary" : "dashboard-btn-secondary"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {(tab === "geral" || tab === "hero" || tab === "associe" || tab === "contato") && (
        <form className="page-form" onSubmit={handleConfigSubmit}>
          {tab === "geral" && (
            <>
              <div className="form-group">
                <label className="form-label">Título do site</label>
                <input
                  className="form-input"
                  value={config.site_title}
                  onChange={(e) => setConfig({ ...config, site_title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tagline</label>
                <input
                  className="form-input"
                  value={config.site_tagline}
                  onChange={(e) => setConfig({ ...config, site_tagline: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Cor primária</label>
                  <input
                    className="form-input"
                    type="color"
                    value={config.primary_color}
                    onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Cor secundária</label>
                  <input
                    className="form-input"
                    type="color"
                    value={config.secondary_color}
                    onChange={(e) => setConfig({ ...config, secondary_color: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">
                  <input
                    type="checkbox"
                    checked={config.is_published}
                    onChange={(e) => setConfig({ ...config, is_published: e.target.checked })}
                  />{" "}
                  Site publicado (visível em /site?schema={schema})
                </label>
              </div>
            </>
          )}

          {tab === "hero" && (
            <>
              <div className="form-group">
                <label className="form-label">Título hero</label>
                <input
                  className="form-input"
                  value={config.hero_title}
                  onChange={(e) => setConfig({ ...config, hero_title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Subtítulo</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={config.hero_subtitle}
                  onChange={(e) => setConfig({ ...config, hero_subtitle: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">CTA — rótulo</label>
                  <input
                    className="form-input"
                    value={config.hero_cta_label}
                    onChange={(e) => setConfig({ ...config, hero_cta_label: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">CTA — link</label>
                  <input
                    className="form-input"
                    value={config.hero_cta_link}
                    onChange={(e) => setConfig({ ...config, hero_cta_link: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Sobre — título</label>
                <input
                  className="form-input"
                  value={config.about_title}
                  onChange={(e) => setConfig({ ...config, about_title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Sobre — texto</label>
                <textarea
                  className="form-textarea"
                  rows={6}
                  value={config.about_text}
                  onChange={(e) => setConfig({ ...config, about_text: e.target.value })}
                />
              </div>
            </>
          )}

          {tab === "associe" && (
            <>
              <div className="form-group">
                <label className="form-label">Título do box</label>
                <input
                  className="form-input"
                  value={config.associe_se_title}
                  onChange={(e) => setConfig({ ...config, associe_se_title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Texto introdutório</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  value={config.associe_se_lead}
                  onChange={(e) => setConfig({ ...config, associe_se_lead: e.target.value })}
                />
              </div>
              <p className="form-hint" style={{ marginBottom: "0.75rem" }}>
                Categorias de filiação (referência UX do box Associe-se — integração com loja futura)
              </p>
              {(config.associe_se_categories ?? []).map((cat, i) => (
                <div key={i} className="form-row" style={{ alignItems: "flex-end" }}>
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label">Categoria</label>
                    <input
                      className="form-input"
                      value={cat.label}
                      onChange={(e) => updateCategory(i, "label", e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label">Dica</label>
                    <input
                      className="form-input"
                      value={cat.hint ?? ""}
                      onChange={(e) => updateCategory(i, "hint", e.target.value)}
                    />
                  </div>
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    onClick={() => removeCategory(i)}
                    aria-label="Remover"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              <button type="button" className="dashboard-btn-secondary" onClick={addCategory}>
                + Categoria
              </button>
              <div className="form-row" style={{ marginTop: "1rem" }}>
                <div className="form-group">
                  <label className="form-label">Botão — rótulo</label>
                  <input
                    className="form-input"
                    value={config.associe_se_cta_label}
                    onChange={(e) => setConfig({ ...config, associe_se_cta_label: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Botão — link</label>
                  <input
                    className="form-input"
                    value={config.associe_se_cta_link}
                    onChange={(e) => setConfig({ ...config, associe_se_cta_link: e.target.value })}
                    placeholder="auto:loja (padrão — login → /app/portal/loja)"
                  />
                  <p className="form-hint">
                    Padrão recomendado: <code>auto:loja</code> →{" "}
                    <a href={lojaPreview}>{lojaPreview}</a>
                  </p>
                </div>
              </div>
            </>
          )}

          {tab === "contato" && (
            <>
              <div className="form-group">
                <label className="form-label">E-mail</label>
                <input
                  className="form-input"
                  type="email"
                  value={config.contact_email}
                  onChange={(e) => setConfig({ ...config, contact_email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Telefone</label>
                <input
                  className="form-input"
                  value={config.contact_phone}
                  onChange={(e) => setConfig({ ...config, contact_phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Endereço</label>
                <input
                  className="form-input"
                  value={config.contact_address}
                  onChange={(e) => setConfig({ ...config, contact_address: e.target.value })}
                />
              </div>
            </>
          )}

          <div className="form-actions">
            <button type="submit" className="dashboard-btn-primary" disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar"}
            </button>
          </div>
        </form>
      )}

      {tab === "paginas" && (
        <div>
          <div style={{ marginBottom: "1rem" }}>
            <button
              type="button"
              className="dashboard-btn-primary"
              onClick={() => setPageForm(emptyPage())}
            >
              <Plus size={16} style={{ marginRight: 6 }} />
              Nova página
            </button>
          </div>

          {pageForm && (
            <form className="page-form" onSubmit={savePage} style={{ marginBottom: "1.5rem" }}>
              <div className="form-group">
                <label className="form-label">Título</label>
                <input
                  className="form-input"
                  required
                  value={pageForm.title}
                  onChange={(e) => setPageForm({ ...pageForm, title: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Slug (opcional)</label>
                  <input
                    className="form-input"
                    value={pageForm.slug ?? ""}
                    onChange={(e) => setPageForm({ ...pageForm, slug: e.target.value })}
                    placeholder="gerado automaticamente"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Tipo</label>
                  <select
                    className="form-select"
                    value={pageForm.page_type}
                    onChange={(e) =>
                      setPageForm({
                        ...pageForm,
                        page_type: e.target.value as SitePage["page_type"],
                      })
                    }
                  >
                    <option value="noticia">Notícia</option>
                    <option value="institucional">Institucional</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Resumo</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={pageForm.summary ?? ""}
                  onChange={(e) => setPageForm({ ...pageForm, summary: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Conteúdo</label>
                <textarea
                  className="form-textarea"
                  rows={8}
                  value={pageForm.content ?? ""}
                  onChange={(e) => setPageForm({ ...pageForm, content: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <input
                    type="checkbox"
                    checked={pageForm.is_published ?? false}
                    onChange={(e) => setPageForm({ ...pageForm, is_published: e.target.checked })}
                  />{" "}
                  Publicada
                </label>
              </div>
              <div className="form-actions">
                <button type="submit" className="dashboard-btn-primary" disabled={salvando}>
                  Salvar página
                </button>
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  onClick={() => setPageForm(null)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Tipo</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {pages.length === 0 ? (
                  <tr>
                    <td colSpan={4}>Nenhuma página cadastrada.</td>
                  </tr>
                ) : (
                  pages.map((p) => (
                    <tr key={p.id}>
                      <td>{p.title}</td>
                      <td>{p.page_type_display}</td>
                      <td>{p.is_published ? "Publicada" : "Rascunho"}</td>
                      <td>
                        <button
                          type="button"
                          className="dashboard-btn-secondary"
                          onClick={() => setPageForm(p)}
                        >
                          Editar
                        </button>{" "}
                        <button
                          type="button"
                          className="dashboard-btn-secondary"
                          onClick={() => handleDeletePage(p.slug)}
                        >
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
