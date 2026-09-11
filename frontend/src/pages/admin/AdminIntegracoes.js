import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Plug, CreditCard, Truck, RefreshCw, Unplug, PlugZap, CheckCircle2,
  AlertTriangle, XCircle, ShieldCheck, ShieldAlert, Rocket, Settings2,
} from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const MP_STATUS = {
  not_configured: { label: "Não configurado", color: "#6b7280", icon: AlertTriangle },
  configured: { label: "Configurado", color: "#FFC107", icon: CheckCircle2 },
  connected: { label: "Conectado", color: "#009B3A", icon: CheckCircle2 },
  invalid: { label: "Credencial inválida", color: "#b91c1c", icon: XCircle },
  error: { label: "Erro", color: "#b91c1c", icon: XCircle },
};
const ME_STATUS = {
  not_configured: { label: "Não configurado", color: "#6b7280", icon: AlertTriangle },
  not_connected: { label: "Não conectado", color: "#FFC107", icon: Plug },
  connected: { label: "Conectado", color: "#009B3A", icon: CheckCircle2 },
  token_expired: { label: "Token expirado", color: "#b45309", icon: RefreshCw },
  error: { label: "Erro", color: "#b91c1c", icon: XCircle },
};

export default function AdminIntegracoes() {
  const [data, setData] = useState(null);

  const load = useCallback(() => api.get("/admin/integrations").then((r) => setData(r.data)), []);
  useEffect(() => {
    load();
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "1") toast.success("Melhor Envio conectado!");
    else if (params.get("connected") === "0") toast.error("Falha ao conectar. Verifique as credenciais.");
  }, [load]);

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <Plug className="text-[#FFC107]" size={28} />
        <h1 className="text-3xl font-display font-black uppercase text-white">Central de Integrações</h1>
      </div>
      <p className="text-gray-500 text-sm mb-8">Gerencie pagamentos e envios. Credenciais ficam salvas de forma segura no banco (nunca no código).</p>

      <div className="grid xl:grid-cols-2 gap-6">
        <MercadoPagoCard st={data?.mercado_pago} reload={load} />
        <MelhorEnvioCard st={data?.melhor_envio} reload={load} />
      </div>
    </div>
  );
}

