/**
 * OnboardingWizard — H2: Interface adaptativa para Nova Diretoria
 *
 * Adapta a experiência conforme perfil_tecnico do usuário:
 * - iniciante: wizards expandidos, descrições longas, uma etapa por vez
 * - intermediario: checklist com navegação livre
 * - avancado: visão compacta, etapas opcionais ocultas
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Circle, ChevronRight, Sparkles, Users } from "lucide-react";
import type { OnboardingEtapa, PerfilTecnico, TransicaoMandato } from "@/types";
import {
  concluirEtapa,
  getTransicaoEmAndamento,
  listOnboardingEtapas,
  updatePerfilTecnico,
} from "@/services/mandatos";
import { useAuth } from "@/contexts/AuthContext";

const PERFIL_LABELS: Record<PerfilTecnico, string> = {
  iniciante: "Iniciante — guia passo a passo",
  intermediario: "Intermediário — checklist guiado",
  avancado: "Avançado — visão compacta",
};

export default function OnboardingWizard() {
  const { user, refreshUser } = useAuth();
  const [transicao, setTransicao] = useState<TransicaoMandato | null>(null);
  const [etapas, setEtapas] = useState<OnboardingEtapa[]>([]);
  const [etapaAtual, setEtapaAtual] = useState(0);
  const [loading, setLoading] = useState(true);
  const [concluindo, setConcluindo] = useState(false);
  const [error, setError] = useState("");

  const perfil = user?.perfil_tecnico ?? "iniciante";
  const modoIniciante = perfil === "iniciante";
  const modoAvancado = perfil === "avancado";

  const carregar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const t = await getTransicaoEmAndamento();
      setTransicao(t);
      if (t) {
        const lista = await listOnboardingEtapas(t.id);
        const visiveis = lista.filter((e) => e.visivel !== false);
        setEtapas(visiveis);
        const primeiraPendente = visiveis.findIndex((e) => !e.concluida);
        setEtapaAtual(primeiraPendente >= 0 ? primeiraPendente : 0);
      }
    } catch {
      setError("Erro ao carregar onboarding.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const handleConcluir = async (etapa: OnboardingEtapa) => {
    setConcluindo(true);
    try {
      await concluirEtapa(etapa.id);
      await carregar();
      if (modoIniciante) {
        setEtapaAtual((i) => Math.min(i + 1, etapas.length - 1));
      }
    } catch {
      setError("Erro ao concluir etapa.");
    } finally {
      setConcluindo(false);
    }
  };

  const handlePerfilChange = async (novoPerfil: PerfilTecnico) => {
    await updatePerfilTecnico(novoPerfil);
    await refreshUser();
    await carregar();
  };

  const etapasVisiveis = modoAvancado
    ? etapas.filter((e) => e.obrigatoria)
    : etapas;

  const progresso =
    etapasVisiveis.length === 0
      ? 0
      : Math.round(
          (etapasVisiveis.filter((e) => e.concluida).length / etapasVisiveis.length) * 100
        );

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando onboarding...</p>
        </div>
      </div>
    );
  }

  if (!transicao) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-empty" style={{ textAlign: "center", padding: "3rem 1rem" }}>
          <Users size={48} style={{ marginBottom: "1rem", opacity: 0.4 }} />
          <h2 className="dashboard-title" style={{ fontSize: "1.25rem" }}>
            Nenhuma transição em andamento
          </h2>
          <p className="dashboard-subtitle">
            Inicie uma transição de mandato em{" "}
            <a href="/app/mandatos">Mandatos</a> para ativar o modo Nova Diretoria.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="highlight-banner">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Sparkles size={16} />
          <p className="highlight-banner-label" style={{ margin: 0 }}>
            Modo Nova Diretoria — H2
          </p>
        </div>
        <h1 className="highlight-banner-title">Onboarding da Nova Gestão</h1>
        <p className="highlight-banner-meta">
          {transicao.mandato_anterior_titulo} → {transicao.mandato_novo_titulo}
        </p>
        <div style={{ marginTop: "1rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "0.875rem",
              color: "#666666",
              marginBottom: "0.35rem",
            }}
          >
            <span>Progresso</span>
            <span>{progresso}%</span>
          </div>
          <div
            style={{
              height: "0.5rem",
              background: "#ecebe6",
              borderRadius: "999px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progresso}%`,
                background: "#c79b45",
                transition: "width 0.5s",
              }}
            />
          </div>
        </div>
      </div>

      <div className="dashboard-content-panel" style={{ marginBottom: "1.25rem" }}>
        <p className="form-label" style={{ marginBottom: "0.75rem" }}>
          Seu perfil técnico (adapta a interface):
        </p>
        <div className="filters-row" style={{ marginBottom: 0 }}>
          {(["iniciante", "intermediario", "avancado"] as PerfilTecnico[]).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => handlePerfilChange(p)}
              className={perfil === p ? "dashboard-btn-save" : "dashboard-btn-secondary"}
            >
              {PERFIL_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="alert-banner alert-banner-error">{error}</div>}

      {modoIniciante ? (
        etapasVisiveis[etapaAtual] && (
          <EtapaCard
            etapa={etapasVisiveis[etapaAtual]}
            expandida
            onConcluir={handleConcluir}
            concluindo={concluindo}
            mandatoAnteriorId={transicao.mandato_anterior}
          />
        )
      ) : (
        <div className="list-stack">
          {etapasVisiveis.map((etapa) => (
            <EtapaCard
              key={etapa.id}
              etapa={etapa}
              expandida={!modoAvancado}
              onConcluir={handleConcluir}
              concluindo={concluindo}
              mandatoAnteriorId={transicao.mandato_anterior}
            />
          ))}
        </div>
      )}

      {modoIniciante && etapasVisiveis.length > 1 && (
        <div className="btn-row" style={{ marginTop: "1.25rem" }}>
          <button
            type="button"
            className="dashboard-btn-secondary"
            disabled={etapaAtual === 0}
            onClick={() => setEtapaAtual((i) => i - 1)}
          >
            ← Anterior
          </button>
          <span className="dashboard-subtitle" style={{ margin: 0 }}>
            {etapaAtual + 1} / {etapasVisiveis.length}
          </span>
          <button
            type="button"
            className="dashboard-btn-edit"
            disabled={etapaAtual >= etapasVisiveis.length - 1}
            onClick={() => setEtapaAtual((i) => i + 1)}
          >
            Próxima <ChevronRight size={16} />
          </button>
        </div>
      )}

      {progresso === 100 && (
        <div className="alert-banner alert-banner-success" style={{ marginTop: "1.25rem", textAlign: "center" }}>
          <CheckCircle2 size={40} style={{ margin: "0 auto 0.75rem" }} />
          <h3 style={{ margin: 0 }}>Onboarding concluído!</h3>
          <p style={{ margin: "0.5rem 0 0" }}>
            A nova diretoria está operacional. Métrica H1: tempo de onboarding registrado.
          </p>
        </div>
      )}
    </div>
  );
}

function etapaDeepLink(
  codigo: string,
  mandatoAnteriorId?: string
): { to: string; label: string } | null {
  // H2 — deep-links mínimos para módulos PIPE
  switch (codigo) {
    case "revisar_snapshot":
      return mandatoAnteriorId
        ? { to: `/app/mandatos/${mandatoAnteriorId}`, label: "Abrir mandato anterior" }
        : null;
    case "revisar_membros":
      return { to: "/app/membros", label: "Abrir Membros" };
    case "revisar_financeiro":
      return { to: "/app/finance", label: "Abrir Financeiro" };
    case "revisar_eventos":
      return { to: "/app/eventos", label: "Abrir Eventos" };
    case "revisar_decisoes":
      return { to: "/app/memoria", label: "Abrir Memória" };
    default:
      return null;
  }
}

function EtapaCard({
  etapa,
  expandida,
  onConcluir,
  concluindo,
  mandatoAnteriorId,
}: {
  etapa: OnboardingEtapa;
  expandida: boolean;
  onConcluir: (e: OnboardingEtapa) => void;
  concluindo: boolean;
  mandatoAnteriorId?: string;
}) {
  const deepLink = expandida ? etapaDeepLink(etapa.codigo, mandatoAnteriorId) : null;

  return (
    <div className="list-card" style={{ alignItems: "flex-start" }}>
      {etapa.concluida ? (
        <CheckCircle2 size={24} style={{ color: "#027a48", flexShrink: 0, marginTop: "0.15rem" }} />
      ) : (
        <Circle size={24} style={{ color: "#d0d0d0", flexShrink: 0, marginTop: "0.15rem" }} />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <p className="list-card-title">{etapa.titulo}</p>
          {etapa.obrigatoria && (
            <span className="status-badge status-badge-pendente">obrigatória</span>
          )}
        </div>
        {expandida && etapa.descricao && (
          <p className="list-card-meta">{etapa.descricao}</p>
        )}
        {deepLink && (
          <p className="list-card-meta" style={{ marginTop: "0.5rem" }}>
            <Link
              to={deepLink.to}
              className="dashboard-btn-secondary"
              style={{ display: "inline-flex", textDecoration: "none" }}
            >
              {deepLink.label}
            </Link>
          </p>
        )}
        {!etapa.concluida && (
          <button
            type="button"
            className="dashboard-btn-save"
            style={{ marginTop: "0.75rem" }}
            onClick={() => onConcluir(etapa)}
            disabled={concluindo}
          >
            {concluindo ? "Salvando..." : "Marcar como concluída"}
          </button>
        )}
        {etapa.concluida && etapa.concluida_em && (
          <p className="list-card-meta" style={{ color: "#027a48" }}>
            Concluída em {new Date(etapa.concluida_em).toLocaleString("pt-BR")}
          </p>
        )}
      </div>
    </div>
  );
}
