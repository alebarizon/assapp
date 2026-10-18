import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Plus, UserX } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getOpcoesPublico, listCampanhas, listDescadastros, reinscrever } from "@/services/newsletter";
import {
  STATUS_CAMPANHA,
  descreverPublico,
  type Campanha,
  type Descadastro,
  type OpcoesPublico,
} from "@/types/newsletter";
import { apiErrorMessage } from "@/utils/apiError";
import { podeEditar } from "@/utils/roles";

function dataCurta(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "";
}

export default function Newsletter() {
  const { user } = useAuth();
  const editavel = podeEditar(user, "newsletter");
  const [campanhas, setCampanhas] = useState<Campanha[]>([]);
  const [descadastros, setDescadastros] = useState<Descadastro[]>([]);
  const [opcoes, setOpcoes] = useState<OpcoesPublico>();
  const [aba, setAba] = useState<"campanhas" | "descadastros">("campanhas");
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    Promise.all([listCampanhas(), listDescadastros(), getOpcoesPublico()])
      .then(([c, d, o]) => {
        setCampanhas(c);
        setDescadastros(d);
        setOpcoes(o);
      })
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar a newsletter.")))
      .finally(() => setLoading(false));
  }, []);

  const reativar = async (d: Descadastro) => {
    if (!window.confirm(`Voltar a enviar a newsletter para ${d.email}? Faça isso só a pedido da pessoa.`)) return;
    try {
      await reinscrever(d.id);
      setDescadastros((lista) => lista.filter((x) => x.id !== d.id));
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao reativar."));
    }
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Newsletter</h1>
          <p className="dashboard-subtitle">Campanhas por e-mail para associados, inscritos em eventos e contatos</p>
        </div>
        {editavel && (
          <div className="dashboard-header-actions">
            <Link to="/app/newsletter/nova" className="dashboard-btn-new">
              <Plus size={16} /> Nova campanha
            </Link>
          </div>
        )}
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      <div className="dashboard-tabs">
        <button type="button" className={`dashboard-tab${aba === "campanhas" ? " active" : ""}`} onClick={() => setAba("campanhas")}>
          Campanhas ({campanhas.length})
        </button>
        <button type="button" className={`dashboard-tab${aba === "descadastros" ? " active" : ""}`} onClick={() => setAba("descadastros")}>
          <UserX size={14} /> Descadastros ({descadastros.length})
        </button>
      </div>

      {aba === "campanhas" && (
        <div className="dashboard-content-panel">
          {campanhas.length === 0 ? (
            <div className="dashboard-empty">Nenhuma campanha ainda. Crie a primeira e envie um teste para você.</div>
          ) : (
            <div className="list-stack">
              {campanhas.map((c) => {
                const st = STATUS_CAMPANHA[c.status];
                const e = c.estatisticas;
                return (
                  <Link key={c.id} to={`/app/newsletter/${c.id}`} className="list-card" style={{ textDecoration: "none", color: "inherit" }}>
                    <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                      <Mail size={20} style={{ marginTop: 2, color: "#1a5f4a" }} />
                      <div>
                        <p className="list-card-title">{c.assunto}</p>
                        <p className="list-card-meta">{descreverPublico(c.publico, opcoes)}</p>
                        <p className="list-card-meta">
                          {c.status === "rascunho"
                            ? `Editado em ${dataCurta(c.updated_at)}`
                            : `Enviada em ${dataCurta(c.enviada_em)}`}
                          {e && ` · ${e.enviado} de ${e.total} enviados`}
                          {e && e.falha > 0 && ` · ${e.falha} falhas`}
                          {e && e.descadastros > 0 && ` · ${e.descadastros} descadastros`}
                        </p>
                      </div>
                    </div>
                    <span className={`status-badge status-badge-${st.badge}`}>{st.label}</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      )}

      {aba === "descadastros" && (
        <div className="dashboard-content-panel">
          <p className="list-card-meta" style={{ marginTop: 0 }}>
            Quem clicou em “não quero mais receber” fica fora de todas as campanhas. Avisos obrigatórios (cobrança,
            convocação) continuam sendo enviados.
          </p>
          {descadastros.length === 0 ? (
            <div className="dashboard-empty">Ninguém se descadastrou.</div>
          ) : (
            <div className="list-stack">
              {descadastros.map((d) => (
                <div key={d.id} className="list-card">
                  <div>
                    <p className="list-card-title">{d.email}</p>
                    <p className="list-card-meta">
                      {dataCurta(d.created_at)}
                      {d.campanha_assunto && ` · pela campanha “${d.campanha_assunto}”`}
                    </p>
                  </div>
                  {editavel && (
                    <button type="button" className="dashboard-btn-secondary" onClick={() => reativar(d)}>
                      Reativar
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
