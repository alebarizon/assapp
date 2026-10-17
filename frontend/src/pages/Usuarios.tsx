import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Mail, Pencil, Plus, Power, ShieldCheck, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import type { PerfilAcesso } from "@/types";
import type { ConvitePayload, PerfisInfo, UsuarioEquipe } from "@/types/equipe";
import {
  atualizarUsuario,
  convidarUsuario,
  getPerfisInfo,
  listEquipe,
  reenviarConvite,
} from "@/services/equipe";
import { apiErrorMessage } from "@/utils/apiError";
import { PERFIL_DESCRICAO, PERFIL_LABEL } from "@/utils/modulos";
import "@/components/usuarios/Usuarios.css";

const PERFIS: PerfilAcesso[] = ["gestor", "diretoria", "administrativo", "financeiro"];

const CONVITE_VAZIO: ConvitePayload = { email: "", first_name: "", last_name: "", perfis: [] };

function formatData(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

function PerfisCheckboxes({
  value,
  onChange,
  sugeridos = [],
}: {
  value: PerfilAcesso[];
  onChange: (perfis: PerfilAcesso[]) => void;
  sugeridos?: PerfilAcesso[];
}) {
  const toggle = (p: PerfilAcesso) =>
    onChange(value.includes(p) ? value.filter((x) => x !== p) : [...value, p]);
  return (
    <div className="us-perfis-grid">
      {PERFIS.map((p) => (
        <label key={p} className={`inline-check us-perfil-opcao${value.includes(p) ? " us-perfil-opcao-on" : ""}`}>
          <input type="checkbox" checked={value.includes(p)} onChange={() => toggle(p)} />
          <span>
            <strong>{PERFIL_LABEL[p]}</strong>
            {sugeridos.includes(p) && <span className="us-sugerido">sugerido pelo cargo</span>}
            <span className="us-perfil-desc">{PERFIL_DESCRICAO[p]}</span>
          </span>
        </label>
      ))}
    </div>
  );
}

export default function Usuarios() {
  const { user: eu, refreshUser } = useAuth();
  const [usuarios, setUsuarios] = useState<UsuarioEquipe[]>([]);
  const [info, setInfo] = useState<PerfisInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [showConvite, setShowConvite] = useState(false);
  const [convite, setConvite] = useState<ConvitePayload>(CONVITE_VAZIO);
  const [salvando, setSalvando] = useState(false);
  const [editando, setEditando] = useState<UsuarioEquipe | null>(null);
  const [perfisEdit, setPerfisEdit] = useState<PerfilAcesso[]>([]);
  const [erroEdicao, setErroEdicao] = useState("");
  const [showMatriz, setShowMatriz] = useState(false);

  const load = async () => {
    try {
      const [lista, perfis] = await Promise.all([listEquipe(), info ? Promise.resolve(info) : getPerfisInfo()]);
      setUsuarios(lista);
      setInfo(perfis);
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao carregar usuários."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const avisar = (msg: string) => {
    setErro("");
    setSucesso(msg);
  };

  const enviarConvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (convite.perfis.length === 0) {
      setErro("Selecione ao menos um perfil.");
      return;
    }
    setSalvando(true);
    try {
      const novo = await convidarUsuario(convite);
      avisar(
        novo.email_enviado
          ? `Convite enviado para ${novo.email}.`
          : `${novo.email} foi adicionado, mas o e-mail não pôde ser enviado. Use “Reenviar convite”.`
      );
      setConvite(CONVITE_VAZIO);
      setShowConvite(false);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao convidar usuário."));
    } finally {
      setSalvando(false);
    }
  };

  const abrirEdicao = (u: UsuarioEquipe) => {
    setEditando(u);
    setPerfisEdit(u.perfis);
    setErroEdicao("");
  };

  const fecharEdicao = () => {
    setEditando(null);
    setErroEdicao("");
  };

  const salvarPerfis = async () => {
    if (!editando) return;
    if (perfisEdit.length === 0) {
      setErroEdicao("Selecione ao menos um perfil.");
      return;
    }
    setSalvando(true);
    try {
      await atualizarUsuario(editando.id, { perfis: perfisEdit });
      avisar(`Perfis de ${editando.nome} atualizados.`);
      if (editando.is_self) await refreshUser();
      fecharEdicao();
      await load();
    } catch (err) {
      setErroEdicao(apiErrorMessage(err, "Erro ao atualizar perfis."));
    } finally {
      setSalvando(false);
    }
  };

  const alternarAtivo = async (u: UsuarioEquipe) => {
    const acao = u.is_active ? "desativar" : "reativar";
    if (u.is_active && !window.confirm(`Desativar o acesso de ${u.nome}? A pessoa não conseguirá mais entrar.`)) return;
    try {
      await atualizarUsuario(u.id, { is_active: !u.is_active });
      avisar(u.is_active ? `${u.nome} foi desativado.` : `${u.nome} foi reativado.`);
      await load();
    } catch (err) {
      setErro(apiErrorMessage(err, `Erro ao ${acao} usuário.`));
    }
  };

  const reenviar = async (u: UsuarioEquipe) => {
    try {
      const r = await reenviarConvite(u.id);
      avisar(r.email_enviado ? `Convite reenviado para ${u.email}.` : "Não foi possível enviar o e-mail agora.");
    } catch (err) {
      setErro(apiErrorMessage(err, "Erro ao reenviar convite."));
    }
  };

  const ativos = usuarios.filter((u) => u.is_active);
  const inativos = usuarios.filter((u) => !u.is_active);

  const renderUsuario = (u: UsuarioEquipe) => (
    <div key={u.id} className={`list-card us-card${u.is_active ? "" : " us-card-inativo"}`}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="list-card-title" style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          {u.nome}
          {u.is_self && <span className="us-voce">você</span>}
          {u.perfis.map((p) => (
            <span key={p} className={`us-perfil-chip us-perfil-${p}`}>
              {PERFIL_LABEL[p]}
            </span>
          ))}
        </div>
        <div className="list-card-meta" style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <span>{u.email}</span>
          {u.cargos.length > 0 && <span>Cargo: {u.cargos.join(", ")}</span>}
          <span>Último acesso: {formatData(u.last_login)}</span>
        </div>
      </div>
      {!u.is_active ? (
        <span className="status-badge status-badge-inativa">Inativo</span>
      ) : u.convite_pendente ? (
        <span className="status-badge status-badge-pendente">Convite pendente</span>
      ) : (
        <span className="status-badge status-badge-ativo">Ativo</span>
      )}
      <div className="us-acoes">
        {u.is_active && (
          <button type="button" className="us-icon-btn" title="Editar perfis" onClick={() => abrirEdicao(u)}>
            <Pencil size={15} />
          </button>
        )}
        {u.is_active && u.convite_pendente && (
          <button type="button" className="us-icon-btn" title="Reenviar convite" onClick={() => reenviar(u)}>
            <Mail size={15} />
          </button>
        )}
        {!u.is_self && (
          <button
            type="button"
            className="us-icon-btn"
            title={u.is_active ? "Desativar acesso" : "Reativar acesso"}
            onClick={() => alternarAtivo(u)}
          >
            <Power size={15} />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="dashboard-page">
      <div className="dashboard-header dashboard-header-row">
        <div>
          <h1 className="dashboard-title">Usuários e perfis</h1>
          <p className="dashboard-subtitle">
            Quem acessa o painel da associação e o que cada pessoa pode fazer. Uma pessoa pode ter mais de um perfil.
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button type="button" className="dashboard-btn-secondary" onClick={() => setShowMatriz((v) => !v)}>
            <ShieldCheck size={16} /> O que cada perfil acessa
          </button>
          <button type="button" className="dashboard-btn-new" onClick={() => setShowConvite((v) => !v)}>
            <Plus size={16} /> Convidar usuário
          </button>
        </div>
      </div>

      {erro && (
        <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem" }}>
          <AlertCircle size={16} /> {erro}
        </div>
      )}
      {sucesso && (
        <div className="alert-banner alert-banner-success" style={{ display: "flex", gap: "0.5rem" }}>
          <CheckCircle2 size={16} /> {sucesso}
        </div>
      )}

      {showMatriz && info && (
        <div className="dashboard-content-panel" style={{ marginBottom: "1.5rem", overflowX: "auto" }}>
          <table className="us-matriz">
            <thead>
              <tr>
                <th>Módulo</th>
                {info.perfis.map((p) => (
                  <th key={p.value}>{p.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {info.modulos.map((m) => (
                <tr key={m.value}>
                  <td>{m.label}</td>
                  {info.perfis.map((p) => {
                    const nivel = info.matriz[p.value]?.[m.value];
                    return (
                      <td key={p.value} className={`us-nivel us-nivel-${nivel || "nenhum"}`}>
                        {nivel === "total" ? "Total" : nivel === "leitura" ? "Consulta" : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showConvite && (
        <div className="page-form-container">
          <form className="page-form" onSubmit={enviarConvite}>
            <p className="dashboard-subtitle" style={{ marginTop: 0 }}>
              A pessoa recebe um e-mail com link para definir a senha. Se o e-mail já for de um associado, ele passa a
              acessar também o painel com a senha que já usa.
            </p>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Nome</label>
                <input
                  className="form-input"
                  autoFocus
                  value={convite.first_name}
                  onChange={(e) => setConvite({ ...convite, first_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Sobrenome</label>
                <input
                  className="form-input"
                  value={convite.last_name}
                  onChange={(e) => setConvite({ ...convite, last_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">E-mail *</label>
                <input
                  className="form-input"
                  type="email"
                  required
                  value={convite.email}
                  onChange={(e) => setConvite({ ...convite, email: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Perfis *</label>
              <PerfisCheckboxes value={convite.perfis} onChange={(perfis) => setConvite({ ...convite, perfis })} />
            </div>
            <div className="form-actions">
              <button type="button" className="dashboard-btn-cancel" onClick={() => setShowConvite(false)}>
                Cancelar
              </button>
              <button type="submit" className="dashboard-btn-save" disabled={salvando}>
                {salvando ? "Enviando..." : "Enviar convite"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="dashboard-loading">
          <div className="loading-spinner" />
          <p>Carregando...</p>
        </div>
      ) : (
        <>
          <div className="list-stack">{ativos.map(renderUsuario)}</div>
          {inativos.length > 0 && (
            <>
              <h2 className="us-secao" style={{ marginTop: "2rem" }}>
                Acessos desativados
              </h2>
              <div className="list-stack">{inativos.map(renderUsuario)}</div>
            </>
          )}
        </>
      )}

      {editando && (
        <div className="dashboard-modal-overlay" onClick={fecharEdicao}>
          <div className="dashboard-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560 }}>
            <div className="dashboard-modal-header">
              <h2 className="dashboard-modal-title">Perfis de {editando.nome}</h2>
              <button type="button" className="dashboard-modal-close" onClick={fecharEdicao} aria-label="Fechar">
                <X size={18} />
              </button>
            </div>
            <div className="dashboard-modal-content page-form">
              {erroEdicao && (
                <div className="alert-banner alert-banner-error" style={{ display: "flex", gap: "0.5rem", marginTop: 0 }}>
                  <AlertCircle size={16} /> {erroEdicao}
                </div>
              )}
              {editando.cargos.length > 0 && (
                <p className="dashboard-subtitle" style={{ marginTop: 0 }}>
                  Cargo no mandato atual: <strong>{editando.cargos.join(", ")}</strong>.
                  {editando.perfis_sugeridos.length > 0 && (
                    <>
                      {" "}
                      Sugestão:{" "}
                      <button
                        type="button"
                        className="us-link-btn"
                        onClick={() => setPerfisEdit(editando.perfis_sugeridos)}
                      >
                        usar {editando.perfis_sugeridos.map((p) => PERFIL_LABEL[p]).join(" + ")}
                      </button>
                    </>
                  )}
                </p>
              )}
              {editando.is_self && (
                <p className="list-card-meta" style={{ marginTop: 0 }}>
                  Atenção: ao remover seu perfil de gestor você perde o acesso a esta página.
                </p>
              )}
              <PerfisCheckboxes value={perfisEdit} onChange={setPerfisEdit} sugeridos={editando.perfis_sugeridos} />
            </div>
            <div className="dashboard-modal-footer">
              <button type="button" className="dashboard-btn-secondary" onClick={fecharEdicao}>
                Cancelar
              </button>
              <button type="button" className="dashboard-btn-new" disabled={salvando} onClick={salvarPerfis}>
                {salvando ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {eu && !loading && usuarios.length === 1 && (
        <div className="dashboard-empty" style={{ marginTop: "1.5rem" }}>
          Só você acessa o painel por enquanto. Convide a secretaria, a tesouraria e os demais diretores.
        </div>
      )}
    </div>
  );
}
