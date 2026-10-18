import React, { useState } from "react";
import { ExternalLink } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import type { EventoAcademico } from "@/types/eventos";
import { enviarCapaEvento, removerCapaEvento, salvarItemLojaEvento, updateEvento } from "@/services/eventos";
import { buildTenantSiteQuery } from "@/utils/tenantSite";

function mensagemErro(err: unknown, padrao: string): string {
  const data = (err as { response?: { data?: Record<string, string | string[]> } })?.response?.data;
  if (!data) return padrao;
  const primeiro = data.detail ?? Object.values(data)[0];
  return String((Array.isArray(primeiro) ? primeiro[0] : primeiro) || padrao);
}

interface Props {
  evento: EventoAcademico;
  onAtualizado: (evento: EventoAcademico) => void;
}

export default function HotsiteEvento({ evento, onAtualizado }: Props) {
  const { tenantSchema } = useAuth();
  const [site, setSite] = useState({
    publicado_site: Boolean(evento.publicado_site),
    resumo: evento.resumo ?? "",
  });
  const [loja, setLoja] = useState({
    price: evento.item_loja?.price ?? evento.valor_inscricao ?? "",
    member_price: evento.item_loja?.member_price ?? "",
    is_active: evento.item_loja?.is_active ?? true,
  });
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");
  const [salvando, setSalvando] = useState<"site" | "loja" | "capa" | null>(null);

  const siteUrl = `/site/eventos/${evento.slug}${buildTenantSiteQuery(tenantSchema || "")}`;

  const executar = async (qual: "site" | "loja" | "capa", acao: () => Promise<EventoAcademico>, ok: string) => {
    setSalvando(qual);
    setErro("");
    setMsg("");
    try {
      onAtualizado(await acao());
      setMsg(ok);
    } catch (err) {
      setErro(mensagemErro(err, "Não foi possível salvar."));
    } finally {
      setSalvando(null);
    }
  };

  const salvarSite = (e: React.FormEvent) => {
    e.preventDefault();
    void executar(
      "site",
      async () => {
        await updateEvento(evento.id, site);
        return { ...evento, ...site };
      },
      site.publicado_site ? "Hotsite publicado." : "Configuração do site salva."
    );
  };

  const salvarLoja = (e: React.FormEvent) => {
    e.preventDefault();
    void executar(
      "loja",
      () =>
        salvarItemLojaEvento(evento.id, {
          price: loja.price || "0",
          member_price: loja.member_price === "" ? null : loja.member_price,
          is_active: loja.is_active,
        }),
      "Inscrição na loja atualizada."
    );
  };

  return (
    <div className="dashboard-content-panel">
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      <form className="page-form" onSubmit={salvarSite}>
        <h3 className="page-form-title" style={{ fontSize: "1.05rem" }}>
          Hotsite do evento
        </h3>
        <p className="form-help-text" style={{ marginTop: 0 }}>
          Página pública com descrição, programação, chamada de trabalhos e inscrição. Eventos em rascunho ou
          cancelados não aparecem, mesmo publicados.
        </p>
        <div className="form-group">
          <label className="form-label">Resumo (cards e topo da página)</label>
          <input
            className="form-input"
            maxLength={300}
            value={site.resumo}
            onChange={(e) => setSite({ ...site, resumo: e.target.value })}
          />
        </div>
        <label className="inline-check">
          <input
            type="checkbox"
            checked={site.publicado_site}
            onChange={(e) => setSite({ ...site, publicado_site: e.target.checked })}
          />
          <span>Publicar no site da associação</span>
        </label>
        <div className="form-actions">
          {evento.publicado_site && (
            <a className="dashboard-btn-secondary" href={siteUrl} target="_blank" rel="noreferrer">
              <ExternalLink size={14} /> Ver hotsite
            </a>
          )}
          <button type="submit" className="dashboard-btn-save" disabled={salvando === "site"}>
            {salvando === "site" ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>

      <div className="page-form" style={{ marginTop: "1.5rem" }}>
        <label className="form-label">Capa</label>
        {evento.capa_url && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <img src={evento.capa_url} alt="" style={{ width: 220, borderRadius: 8 }} />
            <button
              type="button"
              className="dashboard-btn-cancel"
              disabled={salvando === "capa"}
              onClick={() => void executar("capa", () => removerCapaEvento(evento.id), "Capa removida.")}
            >
              Remover capa
            </button>
          </div>
        )}
        <input
          type="file"
          accept="image/*"
          disabled={salvando === "capa"}
          onChange={(e) => {
            const arquivo = e.target.files?.[0];
            if (arquivo) void executar("capa", () => enviarCapaEvento(evento.id, arquivo), "Capa atualizada.");
          }}
        />
      </div>

      <form className="page-form" onSubmit={salvarLoja} style={{ marginTop: "1.5rem" }}>
        <h3 className="page-form-title" style={{ fontSize: "1.05rem" }}>
          Inscrição pela loja
        </h3>
        <p className="form-help-text" style={{ marginTop: 0 }}>
          O associado se inscreve pela loja do portal; a inscrição é confirmada quando o pedido é pago (online ou
          confirmado pela tesouraria). Use preço zero para eventos gratuitos.
        </p>
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Preço (R$) *</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0"
              required
              value={loja.price}
              onChange={(e) => setLoja({ ...loja, price: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Preço para sócio em dia (R$)</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0"
              placeholder="Vazio = mesmo preço"
              value={loja.member_price}
              onChange={(e) => setLoja({ ...loja, member_price: e.target.value })}
            />
          </div>
        </div>
        <label className="inline-check">
          <input
            type="checkbox"
            checked={loja.is_active}
            onChange={(e) => setLoja({ ...loja, is_active: e.target.checked })}
          />
          <span>Inscrições abertas na loja</span>
        </label>
        <div className="form-actions">
          <button type="submit" className="dashboard-btn-save" disabled={salvando === "loja"}>
            {salvando === "loja" ? "Salvando..." : evento.item_loja ? "Atualizar inscrição" : "Criar inscrição na loja"}
          </button>
        </div>
      </form>
    </div>
  );
}
