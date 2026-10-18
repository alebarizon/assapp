import React, { useEffect, useState } from "react";
import RichTextEditor from "./RichTextEditor";
import { listCatalogItems } from "@/services/ecommerce";
import { apiErrorMessage, createCourse, createCourseCatalogItem, updateCourse } from "@/services/courses";
import type { CatalogItem } from "@/types/ecommerce";
import type { Course, CourseLevel, CourseVisibility, ProgressionMode } from "@/types/courses";
import { COURSE_LEVELS } from "@/types/courses";
import { formatCatalogPrice } from "@/utils/tenantSite";

interface CourseSettingsFormProps {
  course: Course | null;
  onSaved: (course: Course) => void;
}

export default function CourseSettingsForm({ course, onSaved }: CourseSettingsFormProps) {
  const [form, setForm] = useState({
    title: course?.title || "",
    slug: course?.slug || "",
    short_description: course?.short_description || "",
    description: course?.description || "",
    instructor_name: course?.instructor_name || "",
    workload_hours: course?.workload_hours ? String(course.workload_hours) : "",
    level: (course?.level || "beginner") as CourseLevel,
    progression_mode: (course?.progression_mode || "sequential") as ProgressionMode,
    visibility: (course?.visibility || "public") as CourseVisibility,
    certificate_enabled: course?.certificate_enabled ?? true,
    catalog_item: course?.catalog_item || "",
  });
  const [cover, setCover] = useState<File | null>(null);
  const [removeCover, setRemoveCover] = useState(false);
  const [catalogItems, setCatalogItems] = useState<CatalogItem[]>([]);
  const [price, setPrice] = useState("");
  const [memberPrice, setMemberPrice] = useState("");
  const [saving, setSaving] = useState(false);
  const [creatingItem, setCreatingItem] = useState(false);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!course) return;
    listCatalogItems({ item_type: "curso" })
      .then(setCatalogItems)
      .catch(() => setCatalogItems([]));
  }, [course]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setMsg("");
    setSaving(true);
    const data = new FormData();
    data.append("title", form.title);
    if (course) data.append("slug", form.slug);
    data.append("short_description", form.short_description);
    data.append("description", form.description);
    data.append("instructor_name", form.instructor_name);
    data.append("workload_hours", form.workload_hours);
    data.append("level", form.level);
    data.append("progression_mode", form.progression_mode);
    data.append("visibility", form.visibility);
    data.append("certificate_enabled", String(form.certificate_enabled));
    if (course) data.append("catalog_item", form.catalog_item);
    if (cover) data.append("cover_image", cover);
    if (removeCover) data.append("remove_cover_image", "true");
    try {
      const saved = course ? await updateCourse(course.id, data) : await createCourse(data);
      setCover(null);
      setRemoveCover(false);
      setMsg("Configurações salvas.");
      onSaved(saved);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao salvar o curso."));
    } finally {
      setSaving(false);
    }
  };

  const handleCreateItem = async () => {
    if (!course) return;
    setErro("");
    setCreatingItem(true);
    try {
      const saved = await createCourseCatalogItem(course.id, price || "0", memberPrice);
      setForm((prev) => ({ ...prev, catalog_item: saved.catalog_item || "" }));
      setMsg("Item criado na loja e vinculado ao curso.");
      onSaved(saved);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao criar o item na loja."));
    } finally {
      setCreatingItem(false);
    }
  };

  return (
    <div className="page-form-container">
      <form className="page-form" onSubmit={handleSubmit}>
        {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
        {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Título *</label>
            <input
              className="form-input"
              required
              maxLength={200}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>
          {course && (
            <div className="form-group">
              <label className="form-label">Endereço (slug)</label>
              <input
                className="form-input"
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
              />
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Resumo</label>
          <input
            className="form-input"
            maxLength={300}
            value={form.short_description}
            onChange={(e) => setForm({ ...form, short_description: e.target.value })}
            placeholder="Uma frase que aparece nos cards do catálogo"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Descrição</label>
          <RichTextEditor
            value={form.description}
            onChange={(html) => setForm((prev) => ({ ...prev, description: html }))}
            onUploadError={setErro}
          />
        </div>

        <div className="form-row-3">
          <div className="form-group">
            <label className="form-label">Instrutor(a)</label>
            <input
              className="form-input"
              value={form.instructor_name}
              onChange={(e) => setForm({ ...form, instructor_name: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Carga horária (h)</label>
            <input
              className="form-input"
              type="number"
              min="0"
              value={form.workload_hours}
              onChange={(e) => setForm({ ...form, workload_hours: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Nível</label>
            <select
              className="form-select"
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value as CourseLevel })}
            >
              {COURSE_LEVELS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Progressão</label>
            <select
              className="form-select"
              value={form.progression_mode}
              onChange={(e) => setForm({ ...form, progression_mode: e.target.value as ProgressionMode })}
            >
              <option value="sequential">Sequencial (libera aula a aula)</option>
              <option value="free">Livre</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Visibilidade no site</label>
            <select
              className="form-select"
              value={form.visibility}
              onChange={(e) => setForm({ ...form, visibility: e.target.value as CourseVisibility })}
            >
              <option value="public">Público (aparece no catálogo)</option>
              <option value="unlisted">Não listado (somente com o link)</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Capa</label>
          {course?.cover_image_url && !removeCover && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
              <img src={course.cover_image_url} alt="" style={{ width: 160, borderRadius: 8 }} />
              <button type="button" className="dashboard-btn-cancel" onClick={() => setRemoveCover(true)}>
                Remover capa
              </button>
            </div>
          )}
          <input type="file" accept="image/*" onChange={(e) => setCover(e.target.files?.[0] || null)} />
        </div>

        <label className="inline-check">
          <input
            type="checkbox"
            checked={form.certificate_enabled}
            onChange={(e) => setForm({ ...form, certificate_enabled: e.target.checked })}
          />
          <span>Emitir certificado ao concluir</span>
        </label>

        {course && (
          <div className="form-group" style={{ marginTop: "1.25rem" }}>
            <label className="form-label">Venda na loja</label>
            <p className="course-muted" style={{ marginTop: 0 }}>
              O associado é matriculado automaticamente quando o pedido deste item é pago. Use preço zero
              para cursos gratuitos.
            </p>
            <select
              className="form-select"
              value={form.catalog_item}
              onChange={(e) => setForm({ ...form, catalog_item: e.target.value })}
            >
              <option value="">Sem item vinculado</option>
              {catalogItems.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} — {formatCatalogPrice(item)}
                  {!item.is_active ? " (inativo)" : ""}
                </option>
              ))}
            </select>
            {!course.catalog_item && (
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Preço (R$)"
                  style={{ maxWidth: 160 }}
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                />
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Sócio em dia (R$)"
                  title="Opcional: preço para sócio com a anuidade em dia"
                  style={{ maxWidth: 180 }}
                  value={memberPrice}
                  onChange={(e) => setMemberPrice(e.target.value)}
                />
                <button
                  type="button"
                  className="dashboard-btn-secondary"
                  disabled={creatingItem}
                  onClick={handleCreateItem}
                >
                  {creatingItem ? "Criando..." : "Criar item na loja"}
                </button>
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button type="submit" className="dashboard-btn-save" disabled={saving}>
            {saving ? "Salvando..." : course ? "Salvar" : "Criar curso"}
          </button>
        </div>
      </form>
    </div>
  );
}
