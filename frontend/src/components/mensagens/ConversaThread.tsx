import React, { useEffect, useRef, useState } from "react";
import type { Conversa } from "@/types/mensagens";
import "./Mensagens.css";

function quando(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

interface Props {
  conversa: Conversa;
  /** true quando quem está vendo é a diretoria */
  diretoria: boolean;
  onResponder: (texto: string) => Promise<void>;
}

export default function ConversaThread({ conversa, diretoria, onResponder }: Props) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const fimRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ block: "nearest" });
  }, [conversa.mensagens.length]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!texto.trim()) return;
    setEnviando(true);
    try {
      await onResponder(texto);
      setTexto("");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      <div className="conversa-thread">
        {conversa.mensagens.map((m) => (
          <div key={m.id} className={`conversa-bolha ${m.da_diretoria === diretoria ? "conversa-bolha-minha" : ""}`}>
            <div className="conversa-bolha-meta">
              <strong>{m.autor_nome}</strong>
              {m.da_diretoria && !diretoria ? " · Diretoria" : ""} · {quando(m.created_at)}
            </div>
            <div className="conversa-bolha-texto">{m.texto}</div>
          </div>
        ))}
        <div ref={fimRef} />
      </div>
      <div className="page-form-container">
        <form className="page-form" onSubmit={enviar}>
          <textarea
            className="form-input"
            rows={3}
            value={texto}
            placeholder="Escreva sua resposta..."
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void enviar(e);
            }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem" }}>
            <span className="list-card-meta" style={{ margin: 0 }}>
              {diretoria ? "O associado recebe um aviso por e-mail." : "Ctrl/⌘ + Enter para enviar."}
            </span>
            <button type="submit" className="dashboard-btn-new" disabled={enviando || !texto.trim()}>
              {enviando ? "Enviando..." : "Enviar"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
