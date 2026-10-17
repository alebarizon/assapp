import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Mail } from "lucide-react";
import AuthShell from "@/components/auth/AuthShell";
import { esqueciSenha } from "@/services/equipe";
import { apiErrorMessage } from "@/utils/apiError";

export default function EsqueciSenha() {
  const [searchParams] = useSearchParams();
  const schema = searchParams.get("schema");
  const [email, setEmail] = useState("");
  const [enviado, setEnviado] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setLoading(true);
    try {
      setEnviado(await esqueciSenha(email, schema));
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível enviar agora. Tente novamente em alguns minutos."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Esqueci a senha" subtitle="Informe seu e-mail e enviaremos um link para definir uma nova senha.">
      {erro && <div className="login-error-message">{erro}</div>}
      {enviado ? (
        <div className="alert-banner alert-banner-success">{enviado}</div>
      ) : (
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
                autoFocus
                autoComplete="email"
              />
            </div>
          </div>
          <button type="submit" className="login-submit-button" disabled={loading}>
            {loading ? "Enviando..." : "Enviar link"}
          </button>
        </form>
      )}
      <p className="login-signup-prompt">
        <Link to="/login" className="login-signup-link">
          Voltar ao login
        </Link>
      </p>
    </AuthShell>
  );
}
