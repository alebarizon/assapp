import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BookOpen, Download, Lock, ShoppingCart } from "lucide-react";
import { addToCart } from "@/services/ecommerce";
import { baixarMinhaPublicacao, listMinhasPublicacoes } from "@/services/publicacoes";
import type { MinhaPublicacao } from "@/types/publicacoes";
import { apiErrorMessage } from "@/utils/apiError";
import { formatBRL } from "@/utils/tenantSite";
import "@/components/publicacoes/Publicacoes.css";

export default function MinhasPublicacoes() {
  const navigate = useNavigate();
  const [itens, setItens] = useState<MinhaPublicacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState<string | null>(null);

  useEffect(() => {
    listMinhasPublicacoes()
      .then(setItens)
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar publicações.")))
      .finally(() => setLoading(false));
  }, []);

  const baixar = async (p: MinhaPublicacao) => {
    setOcupado(p.id);
    setErro("");
    try {
      await baixarMinhaPublicacao(p.id);
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível baixar."));
    } finally {
      setOcupado(null);
    }
  };

  const comprar = async (p: MinhaPublicacao) => {
    if (!p.catalog_item) return;
    setOcupado(p.id);
    setErro("");
    try {
      await addToCart(p.catalog_item);
      navigate("/app/portal/carrinho");
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível adicionar ao carrinho."));
      setOcupado(null);
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
      <div className="dashboard-header">
        <h1 className="dashboard-title">Publicações</h1>
        <p className="dashboard-subtitle">Dossiês, e-books e boletins da associação</p>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}

      {itens.length === 0 ? (
        <div className="dashboard-content-panel">
          <div className="dashboard-empty">Nenhuma publicação disponível ainda.</div>
        </div>
      ) : (
        <div className="pub-grid">
          {itens.map((p) => (
            <div key={p.id} className="pub-card">
              <div className="pub-capa" style={p.capa_url ? { backgroundImage: `url(${p.capa_url})` } : undefined}>
                {!p.capa_url && <BookOpen size={40} />}
              </div>
              <div className="pub-corpo">
                <span className={`status-badge status-badge-${p.liberado ? "ativa" : "pendente"}`} style={{ alignSelf: "flex-start" }}>
                  {p.motivo_display}
                </span>
                <p className="pub-titulo">{p.titulo}</p>
                <p className="pub-meta">
                  {p.tipo_display}
                  {p.ano ? ` · ${p.ano}` : ""}
                  {p.autores.length > 0 && ` · ${p.autores.map((a) => a.nome).join(", ")}`}
                </p>
                {p.resumo && (
                  <p className="pub-meta" style={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {p.resumo}
                  </p>
                )}
                <div className="pub-acoes">
                  {p.liberado ? (
                    p.tem_arquivo ? (
                      <button type="button" className="dashboard-btn-new" disabled={ocupado === p.id} onClick={() => void baixar(p)}>
                        <Download size={14} /> Baixar
                      </button>
                    ) : (
                      <span className="pub-meta">Arquivo em preparação</span>
                    )
                  ) : (
                    <>
                      {p.catalog_item && (
                        <button type="button" className="dashboard-btn-new" disabled={ocupado === p.id} onClick={() => void comprar(p)}>
                          <ShoppingCart size={14} /> Comprar {p.preco_final && formatBRL(p.preco_final)}
                        </button>
                      )}
                      {p.motivo === "requer_adimplencia" && (
                        <Link to="/app/portal/perfil" className="dashboard-btn-secondary">
                          <Lock size={14} /> Regularizar anuidade
                        </Link>
                      )}
                    </>
                  )}
                </div>
                {!p.liberado && p.preco_socio && p.preco && p.preco_final === p.preco && (
                  <p className="pub-meta">Sócio em dia paga {formatBRL(p.preco_socio)}.</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
