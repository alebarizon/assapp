import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BookMarked, Lock, Mail } from "lucide-react";
import { login } from "@/services/auth";
import { setAuthToken, setTenantSchema } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { homePathForRole } from "@/utils/roles";
import "./Login.css";

export default function Login() {
  const [email, setEmail] = useState("diretoria@abciber.org.br");
  const [password, setPassword] = useState("abciber123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser, setSetupCompleted, refreshTenantStatus } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      setAuthToken(data.access);
      setTenantSchema(data.tenant_schema);
      setUser(data.user);
      const completed = data.setup_completed ?? true;
      setSetupCompleted(completed);
      await refreshTenantStatus();
      navigate(homePathForRole(data.user.role, completed));
    } catch {
      setError(
        "Credenciais inválidas. Demo: diretoria@abciber.org.br / abciber123 ou ana.silva@usp.br / associado123."
      );
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
            <p className="login-hero-tagline">PIPE FAPESP · Fase 1</p>
            <h1 className="login-hero-title">
              Memória institucional{"\n"}que atravessa mandatos
            </h1>
            <p className="login-hero-description">
              Onboarding de diretorias, contexto histórico e fluxos acadêmicos
              para associações científicas.
            </p>
          </div>
        </div>
      </aside>

      <div className="login-form-panel">
        <div className="login-form-content">
          <div className="login-mobile-brand">
            <div className="login-mobile-brand-icon">
              <BookMarked className="login-mobile-brand-leaf" />
            </div>
            <span className="login-mobile-brand-name">AssApp</span>
          </div>

          <h2 className="login-form-title">Entrar na plataforma</h2>
          <p className="login-form-subtitle">
            Acesse o painel da sua associação científica.
          </p>

          {error && <div className="login-error-message">{error}</div>}

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="login-field">
              <label className="login-label" htmlFor="email">
                E-mail
              </label>
              <div className="login-input-wrapper">
                <Mail className="login-input-icon" />
                <input
                  id="email"
                  type="email"
                  className="login-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="login-field">
              <label className="login-label" htmlFor="password">
                Senha
              </label>
              <div className="login-input-wrapper">
                <Lock className="login-input-icon" />
                <input
                  id="password"
                  type="password"
                  className="login-input login-input-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button type="submit" className="login-submit-button" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <p className="login-signup-prompt">
            Nova associação?{" "}
            <Link to="/signup" className="login-signup-link">
              Criar conta
            </Link>
          </p>
          <p className="login-hint">
            Demo ABCiber —{" "}
            <code>./scripts/init_sistema_tenant.sh</code>
          </p>
        </div>
      </div>
    </div>
  );
}