function EnvBadge({ env, prod }) {
  const isProd = env === "production";
  return (
    <span data-testid="env-badge" className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ${isProd ? "bg-[#009B3A] text-white" : "bg-[#b45309] text-white"}`}>
      {isProd ? "Produção" : (prod === "sandbox" ? "Sandbox" : "Teste")}
    </span>
  );
}

function StatusPill({ ui }) {
  const Icon = ui.icon;
  return (
    <div className="flex items-center gap-3">
      <div className="h-11 w-11 grid place-items-center rounded-xl" style={{ background: `${ui.color}22`, color: ui.color }}><Icon size={22} /></div>
      <p className="text-white font-display font-bold uppercase text-sm" data-testid="integration-status">{ui.label}</p>
    </div>
  );
}

/* ================= Mercado Pago ================= */
function MercadoPagoCard({ st, reload }) {
  const [publicKey, setPublicKey] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { setPublicKey(st?.public_key || ""); }, [st?.public_key]);

  if (!st) return <CardSkeleton />;
  const env = st.environment || "test";
  const ui = MP_STATUS[st.status] || MP_STATUS.not_configured;
  const configured = st.status && st.status !== "not_configured";
  const isProd = env === "production";

  const switchEnv = async (target) => {
    if (target === env) return;
    const msg = target === "production"
      ? "Trocar para PRODUÇÃO? As credenciais de teste serão apagadas e você precisará cadastrar as de produção e testar antes de ativar."
      : "Trocar para TESTE? As credenciais de produção serão apagadas.";
    if (!window.confirm(msg)) return;
    setBusy(true);
    try {
      await api.put("/admin/mercado-pago/settings", { environment: target });
      setAccessToken(""); setWebhookSecret("");
      toast.success(`Ambiente alterado para ${target === "production" ? "produção" : "teste"}`);
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const save = async () => {
    setBusy(true);
    try {
      const body = { environment: env, public_key: publicKey };
      if (accessToken) body.access_token = accessToken;
      if (webhookSecret) body.webhook_secret = webhookSecret;
      if (!isProd) body.is_enabled = true;
      await api.put("/admin/mercado-pago/settings", body);
      setAccessToken(""); setWebhookSecret("");
      toast.success("Credenciais salvas com segurança");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const test = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/mercado-pago/test");
      if (data.ok) toast.success("Conexão OK"); else toast.error(data.message || "Sem conexão");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const activate = async () => {
    if (!window.confirm("Ativar o modo PRODUÇÃO? A loja passará a cobrar pagamentos reais.")) return;
    setBusy(true);
    try {
      await api.post("/admin/mercado-pago/activate", { confirm: true });
      toast.success("Produção ativada!");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const disconnect = async () => {
    if (!window.confirm("Desconectar o Mercado Pago?")) return;
    await api.post("/admin/mercado-pago/disconnect");
    toast.success("Desconectado"); setPublicKey(""); reload();
  };

  return (
    <div className="bm-card p-6" data-testid="mp-integration-card">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <CreditCard className="text-[#FFC107]" size={24} />
          <h2 className="text-xl font-display font-black uppercase text-white">Mercado Pago</h2>
        </div>
        <EnvBadge env={env} prod="test" />
      </div>

      <div className="flex items-center justify-between gap-3 mb-5">
        <StatusPill ui={ui} />
        {st.is_enabled
          ? <span className="text-xs font-bold text-[#009B3A] flex items-center gap-1" data-testid="mp-enabled-flag"><CheckCircle2 size={14} /> Ativo no checkout</span>
          : <span className="text-xs font-bold text-gray-500 flex items-center gap-1"><ShieldAlert size={14} /> Inativo</span>}
      </div>

      <EnvSwitch value={env} options={[["test", "Teste"], ["production", "Produção"]]} onChange={switchEnv} disabled={busy} testid="mp-env-switch" />

      <div className="space-y-3 mt-4">
        <Field label="Public Key" value={publicKey} onChange={setPublicKey} placeholder={isProd ? "APP_USR-..." : "TEST-..."} testid="mp-public-key" />
        <Field label="Access Token" value={accessToken} onChange={setAccessToken} type="password" placeholder={st.access_token_masked || (isProd ? "APP_USR-..." : "TEST-...")} testid="mp-access-token" />
        <Field label="Webhook Secret (opcional)" value={webhookSecret} onChange={setWebhookSecret} type="password" placeholder="••••••" testid="mp-webhook-secret" />
      </div>

      <div className="mt-4 flex items-start gap-2 text-xs text-gray-400 bg-[#111] border border-[#2e2e2e] rounded-lg p-3">
        <ShieldCheck size={16} className="text-[#009B3A] shrink-0 mt-0.5" />
        <span>O Access Token é cifrado e nunca reexibido. {isProd && <b className="text-[#FFC107]">Produção exige teste + ativação explícita.</b>}</span>
      </div>

      <div className="flex flex-wrap gap-2 mt-5">
        <button onClick={save} disabled={busy} data-testid="mp-save-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-2.5">{busy ? "..." : "Salvar"}</button>
        {configured && <button onClick={test} disabled={busy} data-testid="mp-test-btn" className="bg-[#1E3A8A] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><RefreshCw size={16} /> Testar</button>}
        {isProd && st.status === "connected" && !st.is_enabled && (
          <button onClick={activate} disabled={busy} data-testid="mp-activate-btn" className="bg-[#009B3A] text-white font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Rocket size={16} /> Ativar produção</button>
        )}
        {configured && <button onClick={disconnect} data-testid="mp-disconnect-btn" className="border border-red-500/40 text-red-400 font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Unplug size={16} /> Desconectar</button>}
      </div>
      {isProd && configured && st.status !== "connected" && (
        <p data-testid="mp-activate-hint" className="mt-3 text-xs text-[#FFC107] flex items-center gap-1.5"><AlertTriangle size={14} /> Teste a conexão de produção antes de ativar o modo produção.</p>
      )}
    </div>
  );
}

/* ================= Melhor Envio ================= */
function MelhorEnvioCard({ st, reload }) {
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [redirectUri, setRedirectUri] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setClientId(st?.client_id || "");
    setRedirectUri(st?.redirect_uri || "");
  }, [st?.client_id, st?.redirect_uri]);

  if (!st) return <CardSkeleton />;
  const env = st.environment || "sandbox";
  const ui = ME_STATUS[st.status] || ME_STATUS.not_configured;
  const connected = st.status === "connected";
  const configured = st.configured;

  const switchEnv = async (target) => {
    if (target === env) return;
    if (!window.confirm(`Trocar o ambiente do Melhor Envio para ${target === "production" ? "PRODUÇÃO" : "SANDBOX"}? A conexão e o token atuais serão desassociados.`)) return;
    setBusy(true);
    try {
      await api.put("/admin/melhor-envio/credentials", { environment: target });
      setClientSecret("");
      toast.success("Ambiente alterado. Cadastre as credenciais e reconecte.");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const save = async () => {
    setBusy(true);
    try {
      const body = { environment: env, client_id: clientId, redirect_uri: redirectUri };
      if (clientSecret) body.client_secret = clientSecret;
      await api.put("/admin/melhor-envio/credentials", body);
      setClientSecret("");
      toast.success("Credenciais salvas com segurança");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const connect = async () => {
    try {
      const { data } = await api.get("/admin/melhor-envio/auth-url");
      window.location.href = data.authorization_url;
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const test = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/melhor-envio/test");
      if (data.ok) toast.success(`Conexão OK${data.account_email ? " · " + data.account_email : ""}`);
      else toast.error(data.message || "Sem conexão");
      reload();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const disconnect = async () => {
    if (!window.confirm("Desconectar a conta Melhor Envio? (as credenciais serão preservadas)")) return;
    await api.post("/admin/melhor-envio/disconnect");
    toast.success("Desconectado"); reload();
  };

  return (
    <div className="bm-card p-6" data-testid="me-integration-card">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <Truck className="text-[#FFC107]" size={24} />
          <h2 className="text-xl font-display font-black uppercase text-white">Melhor Envio</h2>
        </div>
        <EnvBadge env={env} prod="sandbox" />
      </div>

      <div className="flex items-center justify-between gap-3 mb-5">
        <StatusPill ui={ui} />
        {st.account_email && <span className="text-xs text-gray-400 truncate max-w-[160px]">{st.account_email}</span>}
      </div>

      <EnvSwitch value={env} options={[["sandbox", "Sandbox"], ["production", "Produção"]]} onChange={switchEnv} disabled={busy} testid="me-env-switch" />

      <div className="space-y-3 mt-4">
        <Field label="Client ID" value={clientId} onChange={setClientId} placeholder="ID do app" testid="me-client-id" />
        <Field label="Client Secret" value={clientSecret} onChange={setClientSecret} type="password" placeholder={st.client_secret_masked || "••••••"} testid="me-client-secret" />
        <Field label="Redirect URI" value={redirectUri} onChange={setRedirectUri} placeholder="https://seu-dominio/api/admin/melhor-envio/callback" testid="me-redirect-uri" />
      </div>

      <div className="mt-4 flex items-start gap-2 text-xs text-gray-400 bg-[#111] border border-[#2e2e2e] rounded-lg p-3">
        <ShieldCheck size={16} className="text-[#009B3A] shrink-0 mt-0.5" />
        <span>O Client Secret é cifrado. Cadastre a mesma Redirect URI no app do Melhor Envio.</span>
      </div>

      <div className="flex flex-wrap gap-2 mt-5">
        <button onClick={save} disabled={busy} data-testid="me-save-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-2.5">{busy ? "..." : "Salvar"}</button>
        {configured && !connected && <button onClick={connect} data-testid="me-connect-btn" className="bg-[#009B3A] text-white font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><PlugZap size={16} /> Conectar</button>}
        {connected && <button onClick={test} disabled={busy} data-testid="me-test-btn" className="bg-[#1E3A8A] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><RefreshCw size={16} /> Testar</button>}
        {connected && <button onClick={connect} data-testid="me-reconnect-btn" className="border border-[#2e2e2e] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Plug size={16} /> Reconectar</button>}
        {connected && <button onClick={disconnect} data-testid="me-disconnect-btn" className="border border-red-500/40 text-red-400 font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Unplug size={16} /> Desconectar</button>}
      </div>

      <Link to="/admin/melhor-envio" data-testid="me-sender-link" className="mt-4 inline-flex items-center gap-2 text-xs text-[#FFC107] hover:underline">
        <Settings2 size={14} /> Configurar dados do remetente e logística
      </Link>
    </div>
  );
}

/* ================= UI helpers ================= */
function EnvSwitch({ value, options, onChange, disabled, testid }) {
  return (
    <div>
      <label className="text-xs text-gray-500 block mb-1.5">Ambiente</label>
      <div className="inline-flex bg-[#111] border border-[#2e2e2e] rounded-full p-1" data-testid={testid}>
        {options.map(([v, l]) => (
          <button key={v} onClick={() => onChange(v)} disabled={disabled} data-testid={`${testid}-${v}`}
            className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide transition-colors ${value === v ? (v.includes("prod") ? "bg-[#009B3A] text-white" : "bg-[#1E3A8A] text-white") : "text-gray-400 hover:text-white"}`}>
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", placeholder, testid }) {
  return (
    <div>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} type={type} placeholder={placeholder} data-testid={testid}
        className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
    </div>
  );
}

function CardSkeleton() {
  return <div className="bm-card p-6 animate-pulse h-96"><div className="h-6 w-40 bg-white/10 rounded mb-6" /><div className="space-y-3"><div className="h-10 bg-white/5 rounded" /><div className="h-10 bg-white/5 rounded" /><div className="h-10 bg-white/5 rounded" /></div></div>;
}
