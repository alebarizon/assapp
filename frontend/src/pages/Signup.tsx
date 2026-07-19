import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BookMarked } from "lucide-react";
import { listPlans, register } from "@/services/auth";
import { setAuthToken, setTenantSchema } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import type { SaasPlan } from "@/types";
import "./Login.css";

function slugifyName(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 32);
}

export default function Signup() {
  const navigate = useNavigate();
  const { setUser, setSetupCompleted, refreshTenantStatus } = useAuth();
  const [plans, setPlans] = useState<SaasPlan[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [slugTouched, setSlugTouched] = useState(false);

  const [form, setForm] = useState({
    association_name: "",
    tenant_slug: "",
    cnpj: "",
    city: "",
    state: "",
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    plan_slug: "starter",
  });

  useEffect(() => {
    listPlans()
      .then((p) => {
        setPlans(p);
        if (p[0]) setForm((f) => ({ ...f, plan_slug: p[0].slug }));
      })
      .catch(() => setPlans([]));
  }, []);

  const suggestedSlug = useMemo(
    () => slugifyName(form.association_name),
    [form.association_name]
  );

  useEffect(() => {
    if (!slugTouched && suggestedSlug) {
      setForm((f) => ({ ...f, tenant_slug: suggestedSlug }));
    }
  }, [suggestedSlug, slugTouched]);

  const update = (field: string, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await register({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
        association_name: form.association_name,
        tenant_slug: form.tenant_slug,
        plan_slug: form.plan_slug,
        cnpj: form.cnpj || undefined,
        phone: form.phone || undefined,
        city: form.city || undefined,
        state: form.state || undefined,
      });
      setAuthToken(data.access);
      setTenantSchema(data.tenant_schema);
      setUser(data.user);
      setSetupCompleted(data.setup_completed ?? false);
      await refreshTenantStatus();
      navigate("/app/setup");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Não foi possível concluir o cadastro.";
      setError(typeof detail === "string" ? detail : "Erro no cadastro.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <aside className="login-hero">
        <div className="login-hero-fallback" aria-hidden />
        <div className="login-hero-overlay" />
        <div className="login-hero-content">
          <div className="login-hero-brand">
            <div className="login-hero-brand-icon">
              <BookMarked className="login-hero-brand-leaf" />
            </div>
            <span className="login-hero-brand-name">AssApp</span>
          </div>
          <div className="login-hero-text">
            <p className="login-hero-tagline">Assinatura simulada</p>
            <h1 className="login-hero-title">
              Cadastre sua{"\n"}associação científica
            </h1>
            <p className="login-hero-description">
              Crie o tenant, escolha o plano e configure o primeiro mandato no
              setup guiado.
            </p>
          </div>
        </div>
      </aside>

      <div className="login-form-panel">
        <div className="login-form-content" style={{ maxWidth: "28rem" }}>
          <div className="login-mobile-brand">
            <div className="login-mobile-brand-icon">
              <BookMarked className="login-mobile-brand-leaf" />
            </div>
            <span className="login-mobile-brand-name">AssApp</span>
          </div>

          <h2 className="login-form-title">Criar conta</h2>
          <p className="login-form-subtitle">
            Pagamento simulado — Stripe virá em ciclo posterior.
          </p>

          {error && <div className="login-error-message">{error}</div>}

          <form className="login-form signup-form-grid" onSubmit={handleSubmit}>
            <fieldset className="signup-fieldset">
              <legend>Associação</legend>
              <input
                className="login-input"
                style={{ paddingLeft: "1rem" }}
                placeholder="Nome da associação"
                value={form.association_name}
                onChange={(e) => update("association_name", e.target.value)}
                required
              />
              <div>
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem", fontFamily: "ui-monospace, monospace" }}
                  placeholder="Slug"
                  value={form.tenant_slug}
                  onChange={(e) => {
                    setSlugTouched(true);
                    update("tenant_slug", e.target.value.toLowerCase());
                  }}
                  required
                  pattern="[a-z][a-z0-9-]{2,31}"
                />
                <p className="login-hint" style={{ textAlign: "left", marginTop: "0.35rem" }}>
                  Schema: {form.tenant_slug || "…"}.localhost
                </p>
              </div>
              <div className="form-row-2">
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="CNPJ (opcional)"
                  value={form.cnpj}
                  onChange={(e) => update("cnpj", e.target.value)}
                />
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="Telefone"
                  value={form.phone}
                  onChange={(e) => update("phone", e.target.value)}
                />
              </div>
              <div className="form-row-3">
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="Cidade"
                  value={form.city}
                  onChange={(e) => update("city", e.target.value)}
                />
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="UF"
                  maxLength={2}
                  value={form.state}
                  onChange={(e) => update("state", e.target.value.toUpperCase())}
                />
              </div>
            </fieldset>

            <fieldset className="signup-fieldset">
              <legend>Administrador</legend>
              <div className="form-row-2">
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="Nome"
                  value={form.first_name}
                  onChange={(e) => update("first_name", e.target.value)}
                  required
                />
                <input
                  className="login-input"
                  style={{ paddingLeft: "1rem" }}
                  placeholder="Sobrenome"
                  value={form.last_name}
                  onChange={(e) => update("last_name", e.target.value)}
                />
              </div>
              <input
                type="email"
                className="login-input"
                style={{ paddingLeft: "1rem" }}
                placeholder="E-mail"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
              />
              <input
                type="password"
                className="login-input"
                style={{ paddingLeft: "1rem" }}
                placeholder="Senha (mín. 8)"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                required
                minLength={8}
              />
            </fieldset>

            <fieldset className="signup-fieldset">
              <legend>Plano</legend>
              {plans.map((plan) => (
                <label
                  key={plan.slug}
                  className={`signup-plan-card${form.plan_slug === plan.slug ? " selected" : ""}`}
                >
                  <input
                    type="radio"
                    name="plan"
                    checked={form.plan_slug === plan.slug}
                    onChange={() => update("plan_slug", plan.slug)}
                  />
                  <span>
                    <span className="signup-plan-name">{plan.name}</span>
                    <span className="signup-plan-desc">{plan.description}</span>
                  </span>
                </label>
              ))}
            </fieldset>

            <button type="submit" className="login-submit-button" disabled={loading}>
              {loading ? "Criando associação..." : "Criar conta e continuar"}
            </button>
          </form>

          <p className="login-signup-prompt">
            Já tem conta?{" "}
            <Link to="/login" className="login-signup-link">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
