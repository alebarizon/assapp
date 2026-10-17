import React, { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { apiErrorMessage } from "@/utils/apiError";
import type { FormularioParaResponder, PerguntaPublica, ValorResposta } from "@/types/formularios";

type Answers = Record<string, ValorResposta>;

interface FormResponderProps {
  formulario: FormularioParaResponder;
  /** Permite salvar rascunho (portal e convite). */
  permitirRascunho?: boolean;
  /** Pede nome e e-mail (link público com identificação). */
  pedirIdentificacao?: boolean;
  onEnviar: (
    answers: Answers,
    enviar: boolean,
    identificacao: { nome: string; email: string }
  ) => Promise<{ mensagem_confirmacao: string }>;
  acaoFinal?: React.ReactNode;
}

function Campo({
  pergunta,
  valor,
  onChange,
  disabled,
}: {
  pergunta: PerguntaPublica;
  valor: ValorResposta | undefined;
  onChange: (v: ValorResposta) => void;
  disabled: boolean;
}) {
  const texto = typeof valor === "string" ? valor : "";
  switch (pergunta.tipo) {
    case "texto_longo":
      return <textarea className="form-input" rows={4} value={texto} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case "numero":
      return <input className="form-input" type="number" step="any" value={texto} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case "email":
      return <input className="form-input" type="email" value={texto} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case "data":
      return <input className="form-input" type="date" value={texto} disabled={disabled} onChange={(e) => onChange(e.target.value)} style={{ maxWidth: 220 }} />;
    case "escolha_unica":
      return (
        <div>
          {pergunta.opcoes.map((opcao) => (
            <label key={opcao} className="fr-option">
              <input type="radio" name={pergunta.id} checked={texto === opcao} disabled={disabled} onChange={() => onChange(opcao)} />
              {opcao}
            </label>
          ))}
        </div>
      );
    case "multipla_escolha": {
      const lista = Array.isArray(valor) ? valor : [];
      return (
        <div>
          {pergunta.opcoes.map((opcao) => (
            <label key={opcao} className="fr-option">
              <input
                type="checkbox"
                checked={lista.includes(opcao)}
                disabled={disabled}
                onChange={(e) => onChange(e.target.checked ? [...lista, opcao] : lista.filter((o) => o !== opcao))}
              />
              {opcao}
            </label>
          ))}
        </div>
      );
    }
    case "escala": {
      const notas = [];
      for (let n = pergunta.escala_min; n <= pergunta.escala_max; n++) notas.push(String(n));
      return (
        <div className="fr-scale">
          {notas.map((n) => (
            <button
              key={n}
              type="button"
              className={texto === n ? "selected" : ""}
              disabled={disabled}
              onClick={() => onChange(texto === n ? "" : n)}
            >
              {n}
            </button>
          ))}
        </div>
      );
    }
    default:
      return <input className="form-input" value={texto} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
  }
}

export default function FormResponder({
  formulario,
  permitirRascunho = false,
  pedirIdentificacao = false,
  onEnviar,
  acaoFinal,
}: FormResponderProps) {
  const jaEnviada = formulario.situacao === "enviada";
  const [answers, setAnswers] = useState<Answers>(formulario.valores || {});
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [erros, setErros] = useState<Record<string, string>>({});
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [concluido, setConcluido] = useState<string | null>(jaEnviada ? formulario.mensagem_confirmacao : null);

  const fechado = !formulario.aceitando_respostas;

  const submeter = async (enviar: boolean) => {
    setErro("");
    setAviso("");
    setErros({});
    setEnviando(true);
    try {
      const result = await onEnviar(answers, enviar, { nome: nome.trim(), email: email.trim() });
      if (enviar) {
        setConcluido(result.mensagem_confirmacao || "");
        window.scrollTo(0, 0);
      } else {
        setAviso("Rascunho salvo. Você pode continuar depois.");
      }
    } catch (err) {
      const data = (err as { response?: { data?: { erros?: Record<string, string> } } })?.response?.data;
      if (data?.erros) setErros(data.erros);
      setErro(apiErrorMessage(err, "Não foi possível enviar. Tente novamente."));
    } finally {
      setEnviando(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void submeter(true);
  };

  if (concluido !== null) {
    return (
      <div className="fr-done">
        <CheckCircle2 size={44} color="#027a48" />
        <h2>Resposta enviada</h2>
        <p style={{ whiteSpace: "pre-wrap" }}>{concluido || "Obrigado pela sua participação!"}</p>
        {acaoFinal}
      </div>
    );
  }

  return (
    <form className="page-form" style={{ gap: 0 }} onSubmit={handleSubmit}>
      {fechado && <div className="alert-banner alert-banner-error">Este formulário não está recebendo respostas.</div>}
      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {aviso && <div className="alert-banner alert-banner-success">{aviso}</div>}

      {pedirIdentificacao && (
        <div className="form-row-2" style={{ marginBottom: "1rem" }}>
          <div className="form-group">
            <label className="form-label">Seu nome *</label>
            <input className="form-input" value={nome} required onChange={(e) => setNome(e.target.value)} />
            {erros.nome && <div className="fr-error">{erros.nome}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Seu e-mail *</label>
            <input className="form-input" type="email" value={email} required onChange={(e) => setEmail(e.target.value)} />
          </div>
        </div>
      )}

      {formulario.secoes.map((secao) => (
        <div key={secao.id}>
          {secao.titulo && <h3 className="fr-section-title">{secao.titulo}</h3>}
          {secao.descricao && <p className="fb-muted" style={{ marginTop: 0, whiteSpace: "pre-wrap" }}>{secao.descricao}</p>}
          {secao.perguntas.map((p) => (
            <div key={p.id} className={`fr-question${erros[p.id] ? " has-error" : ""}`}>
              <span className="fr-question-label">
                {p.texto}
                {p.obrigatoria && <span style={{ color: "#b42318" }}> *</span>}
              </span>
              {p.ajuda && <p className="fb-muted" style={{ margin: "0 0 0.4rem" }}>{p.ajuda}</p>}
              <Campo
                pergunta={p}
                valor={answers[p.id]}
                disabled={fechado || enviando}
                onChange={(v) => setAnswers((prev) => ({ ...prev, [p.id]: v }))}
              />
              {erros[p.id] && <div className="fr-error">{erros[p.id]}</div>}
            </div>
          ))}
        </div>
      ))}

      {!fechado && (
        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end", marginTop: "1rem" }}>
          {permitirRascunho && (
            <button type="button" className="dashboard-btn-secondary" disabled={enviando} onClick={() => submeter(false)}>
              Salvar rascunho
            </button>
          )}
          <button type="submit" className="dashboard-btn-new" disabled={enviando}>
            {enviando ? "Enviando..." : "Enviar respostas"}
          </button>
        </div>
      )}
    </form>
  );
}
