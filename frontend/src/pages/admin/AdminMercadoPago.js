import { useEffect, useState, useCallback } from "react";
import { CreditCard, RefreshCw, Unplug, CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const STATUS_UI = {
  not_configured: { label: "Não configurado", color: "#6b7280", icon: AlertTriangle },
  configured: { label: "Configurado", color: "#FFC107", icon: CheckCircle2 },
  connected: { label: "Conectado", color: "#009B3A", icon: CheckCircle2 },
  invalid: { label: "Credencial inválida", color: "#b91c1c", icon: XCircle },
  error: { label: "Erro", color: "#b91c1c", icon: XCircle },
};

export default function AdminMercadoPago() {
  const [status, setStatus] = useState(null);
  const [publicKey, setPublicKey] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.get("/admin/mercado-pago/status").then((r) => { setStatus(r.data); setPublicKey(r.data.public_key || ""); }), []);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    setBusy(true);
    try {
      const body = { environment: "test", public_key: publicKey, is_enabled: true };
      if (accessToken) body.access_token = accessToken;
      if (webhookSecret) body.webhook_secret = webhookSecret;
      await api.put("/admin/mercado-pago/settings", body);
      setAccessToken(""); setWebhookSecret("");
      toast.success("Credenciais salvas com segurança");
      load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const testConn = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/mercado-pago/test");
      if (data.ok) toast.success("Conexão OK"); else toast.error(data.message || "Sem conexão");
      load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const disconnect = async () => {
    if (!window.confirm("Desconectar o Mercado Pago?")) return;
    await api.post("/admin/mercado-pago/disconnect");
    toast.success("Desconectado"); setPublicKey(""); load();
  };

  const ui = STATUS_UI[status?.status] || STATUS_UI.not_configured;
  const StatusIcon = ui.icon;
  const configured = status?.status && status.status !== "not_configured";

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <CreditCard className="text-[#FFC107]" size={28} />
          <h1 className="text-3xl font-display font-black uppercase text-white">Mercado Pago</h1>
          <span data-testid="mp-env-badge" className="bg-[#b45309] text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">{status?.environment || "test"}</span>
        </div>
      </div>

      <div className="bm-card p-6 mb-6" data-testid="mp-status-card">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 grid place-items-center rounded-xl" style={{ background: `${ui.color}22`, color: ui.color }}><StatusIcon size={24} /></div>
            <div>
              <p className="text-white font-display font-bold uppercase" data-testid="mp-status">{ui.label}</p>
              <p className="text-xs text-gray-500">Ambiente de TESTE · produção bloqueada nesta fase</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {configured && <button onClick={testConn} disabled={busy} data-testid="mp-test-btn" className="bg-[#1E3A8A] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><RefreshCw size={16} /> Testar conexão</button>}
            {configured && <button onClick={disconnect} data-testid="mp-disconnect-btn" className="border border-red-500/40 text-red-400 font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Unplug size={16} /> Desconectar</button>}
          </div>
        </div>
      </div>

      <div className="bm-card p-6" data-testid="mp-credentials-card">
        <h3 className="font-display font-bold text-white uppercase mb-1">Credenciais de teste</h3>
        <p className="text-xs text-gray-500 mb-5">Obtenha em: painel do desenvolvedor → Suas integrações → Testes → Credenciais de teste.</p>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Public Key</label>
            <input value={publicKey} onChange={(e) => setPublicKey(e.target.value)} placeholder="TEST-..." data-testid="mp-public-key" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Access Token</label>
            <input value={accessToken} onChange={(e) => setAccessToken(e.target.value)} type="password" placeholder={status?.access_token_masked || "APP_USR-..."} data-testid="mp-access-token" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Webhook Secret (opcional)</label>
            <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} type="password" placeholder="••••••" data-testid="mp-webhook-secret" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          </div>
        </div>
        <div className="mt-4 flex items-start gap-2 text-xs text-gray-400 bg-[#111] border border-[#2e2e2e] rounded-lg p-3">
          <ShieldCheck size={16} className="text-[#009B3A] shrink-0 mt-0.5" />
          <span>O Access Token é armazenado de forma <b className="text-white">criptografada</b> e nunca será exibido novamente. A Public Key pode ser usada no frontend.</span>
        </div>
        <button onClick={save} disabled={busy} data-testid="mp-save-btn" className="mt-5 bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-3">{busy ? "Salvando..." : "Salvar"}</button>
      </div>
    </div>
  );
}
