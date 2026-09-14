import { useEffect, useState } from "react";
import { Truck, Plug, Save, RefreshCw, Power, Activity, PlayCircle, History, RotateCcw, AlertTriangle, FlaskConical, CheckCircle2, XCircle, Circle } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const STATUS = {
  not_configured: ["Não configurado", "text-gray-400 bg-gray-500/10"],
  connected: ["Conectado", "text-[#009B3A] bg-[#009B3A]/10"],
  unavailable: ["Indisponível", "text-[#FFC107] bg-[#FFC107]/10"],
  error: ["Erro", "text-red-400 bg-red-500/10"],
};

export default function AdminSuperFrete() {
  const [c, setC] = useState(null);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api.get("/admin/superfrete/config").then((r) => setC(r.data));
  useEffect(() => { load(); }, []);
  if (!c) return <div className="text-gray-400">Carregando...</div>;

  const set = (k, v) => setC((s) => ({ ...s, [k]: v }));
  const inp = "w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";
  const [statusLabel, statusCls] = STATUS[c.status] || STATUS.not_configured;

  const save = async () => {
    setBusy(true);
    try {
      const payload = { ...c };
      if (token.trim()) payload.token = token.trim();
      payload.enabled_services = (Array.isArray(c.enabled_services) ? c.enabled_services : String(c.enabled_services || "").split(",")).map((x) => String(x).trim()).filter(Boolean);
      const { data } = await api.put("/admin/superfrete/config", payload);
      setC(data); setToken(""); toast.success("Configuração salva");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const test = async () => {
    setBusy(true);
    try { const { data } = await api.post("/admin/superfrete/test"); setC((s) => ({ ...s, ...data })); toast.success(`Status: ${data.status}`); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); load(); }
    finally { setBusy(false); }
  };
  const disconnect = async () => {
    if (!window.confirm("Desativar a SuperFrete? (as configurações são preservadas)")) return;
    try { await api.post("/admin/superfrete/disconnect"); toast.success("SuperFrete desativada"); load(); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const F = ({ label, k, ph, cls }) => (
    <div className={cls}><label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input value={c[k] ?? ""} onChange={(e) => set(k, e.target.value)} placeholder={ph} data-testid={`sf-${k}`} className={inp} /></div>
  );

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-3 mb-2"><Truck className="text-[#FFC107]" size={28} /><h1 className="text-3xl font-display font-black uppercase text-white">SuperFrete</h1>
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${statusCls}`} data-testid="sf-status">{statusLabel}</span>
        <span className="text-xs px-2 py-1 rounded-full bg-[#1E3A8A]/20 text-[#8fb0ff]">PRINCIPAL</span>
      </div>
      <p className="text-gray-500 text-sm mb-6">Provider logístico principal. O Melhor Envio permanece como legado.</p>

      <div className="bm-card p-6 space-y-4" data-testid="superfrete-config">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="text-xs text-gray-500 block mb-1">Ambiente</label>
            <select value={c.environment} onChange={(e) => set("environment", e.target.value)} data-testid="sf-environment" className={inp}>
              <option value="sandbox">Sandbox (teste)</option><option value="production">Produção</option>
            </select>
          </div>
          <label className="flex items-end gap-2 pb-2 text-sm text-white cursor-pointer">
            <input type="checkbox" checked={!!c.is_enabled} onChange={(e) => set("is_enabled", e.target.checked)} data-testid="sf-enabled" className="accent-[#FFC107] h-4 w-4" />
            Ativa como provider principal
          </label>
        </div>

        <div>
          <label className="text-xs text-gray-500 block mb-1">Token de integração {c.has_token && <span className="text-gray-600">(atual: {c.token_masked})</span>}</label>
          <input value={token} onChange={(e) => setToken(e.target.value)} placeholder={c.has_token ? "Deixe em branco para manter o atual" : "Cole o token da SuperFrete"} data-testid="sf-token" className={inp} />
          <p className="text-[11px] text-gray-600 mt-1">O token é criptografado e nunca é exibido por completo. Obtenha em Integrações → Desenvolvedores no painel SuperFrete.</p>
        </div>

        <p className="text-xs font-bold text-gray-400 uppercase pt-2 border-t border-[#2e2e2e]">Remetente</p>
        <div className="grid grid-cols-2 gap-4">
          <F label="Nome" k="sender_name" />
          <F label="E-mail (User-Agent)" k="sender_email" />
          <F label="Documento (CPF/CNPJ)" k="sender_document" />
          <F label="Telefone" k="sender_phone" />
          <F label="CEP de origem" k="sender_postal_code" ph="00000000" />
          <F label="Endereço" k="sender_address" />
          <F label="Número" k="sender_number" />
          <F label="Complemento" k="sender_complement" />
          <F label="Bairro" k="sender_district" />
          <F label="Cidade" k="sender_city" />
          <F label="UF" k="sender_state" />
        </div>

        <p className="text-xs font-bold text-gray-400 uppercase pt-2 border-t border-[#2e2e2e]">Padrões de pacote (fallback)</p>
        <div className="grid grid-cols-4 gap-3">
          <F label="Peso (kg)" k="default_weight" />
          <F label="Largura (cm)" k="default_width" />
          <F label="Altura (cm)" k="default_height" />
          <F label="Comprim. (cm)" k="default_length" />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Serviços habilitados (IDs, separados por vírgula)</label>
          <input value={Array.isArray(c.enabled_services) ? c.enabled_services.join(",") : (c.enabled_services || "")} onChange={(e) => set("enabled_services", e.target.value.split(","))} data-testid="sf-services" placeholder="1,2,17" className={inp} />
        </div>

        <p className="text-xs font-bold text-gray-400 uppercase pt-2 border-t border-[#2e2e2e]">Rollout (liberação gradual)</p>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="text-xs text-gray-500 block mb-1">Modo</label>
            <select value={c.rollout_mode || "ENABLED"} onChange={(e) => set("rollout_mode", e.target.value)} data-testid="sf-rollout-mode" className={inp}>
              <option value="DISABLED">Desligado (só Melhor Envio)</option>
              <option value="TEST_ORDER_ONLY">Somente pedido de teste</option>
              <option value="ADMIN_ONLY">Somente admin</option>
              <option value="PERCENTAGE">Percentual de clientes</option>
              <option value="ENABLED">Todos os clientes</option>
            </select>
          </div>
          {c.rollout_mode === "PERCENTAGE" && (
            <div><label className="text-xs text-gray-500 block mb-1">Percentual (%)</label>
              <input type="number" min={0} max={100} value={c.rollout_percentage ?? 0} onChange={(e) => set("rollout_percentage", e.target.value)} data-testid="sf-rollout-pct" className={inp} />
            </div>
          )}
        </div>
        <p className="text-[11px] text-gray-600">Em <b>Desligado</b> e <b>Somente pedido de teste</b>, o checkout público continua no Melhor Envio. Rollback para “Desligado” é imediato para novos pedidos; envios já criados seguem sendo acompanhados.</p>

        <div className="flex flex-wrap gap-3 pt-2">
          <button onClick={save} disabled={busy} data-testid="sf-save" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-2.5 flex items-center gap-2"><Save size={16} /> Salvar</button>
          <button onClick={test} disabled={busy} data-testid="sf-test" className="border border-[#1E3A8A] text-[#8fb0ff] font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Plug size={16} /> Testar conexão</button>
          <button onClick={load} disabled={busy} className="border border-[#2e2e2e] text-gray-300 rounded-full px-4 py-2.5 flex items-center gap-2"><RefreshCw size={15} /> Recarregar</button>
          {c.is_enabled && <button onClick={disconnect} data-testid="sf-disconnect" className="border border-red-500/40 text-red-400 rounded-full px-4 py-2.5 flex items-center gap-2 ml-auto"><Power size={15} /> Desativar</button>}
        </div>
        {c.last_error && <p className="text-xs text-red-400" data-testid="sf-last-error">Último erro: {c.last_error}</p>}
      </div>

      <SuperFreteSyncPanel />
      <ControlledTestPanel />
    </div>
  );
}

function fmtDate(s) {
  if (!s) return "—";
  try { return new Date(s).toLocaleString("pt-BR"); } catch { return s; }
}

function SuperFreteSyncPanel() {
  const [st, setSt] = useState(null);
  const [runs, setRuns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [showHist, setShowHist] = useState(false);

  const load = () => api.get("/admin/superfrete/sync/status").then((r) => setSt(r.data)).catch(() => {});
  const loadRuns = () => api.get("/admin/superfrete/sync/runs?limit=20").then((r) => setRuns(r.data.runs || [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const runNow = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/superfrete/sync/run");
      if (data.status === "skipped_locked") toast.warning("Ciclo não executado: sincronização suspensa/desativada ou já em execução.");
      else toast.success(`Ciclo concluído: ${data.updated} atualizado(s), ${data.unchanged} sem mudança, ${data.failed} falha(s).`);
      load(); if (showHist) loadRuns();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const reprocess = async () => {
    setBusy(true);
    try { const { data } = await api.post("/admin/superfrete/sync/reprocess-failures"); toast.success(`${data.reprocessed} envio(s) reprogramado(s).`); load(); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const toggleHist = () => { const n = !showHist; setShowHist(n); if (n) loadRuns(); };

  if (!st) return null;
  const lr = st.last_run;
  const box = "bg-[#111] border border-[#2e2e2e] rounded-lg p-3";
  const K = ({ label, value, cls }) => (
    <div className={box}><p className="text-[11px] text-gray-500">{label}</p><p className={`text-sm font-bold ${cls || "text-white"}`}>{value}</p></div>
  );

  return (
    <div className="bm-card p-6 space-y-4 mt-6" data-testid="superfrete-sync-panel">
      <div className="flex items-center gap-3">
        <Activity className="text-[#009B3A]" size={22} />
        <h2 className="text-xl font-display font-black uppercase text-white">Sincronização automática</h2>
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${st.scheduler_running ? "text-[#009B3A] bg-[#009B3A]/10" : "text-gray-400 bg-gray-500/10"}`} data-testid="sf-sync-scheduler">
          {st.scheduler_running ? "Ativo" : "Parado"}
        </span>
      </div>
      <p className="text-gray-500 text-xs">Fonte automática de atualização por consulta (polling). Webhook não é usado: a documentação oficial não define assinatura verificável.</p>

      {st.sync_suspended && (
        <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/30 rounded-lg p-3" data-testid="sf-sync-suspended">
          <AlertTriangle className="text-red-400 shrink-0" size={18} />
          <div className="text-sm text-red-300">
            <p className="font-bold">Sincronização suspensa</p>
            <p className="text-xs text-red-400/90">{st.sync_suspended_reason || "Autenticação inválida."} Atualize o token e clique em “Testar conexão” para reativar.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <K label="Autenticação" value={st.auth_valid ? "Válida" : "Inválida"} cls={st.auth_valid ? "text-[#009B3A]" : "text-red-400"} />
        <K label="Ciclo" value={`${st.cycle_seconds}s`} />
        <K label="Envios ativos" value={st.active_shipments} />
        <K label="Sync habilitada" value={st.sync_enabled ? "Sim" : "Não"} cls={st.sync_enabled ? "text-white" : "text-[#FFC107]"} />
      </div>

      <div className="border-t border-[#2e2e2e] pt-3">
        <p className="text-xs font-bold text-gray-400 uppercase mb-2">Última execução</p>
        {lr ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="sf-sync-lastrun">
            <K label="Quando" value={fmtDate(lr.started_at)} />
            <K label="Gatilho" value={lr.trigger} />
            <K label="Status" value={lr.status} cls={lr.status === "ok" ? "text-[#009B3A]" : "text-[#FFC107]"} />
            <K label="Duração" value={`${lr.duration_ms ?? 0} ms`} />
            <K label="Processados" value={lr.processed} />
            <K label="Atualizados" value={lr.updated} cls="text-[#009B3A]" />
            <K label="Sem mudança" value={lr.unchanged} />
            <K label="Falhas" value={lr.failed} cls={lr.failed ? "text-red-400" : "text-white"} />
          </div>
        ) : <p className="text-sm text-gray-500">Nenhuma execução registrada ainda.</p>}
      </div>

      <div className="flex flex-wrap gap-3 pt-1">
        <button onClick={runNow} disabled={busy} data-testid="sf-sync-run" className="bg-[#009B3A] text-white font-bold rounded-full px-5 py-2.5 flex items-center gap-2 disabled:opacity-50"><PlayCircle size={16} /> Sincronizar agora</button>
        <button onClick={reprocess} disabled={busy} data-testid="sf-sync-reprocess" className="border border-[#FFC107]/50 text-[#FFC107] font-semibold rounded-full px-5 py-2.5 flex items-center gap-2 disabled:opacity-50"><RotateCcw size={15} /> Reprocessar falhas</button>
        <button onClick={toggleHist} data-testid="sf-sync-history" className="border border-[#2e2e2e] text-gray-300 rounded-full px-4 py-2.5 flex items-center gap-2"><History size={15} /> Histórico</button>
        <button onClick={load} disabled={busy} className="border border-[#2e2e2e] text-gray-300 rounded-full px-4 py-2.5 flex items-center gap-2 ml-auto"><RefreshCw size={15} /> Atualizar</button>
      </div>

      {showHist && (
        <div className="border-t border-[#2e2e2e] pt-3 overflow-x-auto" data-testid="sf-sync-runs">
          <table className="w-full text-xs">
            <thead><tr className="text-gray-500 text-left">
              <th className="py-1 pr-3">Quando</th><th className="pr-3">Gatilho</th><th className="pr-3">Status</th>
              <th className="pr-3">Proc.</th><th className="pr-3">Atual.</th><th className="pr-3">S/mud.</th><th className="pr-3">Falhas</th><th>Duração</th>
            </tr></thead>
            <tbody>
              {runs.length === 0 && <tr><td colSpan={8} className="py-2 text-gray-600">Sem execuções.</td></tr>}
              {runs.map((r) => (
                <tr key={r.id} className="text-gray-300 border-t border-[#1e1e1e]">
                  <td className="py-1.5 pr-3">{fmtDate(r.started_at)}</td><td className="pr-3">{r.trigger}</td>
                  <td className={`pr-3 ${r.status === "ok" ? "text-[#009B3A]" : "text-[#FFC107]"}`}>{r.status}</td>
                  <td className="pr-3">{r.processed}</td><td className="pr-3">{r.updated}</td>
                  <td className="pr-3">{r.unchanged}</td><td className={`pr-3 ${r.failed ? "text-red-400" : ""}`}>{r.failed}</td>
                  <td>{r.duration_ms ?? 0} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const CHECK_LABELS = [
  ["token_valid", "Token válido"],
  ["connection_ok", "Conexão OK"],
  ["quote_returned", "Cotação retornada"],
  ["service_selected", "Serviço selecionado"],
  ["shipment_created", "Envio criado"],
  ["label_available", "Etiqueta disponível"],
  ["tracking_received", "Tracking recebido"],
  ["polling_synced", "Polling sincronizou"],
  ["idempotency_validated", "Idempotência validada"],
  ["no_critical_error", "Nenhum erro crítico"],
  ["melhor_envio_intact", "Melhor Envio intacto"],
];

const CT_STATUS = {
  PENDING: ["VALIDAÇÃO PENDENTE", "text-gray-400 bg-gray-500/10"],
  PARTIAL: ["VALIDAÇÃO PARCIAL", "text-[#FFC107] bg-[#FFC107]/10"],
  APPROVED: ["VALIDAÇÃO APROVADA", "text-[#009B3A] bg-[#009B3A]/10"],
  FAILED: ["VALIDAÇÃO REPROVADA", "text-red-400 bg-red-500/10"],
};

function ControlledTestPanel() {
  const [st, setSt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [p, setP] = useState({ origin_postal_code: "", dest_postal_code: "", weight: "0.3", width: "16", height: "6", length: "20", insurance_value: "0", product_name: "Miniatura de teste" });
  const [track, setTrack] = useState("");

  const load = () => api.get("/admin/superfrete/controlled-test").then((r) => setSt(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const call = async (fn, confirmMsg) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    setBusy(true);
    try { const { data } = await fn(); setSt(data); return data; }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); load(); }
    finally { setBusy(false); }
  };

  const inp = "w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";
  if (!st) return null;
  const ck = st.checklist || {};
  const [slabel, scls] = CT_STATUS[st.status] || CT_STATUS.PENDING;
  const setP2 = (k, v) => setP((s) => ({ ...s, [k]: v }));

  const saveParams = () => call(() => api.post("/admin/superfrete/controlled-test/params", {
    ...p, weight: Number(p.weight), width: Number(p.width), height: Number(p.height),
    length: Number(p.length), insurance_value: Number(p.insurance_value),
  })).then((d) => d && toast.success("Parâmetros salvos"));
  const conn = () => call(() => api.post("/admin/superfrete/controlled-test/connection")).then((d) => d && toast.success("Conexão OK"));
  const quote = () => call(() => api.post("/admin/superfrete/controlled-test/quote")).then((d) => d && toast.success("Cotação retornada"));
  const pick = (sid) => call(() => api.post("/admin/superfrete/controlled-test/select", { service_id: sid })).then((d) => d && toast.success("Serviço selecionado"));
  const create = () => call(() => api.post("/admin/superfrete/controlled-test/create"), "Criar o envio de TESTE controlado para este pedido de teste? Nenhum pedido real é afetado.").then((d) => d && toast.success("Envio de teste criado"));
  const consult = () => call(() => api.post("/admin/superfrete/controlled-test/consult")).then((d) => d && toast.success("Consulta feita"));
  const label = () => call(() => api.post("/admin/superfrete/controlled-test/label")).then((d) => d && toast.success("Etiqueta verificada"));
  const capture = () => call(() => api.post("/admin/superfrete/controlled-test/tracking", { tracking_code: track.trim() })).then((d) => { if (d) { setTrack(""); toast.success("Rastreio capturado"); } });
  const doSync = () => call(() => api.post("/admin/superfrete/controlled-test/sync")).then((d) => d && toast.success("Sincronizado"));
  const finalize = () => call(() => api.post("/admin/superfrete/controlled-test/finalize")).then((d) => d && toast.success(`Status: ${d.status}`));
  const reset = () => call(() => api.post("/admin/superfrete/controlled-test/reset"), "Reiniciar o teste controlado? (limpa o checklist)").then((d) => d && toast.success("Teste reiniciado"));

  const F = ({ label, k, ph, type }) => (
    <div><label className="text-[11px] text-gray-500 block mb-1">{label}</label>
      <input type={type || "text"} value={p[k]} onChange={(e) => setP2(k, e.target.value)} placeholder={ph} data-testid={`ct-${k}`} className={inp} /></div>
  );
  const btn = "text-xs font-semibold rounded-full px-4 py-2 border border-[#2e2e2e] text-gray-300 disabled:opacity-40";

  return (
    <div className="bm-card p-6 space-y-4 mt-6" data-testid="controlled-test-panel">
      <div className="flex items-center gap-3">
        <FlaskConical className="text-[#FFC107]" size={22} />
        <h2 className="text-xl font-display font-black uppercase text-white">Teste controlado</h2>
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${scls}`} data-testid="ct-status">{slabel}</span>
      </div>
      <p className="text-gray-500 text-xs">Valide a SuperFrete ponta a ponta com credencial real, sem afetar clientes. Cada etapa é disparada por você; conexão e cotação não criam envio.</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <F label="CEP origem" k="origin_postal_code" ph="01153000" />
        <F label="CEP destino" k="dest_postal_code" ph="20040002" />
        <F label="Peso (kg)" k="weight" type="number" />
        <F label="Valor declarado (R$)" k="insurance_value" type="number" />
        <F label="Largura (cm)" k="width" type="number" />
        <F label="Altura (cm)" k="height" type="number" />
        <F label="Comprimento (cm)" k="length" type="number" />
        <F label="Produto" k="product_name" />
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={saveParams} disabled={busy} data-testid="ct-params" className="text-xs font-bold rounded-full px-4 py-2 bg-[#1E3A8A] text-white disabled:opacity-40">1. Definir parâmetros</button>
        <button onClick={conn} disabled={busy} data-testid="ct-connection" className={btn}>2. Testar conexão</button>
        <button onClick={quote} disabled={busy} data-testid="ct-quote" className={btn}>3. Cotar</button>
        <button onClick={consult} disabled={busy} data-testid="ct-consult" className={btn}>Consultar</button>
        <button onClick={label} disabled={busy} data-testid="ct-label" className={btn}>Etiqueta</button>
        <button onClick={doSync} disabled={busy} data-testid="ct-sync" className={btn}>Sincronizar</button>
      </div>

      {(st.quote_options || []).length > 0 && (
        <div className="border border-[#2e2e2e] rounded-lg p-3" data-testid="ct-services">
          <p className="text-[11px] text-gray-500 mb-2">4. Escolha um serviço:</p>
          <div className="space-y-1.5">
            {st.quote_options.map((o) => {
              const sel = st.selected_service && String(st.selected_service.service_id) === String(o.service_id);
              return (
                <button key={o.service_id} onClick={() => pick(o.service_id)} disabled={busy} data-testid={`ct-svc-${o.service_id}`}
                  className={`w-full text-left text-xs rounded-lg px-3 py-2 border ${sel ? "border-[#009B3A] bg-[#009B3A]/10 text-white" : "border-[#2e2e2e] text-gray-300"}`}>
                  <span className="font-bold">{o.service_name}</span> · {o.company_name} · R$ {Number(o.price).toFixed(2)} · {o.delivery_max || o.estimated_days || "?"} dia(s)
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-end gap-2">
        <button onClick={create} disabled={busy || !ck.service_selected} data-testid="ct-create" className="text-xs font-bold rounded-full px-4 py-2 bg-[#FFC107] text-[#111] disabled:opacity-40">5. Criar envio (idempotente)</button>
        <div className="flex-1 min-w-[180px]">
          <label className="text-[11px] text-gray-500 block mb-1">Rastreio (emitido no painel)</label>
          <input value={track} onChange={(e) => setTrack(e.target.value)} data-testid="ct-track-input" placeholder="Código de rastreio" className={inp} />
        </div>
        <button onClick={capture} disabled={busy || !track.trim()} data-testid="ct-track-save" className="text-xs font-bold rounded-full px-4 py-2 bg-[#1E3A8A] text-white disabled:opacity-40">Capturar tracking</button>
      </div>

      <div className="border-t border-[#2e2e2e] pt-3">
        <p className="text-xs font-bold text-gray-400 uppercase mb-2">Checklist</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1" data-testid="ct-checklist">
          {CHECK_LABELS.map(([k, lbl]) => (
            <div key={k} className="flex items-center gap-2 text-sm">
              {ck[k] ? <CheckCircle2 size={15} className="text-[#009B3A]" /> : (k === "no_critical_error" && ck[k] === false ? <XCircle size={15} className="text-red-400" /> : <Circle size={15} className="text-gray-600" />)}
              <span className={ck[k] ? "text-gray-200" : "text-gray-500"}>{lbl}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        <button onClick={finalize} disabled={busy} data-testid="ct-finalize" className="text-xs font-bold rounded-full px-5 py-2 bg-[#009B3A] text-white">Registrar resultado</button>
        <button onClick={reset} disabled={busy} data-testid="ct-reset" className="text-xs font-semibold rounded-full px-4 py-2 border border-red-500/40 text-red-400 ml-auto">Reiniciar teste</button>
      </div>
      <p className="text-[11px] text-gray-600">A emissão/compra e o cancelamento da etiqueta são finalizados no painel SuperFrete (a API não expõe contrato público completo para isso). O pedido de teste é isolado e não entra em métricas reais.</p>
    </div>
  );
}
