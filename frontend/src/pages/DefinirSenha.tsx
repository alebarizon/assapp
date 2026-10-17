import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Lock } from "lucide-react";
import AuthShell from "@/components/auth/AuthShell";
import { useAuth } from "@/contexts/AuthContext";
import { definirSenha, validarLinkSenha, type LinkSenha } from "@/services/equipe";
import { setAuthToken, setTenantSchema } from "@/services/api";
import { apiErrorMessage } from "@/utils/apiError";
import { homePathForUser } from "@/utils/roles";

export default function DefinirSenha() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser, setSetupCompleted, refreshTenantStatus } = useAuth();
  const link: LinkSenha = {
    schema: searchParams.get("schema") || "",
    uid: searchParams.get("uid") || "",
    token: searchParams.get("token") || "",
  };
  const [conta, setConta] = useState<{ email: string; first_name: string } | null>(null);
  const [verificando, setVerificando] = useState(true);
  const [senha, setSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    validarLinkSenha(link)
      .then(setConta)
      .catch((err) => setErro(apiErrorMessage(err, "Link inválido ou expirado.")))
      .finally(() => setVerificando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (senha.length < 8) {
      setErro("A senha deve ter pelo menos 8 caracteres.");
      return;
    }
    if (senha !== confirmacao) {
      setErro("As senhas não conferem.");
      return;
    }
    setErro("");
    setLoading(true);
    try {
      const data = await definirSenha(link, senha);
      setAuthToken(data.access);
      setTenantSchema(data.tenant_schema);
      setUser(data.user);
      const completed = data.setup_completed ?? true;
      setSetupCompleted(completed);
      await refreshTenantStatus();
      navigate(homePathForUser(data.user, completed));
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível definir a senha."));
    } finally {
      setLoading(false);
    }
  };

  const recuperar = `/esqueci-senha${link.schema ? `?schema=${encodeURIComponent(link.schema)}` : ""}`;

  return (
    <AuthShell
      title="Definir senha"
      subtitle={conta ? <>Olá, {conta.first_name || conta.email}! Escolha a senha de acesso para <strong>{conta.email}</strong>.</> : undefined}
    >
      {erro && <div className="login-error-message">{erro}</div>}
      {verificando ? (
        <p className="login-form-subtitle">Verificando o link...</p>
      ) : conta ? (
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="login-label" htmlFor="senha">
              Nova senha
            </label>
            <div className="login-input-wrapper">
              <Lock className="login-input-icon" />
              <input
                id="senha"
                type="password"
                className="login-input"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
                minLength={8}
                autoFocus
                autoComplete="new-password"
              />
            </div>
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="confirmacao">
              Confirme a senha
            </label>
            <div className="login-input-wrapper">
              <Lock className="login-input-icon" />
              <input
                id="confirmacao"
                type="password"
                className="login-input"
                value={confirmacao}
                onChange={(e) => setConfirmacao(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
          </div>
          <button type="submit" className="login-submit-button" disabled={loading}>
            {loading ? "Salvando..." : "Salvar e entrar"}
          </button>
        </form>
      ) : (
        <p className="login-signup-prompt">
          <Link to={recuperar} className="login-signup-link">
            Pedir um novo link
          </Link>
        </p>
      )}
    </AuthShell>
  );
}
