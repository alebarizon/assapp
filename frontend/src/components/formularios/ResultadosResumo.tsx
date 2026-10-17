import type { ResumoFormulario } from "@/types/formularios";

export default function ResultadosResumo({ resumo }: { resumo: ResumoFormulario }) {
  if (resumo.total_respostas === 0) {
    return <div className="dashboard-empty">Nenhuma resposta enviada ainda.</div>;
  }
  return (
    <div>
      {resumo.perguntas.map((p, index) => {
        const maior = Math.max(1, ...(p.opcoes || []).map((o) => o.total));
        return (
          <div key={p.id} className="fres-card">
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
              <strong>
                {index + 1}. {p.texto}
              </strong>
              <span className="fb-muted" style={{ whiteSpace: "nowrap" }}>
                {p.respondidas} de {resumo.total_respostas} responderam
              </span>
            </div>
            {p.media != null && (
              <p style={{ margin: "0.5rem 0" }}>
                Média: <strong>{p.media.toLocaleString("pt-BR")}</strong>
              </p>
            )}
            {p.opcoes?.map((o) => (
              <div key={o.opcao} className="fres-bar-row">
                <span>{o.opcao}</span>
                <div className="fres-bar">
                  <div style={{ width: `${(o.total / maior) * 100}%` }} />
                </div>
                <span className="fb-muted">
                  {o.total} ({p.respondidas ? Math.round((o.total / p.respondidas) * 100) : 0}%)
                </span>
              </div>
            ))}
            {p.textos &&
              (p.textos.length ? (
                <div className="fres-texts" style={{ marginTop: "0.5rem" }}>
                  {p.textos.map((t, i) => (
                    <p key={i}>{t}</p>
                  ))}
                </div>
              ) : (
                <p className="fb-muted">Sem respostas.</p>
              ))}
          </div>
        );
      })}
    </div>
  );
}
