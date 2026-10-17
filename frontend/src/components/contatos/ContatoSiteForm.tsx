import React, { useState } from "react";
import { enviarContatoPublico } from "@/services/contatos";
import { apiErrorMessage } from "@/utils/apiError";
import { ASSUNTO_LABEL, type ContatoAssunto, type ContatoPublicoPayload } from "@/types/contatos";
import "./Contatos.css";

const VAZIO: ContatoPublicoPayload = {
  nome: "",
  email: "",
  telefone: "",
  instituicao: "",
  assunto: "outro",
  mensagem: "",
  consentimento_lgpd: false,
  website: "",
};

export default function ContatoSiteForm({ schema, associacao }: { schema: string; associacao: string }) {
  const [form, setForm] = useState<ContatoPublicoPayload>(VAZIO);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState("");
  const [erro, setErro] = useState("");

  const set = <K extends keyof ContatoPublicoPayload>(campo: K, valor: ContatoPublicoPayload[K]) =>
    setForm((f) => ({ ...f, [campo]: valor }));

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      const resp = await enviarContatoPublico(schema, {
        ...form,
        origem: form.assunto === "filiacao" ? "site_associe_se" : "site_contato",
      });
      setOk(resp.detail);
      setForm(VAZIO);
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setErro(
        status === 429
          ? "Muitas mensagens enviadas. Tente novamente mais tarde."
          : apiErrorMessage(err, "Não foi possível enviar. Tente novamente.")
      );
    } finally {
      setEnviando(false);
    }
  };

  if (ok) {
    return (
      <div className="ts-contato-ok">
        {ok}{" "}
        <button
          type="button"
          onClick={() => setOk("")}
          style={{ marginLeft: 8, background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer" }}
        >
          Enviar outra mensagem
        </button>
      </div>
    );
  }

  return (
    <form className="ts-contato-form" onSubmit={enviar}>
      <div className="ts-row">
        <label>
          Nome *
          <input required maxLength={200} value={form.nome} onChange={(e) => set("nome", e.target.value)} />
        </label>
        <label>
          E-mail *
          <input type="email" required value={form.email} onChange={(e) => set("email", e.target.value)} />
        </label>
      </div>
      <div className="ts-row">
        <label>
          Telefone
          <input maxLength={40} value={form.telefone} onChange={(e) => set("telefone", e.target.value)} />
        </label>
        <label>
          Instituição
          <input maxLength={255} value={form.instituicao} onChange={(e) => set("instituicao", e.target.value)} />
        </label>
      </div>
      <label>
        Assunto
        <select value={form.assunto} onChange={(e) => set("assunto", e.target.value as ContatoAssunto)}>
          {Object.entries(ASSUNTO_LABEL).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
      </label>
      <label>
        Mensagem *
        <textarea required rows={5} maxLength={5000} value={form.mensagem} onChange={(e) => set("mensagem", e.target.value)} />
      </label>
      <label className="ts-hp" aria-hidden="true">
        Site
        <input tabIndex={-1} autoComplete="off" value={form.website} onChange={(e) => set("website", e.target.value)} />
      </label>
      <label className="ts-consent">
        <input
          type="checkbox"
          required
          checked={form.consentimento_lgpd}
          onChange={(e) => set("consentimento_lgpd", e.target.checked)}
        />
        Autorizo {associacao} a usar meus dados para responder a este contato, conforme a LGPD.
      </label>
      {erro && <div className="ts-contato-erro">{erro}</div>}
      <button type="submit" className="ts-contato-submit" disabled={enviando}>
        {enviando ? "Enviando..." : "Enviar mensagem"}
      </button>
    </form>
  );
}
