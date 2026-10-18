import React, { useState } from "react";
import type { Membro } from "@/types/membros";
import { atualizarMeuPerfil } from "@/services/membros";
import { apiErrorMessage } from "@/utils/apiError";

export default function PerfilPublicoForm({ membro, onSalvo }: { membro: Membro; onSalvo: (m: Membro) => void }) {
  const [form, setForm] = useState({
    instituicao: membro.instituicao ?? "",
    area_atuacao: membro.area_atuacao ?? "",
    lattes_url: membro.lattes_url ?? "",
    orcid: membro.orcid ?? "",
    telefone: membro.telefone ?? "",
    mini_bio: membro.mini_bio ?? "",
    diretorio_publico: Boolean(membro.diretorio_publico),
  });
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    setOk("");
    try {
      const m = await atualizarMeuPerfil(form);
      onSalvo(m);
      setOk(m.diretorio_publico ? "Perfil salvo. Você aparece no diretório do site." : "Perfil salvo.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível salvar."));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <form className="dashboard-content-panel page-form" style={{ marginBottom: "1.25rem" }} onSubmit={salvar}>
      <h2 className="dashboard-title" style={{ fontSize: "1.05rem", marginTop: 0 }}>
        Perfil acadêmico e diretório
      </h2>
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {ok && <div className="highlight-banner">{ok}</div>}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Instituição</label>
          <input className="form-input" value={form.instituicao} onChange={(e) => setForm({ ...form, instituicao: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">Área de atuação</label>
          <input className="form-input" value={form.area_atuacao} onChange={(e) => setForm({ ...form, area_atuacao: e.target.value })} />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Currículo Lattes</label>
          <input className="form-input" type="url" placeholder="http://lattes.cnpq.br/..." value={form.lattes_url} onChange={(e) => setForm({ ...form, lattes_url: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">ORCID</label>
          <input className="form-input" placeholder="0000-0000-0000-0000" maxLength={19} value={form.orcid} onChange={(e) => setForm({ ...form, orcid: e.target.value })} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Minibiografia</label>
        <textarea className="form-input" rows={3} maxLength={600} value={form.mini_bio} onChange={(e) => setForm({ ...form, mini_bio: e.target.value })} placeholder="Temas de pesquisa, grupos, atuação" />
      </div>
      <div className="form-group">
        <label className="form-label">Telefone (não aparece no diretório)</label>
        <input className="form-input" value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} />
      </div>
      <label style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: "0.9rem", margin: "0.25rem 0 1rem" }}>
        <input type="checkbox" style={{ marginTop: 3 }} checked={form.diretorio_publico} onChange={(e) => setForm({ ...form, diretorio_publico: e.target.checked })} />
        <span>
          Quero aparecer no diretório público de associados do site, com nome, instituição, área, minibiografia,
          Lattes e ORCID. E-mail, telefone e CPF nunca são exibidos. Posso desmarcar a qualquer momento.
        </span>
      </label>
      <div className="form-actions">
        <button type="submit" className="dashboard-btn-save" disabled={salvando}>
          {salvando ? "Salvando..." : "Salvar perfil"}
        </button>
      </div>
    </form>
  );
}
