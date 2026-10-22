import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RotateCcw, Send, Users } from "lucide-react";
import {
  listEnviosRegua,
  listReguas,
  previaRegua,
  restaurarRegua,
  salvarRegua,
  testarRegua,
} from "@/services/newsletter";
import {
  REGUA_INFO,
  type EnvioRegua,
  type ListaReguas,
  type PreviaRegua,
  type Regua,
  type TipoRegua,
} from "@/types/newsletter";
import { apiErrorMessage } from "@/utils/apiError";

const ORDEM: TipoRegua[] = ["boas_vindas", "inativos", "autor_nao_socio"];

function dataCurta(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function ReguaCard({
  regua,
  editavel,
  limite,
  onSalva,
}: {
  regua: Regua;
  editavel: boolean;
  limite: number;
  onSalva: (r: Regua) => void;
}) {
  const info = REGUA_INFO[regua.tipo];
  const [form, setForm] = useState({ assunto: regua.assunto, corpo: regua.corpo, dias: regua.dias });
  const [previa, setPrevia] = useState<PreviaRegua>();
  const [ocupado, setOcupado] = useState(false);
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  useEffect(() => {
    setForm({ assunto: regua.assunto, corpo: regua.corpo, dias: regua.dias });
  }, [regua]);

  const alterado = form.assunto !== regua.assunto || form.corpo !== regua.corpo || form.dias !== regua.dias;

  const executar = async (fn: () => Promise<void>) => {
    setOcupado(true);
    setErro("");
    setMsg("");
    try {
      await fn();
    } catch (err) {
      setErro(apiErrorMessage(err, "Não foi possível concluir."));
    } finally {
      setOcupado(false);
    }
  };

  const salvar = () =>
    executar(async () => {
      onSalva(await salvarRegua(regua.tipo, form));
      setPrevia(undefined);
      setMsg("Alterações salvas.");
    });

  const alternar = () =>
    executar(async () => {
      if (!regua.ativa) {
        const p = await previaRegua(regua.tipo);
        setPrevia(p);
        const excedente = p.total > limite ? ` (no máximo ${limite} por dia; o restante segue nos dias seguintes)` : "";
        if (!window.confirm(`Ativar “${regua.nome}”? Na próxima execução, ${p.total} pessoa(s) receberiam${excedente}.`)) return;
      }
      onSalva(await salvarRegua(regua.tipo, { ativa: !regua.ativa }));
    });

  const verPrevia = () => executar(async () => setPrevia(await previaRegua(regua.tipo)));

  const testar = () =>
    executar(async () => {
      if (alterado) onSalva(await salvarRegua(regua.tipo, form));
      const r = await testarRegua(regua.tipo);
      setMsg(`Teste enviado para ${r.enviado_para}.`);
    });

  const restaurar = () =>
    executar(async () => {
      if (!window.confirm("Voltar ao texto e prazo padrão desta régua?")) return;
      onSalva(await restaurarRegua(regua.tipo));
      setMsg("Texto padrão restaurado.");
    });

  return (
    <div className="dashboard-content-panel page-form">
      <div className="nl-regua-head">
        <div>
          <h2 className="nl-section-title">{regua.nome}</h2>
          <p className="nl-fonte-hint" style={{ marginTop: 0 }}>{info.gatilho(form.dias)}</p>
        </div>
        <span className={`status-badge status-badge-${regua.ativa ? "ativa" : "rascunho"}`}>
          {regua.ativa ? "Ativa" : "Desligada"}
        </span>
      </div>

      {erro && <div className="alert-banner alert-banner-error">{erro}</div>}
      {msg && <div className="alert-banner alert-banner-success">{msg}</div>}

      <div className="form-row">
        <div className="form-group" style={{ flex: 3 }}>
          <label className="form-label">Assunto</label>
          <input
            className="form-input"
            disabled={!editavel}
            value={form.assunto}
            onChange={(e) => setForm({ ...form, assunto: e.target.value })}
          />
        </div>
        <div className="form-group" style={{ flex: 1 }}>
          <label className="form-label">{info.diasLabel}</label>
          <input
            className="form-input"
            type="number"
            min={1}
            max={info.diasMax}
            disabled={!editavel}
            value={form.dias}
            onChange={(e) => setForm({ ...form, dias: Number(e.target.value) || 1 })}
          />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Texto</label>
        <textarea
          className="form-input"
          rows={8}
          disabled={!editavel}
          value={form.corpo}
          onChange={(e) => setForm({ ...form, corpo: e.target.value })}
        />
        <p className="nl-fonte-hint">
          Variáveis: {"{nome}"} (primeiro nome), {"{associacao}"}, {"{proximo_evento}"}
          {regua.tipo === "autor_nao_socio" && <>, {"{trabalho}"}, {"{evento}"}</>}.
          {regua.tipo === "boas_vindas"
            ? " Mensagem de filiação: vai mesmo para quem se descadastrou da newsletter."
            : " Leva o link “não quero mais receber” e respeita os descadastros."}
        </p>
      </div>

      <p className="list-card-meta">
        Enviados: {regua.enviados_30_dias} nos últimos 30 dias · {regua.enviados_total} no total
      </p>

      {previa && (
        <div className="nl-fonte">
          <div className="nl-total">
            <strong>{previa.total}</strong> pessoa(s) receberiam na próxima execução
          </div>
          {previa.amostra.length > 0 && (
            <ul className="nl-amostra">
              {previa.amostra.map((p) => (
                <li key={p.email}>
                  {p.nome || p.email} · {p.email}
                  {p.detalhe && ` · ${p.detalhe}`}
                </li>
              ))}
              {previa.total > previa.amostra.length && <li>e mais {previa.total - previa.amostra.length}…</li>}
            </ul>
          )}
        </div>
      )}

      <div className="nl-regua-acoes">
        {editavel && (
          <button type="button" className="dashboard-btn-new" disabled={ocupado} onClick={alternar}>
            {regua.ativa ? "Desligar" : "Ativar"}
          </button>
        )}
        {editavel && (
          <button type="button" className="dashboard-btn-secondary" disabled={ocupado || !alterado} onClick={salvar}>
            Salvar texto
          </button>
        )}
        <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={verPrevia}>
          <Users size={14} /> Quem receberia hoje
        </button>
        {editavel && (
          <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={testar}>
            <Send size={14} /> Enviar teste para mim
          </button>
        )}
        {editavel && (
          <button type="button" className="dashboard-btn-secondary" disabled={ocupado} onClick={restaurar}>
            <RotateCcw size={14} /> Texto padrão
          </button>
        )}
      </div>
    </div>
  );
}

export default function ReguasPanel({ editavel }: { editavel: boolean }) {
  const [dados, setDados] = useState<ListaReguas>();
  const [envios, setEnvios] = useState<EnvioRegua[]>([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    Promise.all([listReguas(), listEnviosRegua()])
      .then(([d, e]) => {
        setDados(d);
        setEnvios(e);
      })
      .catch((err) => setErro(apiErrorMessage(err, "Erro ao carregar as réguas.")));
  }, []);

  if (erro) return <div className="alert-banner alert-banner-error">{erro}</div>;
  if (!dados) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner" />
      </div>
    );
  }

  const atualizar = (r: Regua) =>
    setDados((d) => d && { ...d, reguas: d.reguas.map((x) => (x.tipo === r.tipo ? r : x)) });

  return (
    <div className="list-stack">
      <p className="list-card-meta" style={{ marginTop: 0 }}>
        E-mails automáticos enviados uma vez por dia, a partir das {dados.hora}h, para quem entra na regra de cada
        régua. Ninguém recebe a mesma mensagem duas vezes.
      </p>
      {!dados.email_entregue && (
        <div className="alert-banner alert-banner-info">
          O servidor ainda não tem um provedor de e-mail configurado: as réguas ficam paradas (nada é enviado nem
          registrado) até ele ser configurado. Já dá para preparar os textos e ver quem receberia.
        </div>
      )}

      {[...dados.reguas].sort((a, b) => ORDEM.indexOf(a.tipo) - ORDEM.indexOf(b.tipo)).map((r) => (
        <ReguaCard key={r.tipo} regua={r} editavel={editavel} limite={dados.limite_por_dia} onSalva={atualizar} />
      ))}

      <div className="dashboard-content-panel">
        <h2 className="nl-section-title">Últimos envios automáticos</h2>
        {envios.length === 0 ? (
          <div className="dashboard-empty">Nenhum e-mail automático enviado ainda.</div>
        ) : (
          <div className="list-stack">
            {envios.map((e) => (
              <div key={e.id} className="list-card">
                <div>
                  <p className="list-card-title">
                    {e.membro ? <Link to={`/app/membros/${e.membro}`}>{e.nome || e.email}</Link> : e.nome || e.email}
                  </p>
                  <p className="list-card-meta">
                    {e.tipo_nome} · {e.email} · {dataCurta(e.enviado_em)}
                    {e.detalhe && ` · ${e.detalhe}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
