import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeSetup } from "@/services/auth";
import { useAuth } from "@/contexts/AuthContext";

const STEPS = ["Dados", "1º Mandato", "Diretoria"] as const;

export default function AssociationSetup() {
  const navigate = useNavigate();
  const { user, tenantStatus, setSetupCompleted, refreshTenantStatus } = useAuth();
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [assoc, setAssoc] = useState({
    association_name: "",
    description: "",
    city: "",
    state: "",
    cnpj: "",
  });

  useEffect(() => {
    if (!tenantStatus) return;
    setAssoc((prev) => ({
      association_name: prev.association_name || tenantStatus.name || "",
      description: prev.description || tenantStatus.description || "",
      city: prev.city || tenantStatus.city || "",
      state: prev.state || tenantStatus.state || "",
      cnpj: prev.cnpj || tenantStatus.cnpj || "",
    }));
  }, [tenantStatus]);

  const [mandato, setMandato] = useState({
    titulo: "Diretoria 2026-2028",
    data_inicio: "2026-01-01",
    data_fim: "2028-12-31",
    descricao: "",
  });

  const [presidenteComoAdmin, setPresidenteComoAdmin] = useState(true);
  const [extraCargos, setExtraCargos] = useState<
    Array<{ cargo: string; email: string; first_name: string; last_name: string }>
  >([]);

  const finish = async () => {
    setError("");
    setLoading(true);
    try {
      const cargos: Array<{
        cargo: string;
        email?: string;
        first_name?: string;
        last_name?: string;
      }> = [
        {
          cargo: "presidente",
          ...(presidenteComoAdmin
            ? {}
            : {
                email: user?.email,
                first_name: user?.first_name,
                last_name: user?.last_name,
              }),
        },
        ...extraCargos
          .filter((c) => c.email && c.cargo)
          .map((c) => ({
            cargo: c.cargo,
            email: c.email,
            first_name: c.first_name,
            last_name: c.last_name,
          })),
      ];

      await completeSetup({
        association_name: assoc.association_name || undefined,
        description: assoc.description || undefined,
        city: assoc.city || undefined,
        state: assoc.state || undefined,
        cnpj: assoc.cnpj || undefined,
        mandato: {
          titulo: mandato.titulo,
          data_inicio: mandato.data_inicio,
          data_fim: mandato.data_fim || undefined,
          descricao: mandato.descricao || undefined,
        },
        cargos,
      });
      setSetupCompleted(true);
      await refreshTenantStatus();
      navigate("/app/memoria");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Não foi possível concluir o setup.";
      setError(typeof detail === "string" ? detail : "Erro no setup.");
    } finally {
      setLoading(false);
    }
  };

  const next = () => {
    setError("");
    if (step === 0 && !assoc.association_name.trim()) {
      setError("Informe o nome da associação.");
      return;
    }
    if (step === 1 && (!mandato.titulo.trim() || !mandato.data_inicio)) {
      setError("Informe título e data de início do mandato.");
      return;
    }
    if (step < STEPS.length - 1) setStep((s) => s + 1);
    else void finish();
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Configurar associação</h1>
        <p className="dashboard-subtitle">
          Complete o setup para criar o 1º mandato e a diretoria.
        </p>
      </div>

      <div className="setup-steps">
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={`setup-step${i === step ? " active" : ""}${i < step ? " done" : ""}`}
          >
            {i + 1}. {label}
          </div>
        ))}
      </div>

      <div className="page-form-container">
        <div className="page-form-header">
          <h2 className="page-form-title">{STEPS[step]}</h2>
        </div>

        <div className="page-form">
          {step === 0 && (
            <>
              <div className="form-group">
                <label className="form-label">Nome da associação</label>
                <input
                  className="form-input"
                  value={assoc.association_name}
                  onChange={(e) => setAssoc({ ...assoc, association_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Descrição</label>
                <textarea
                  className="form-input"
                  rows={3}
                  value={assoc.description}
                  onChange={(e) => setAssoc({ ...assoc, description: e.target.value })}
                />
              </div>
              <div className="form-row-3">
                <div className="form-group">
                  <label className="form-label">Cidade</label>
                  <input
                    className="form-input"
                    value={assoc.city}
                    onChange={(e) => setAssoc({ ...assoc, city: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">UF</label>
                  <input
                    className="form-input"
                    maxLength={2}
                    value={assoc.state}
                    onChange={(e) =>
                      setAssoc({ ...assoc, state: e.target.value.toUpperCase() })
                    }
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">CNPJ</label>
                <input
                  className="form-input"
                  value={assoc.cnpj}
                  onChange={(e) => setAssoc({ ...assoc, cnpj: e.target.value })}
                />
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <div className="form-group">
                <label className="form-label">Título do mandato</label>
                <input
                  className="form-input"
                  value={mandato.titulo}
                  onChange={(e) => setMandato({ ...mandato, titulo: e.target.value })}
                />
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label">Início</label>
                  <input
                    type="date"
                    className="form-input"
                    value={mandato.data_inicio}
                    onChange={(e) => setMandato({ ...mandato, data_inicio: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Fim</label>
                  <input
                    type="date"
                    className="form-input"
                    value={mandato.data_fim}
                    onChange={(e) => setMandato({ ...mandato, data_fim: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Observações</label>
                <textarea
                  className="form-input"
                  rows={2}
                  value={mandato.descricao}
                  onChange={(e) => setMandato({ ...mandato, descricao: e.target.value })}
                />
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <label className="inline-check">
                <input
                  type="checkbox"
                  checked={presidenteComoAdmin}
                  onChange={(e) => setPresidenteComoAdmin(e.target.checked)}
                />
                <span>
                  <strong>Eu sou o(a) presidente desta gestão</strong>
                  <br />
                  <span style={{ fontSize: "0.8rem", color: "#666" }}>
                    Usa sua conta ({user?.email}) como presidente do 1º mandato.
                  </span>
                </span>
              </label>

              <div style={{ marginTop: "1rem" }}>
                <div className="btn-row" style={{ marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>
                    Outros cargos (opcional)
                  </span>
                  <button
                    type="button"
                    className="dashboard-btn-secondary"
                    onClick={() =>
                      setExtraCargos([
                        ...extraCargos,
                        { cargo: "secretario", email: "", first_name: "", last_name: "" },
                      ])
                    }
                  >
                    + Adicionar
                  </button>
                </div>
                {extraCargos.map((c, idx) => (
                  <div key={idx} className="form-row-2" style={{ marginBottom: "0.75rem" }}>
                    <select
                      className="form-select"
                      value={c.cargo}
                      onChange={(e) => {
                        const next = [...extraCargos];
                        next[idx] = { ...next[idx], cargo: e.target.value };
                        setExtraCargos(next);
                      }}
                    >
                      <option value="vice_presidente">Vice-Presidente</option>
                      <option value="secretario">Secretário</option>
                      <option value="tesoureiro">Tesoureiro</option>
                      <option value="diretor">Diretor</option>
                      <option value="conselho_fiscal">Conselho Fiscal</option>
                    </select>
                    <input
                      className="form-input"
                      placeholder="E-mail"
                      value={c.email}
                      onChange={(e) => {
                        const next = [...extraCargos];
                        next[idx] = { ...next[idx], email: e.target.value };
                        setExtraCargos(next);
                      }}
                    />
                    <input
                      className="form-input"
                      placeholder="Nome"
                      value={c.first_name}
                      onChange={(e) => {
                        const next = [...extraCargos];
                        next[idx] = { ...next[idx], first_name: e.target.value };
                        setExtraCargos(next);
                      }}
                    />
                    <input
                      className="form-input"
                      placeholder="Sobrenome"
                      value={c.last_name}
                      onChange={(e) => {
                        const next = [...extraCargos];
                        next[idx] = { ...next[idx], last_name: e.target.value };
                        setExtraCargos(next);
                      }}
                    />
                  </div>
                ))}
              </div>
            </>
          )}

          {error && <div className="alert-banner alert-banner-error">{error}</div>}

          <div className="form-actions btn-row">
            <button
              type="button"
              className="dashboard-btn-cancel"
              disabled={step === 0 || loading}
              onClick={() => setStep((s) => s - 1)}
            >
              Voltar
            </button>
            <button
              type="button"
              className="dashboard-btn-save"
              disabled={loading}
              onClick={next}
            >
              {loading
                ? "Salvando..."
                : step === STEPS.length - 1
                  ? "Concluir setup"
                  : "Continuar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
