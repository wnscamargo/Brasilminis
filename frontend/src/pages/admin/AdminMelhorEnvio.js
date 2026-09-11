import { useEffect, useState, useCallback } from "react";
import { Truck, Plug, PlugZap, RefreshCw, Unplug, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { useCepAutofill, maskCep } from "@/lib/cep";

const STATUS_UI = {
  not_configured: { label: "Não configurado", color: "#6b7280", icon: AlertTriangle },
  not_connected: { label: "Não conectado", color: "#FFC107", icon: Plug },
  connected: { label: "Conectado", color: "#009B3A", icon: CheckCircle2 },
  token_expired: { label: "Token expirado", color: "#b45309", icon: RefreshCw },
  error: { label: "Erro", color: "#b91c1c", icon: XCircle },
};

const SENDER_FIELDS = [
  ["name", "Nome"], ["company", "Empresa"], ["email", "E-mail"], ["phone", "Telefone"],
  ["document", "CPF/CNPJ"], ["state_register", "Inscrição Estadual (IE)"],
  ["postal_code", "CEP"], ["address", "Rua"], ["number", "Número"], ["complement", "Complemento"],
  ["district", "Bairro"], ["city", "Cidade"], ["state_abbr", "UF"],
];

export default function AdminMelhorEnvio() {
  const [status, setStatus] = useState(null);
  const [sender, setSender] = useState({});
  const [busy, setBusy] = useState(false);

  const fillFromCep = useCepAutofill((d) => setSender((s) => ({
    ...s,
    address: d.street || s.address,
    district: d.district || s.district,
    city: d.city || s.city,
    state_abbr: d.uf || s.state_abbr,
  })));

  const loadStatus = useCallback(() => api.get("/admin/melhor-envio/status").then((r) => setStatus(r.data)), []);
  useEffect(() => {
    loadStatus();
    api.get("/admin/melhor-envio/sender").then((r) => setSender(r.data));
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "1") toast.success("Melhor Envio conectado!");
    else if (params.get("connected") === "0") toast.error("Falha ao conectar. Verifique o app Sandbox.");
  }, [loadStatus]);

  const connect = async () => {
    try {
      const { data } = await api.get("/admin/melhor-envio/auth-url");
      window.location.href = data.authorization_url;
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const testConn = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/melhor-envio/test");
      if (data.ok) toast.success(`Conexão OK${data.account_email ? " · " + data.account_email : ""}`);
      else toast.error(data.message || "Sem conexão");
      loadStatus();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const disconnect = async () => {
    if (!window.confirm("Desconectar a conta Melhor Envio?")) return;
    await api.post("/admin/melhor-envio/disconnect");
    toast.success("Desconectado");
    loadStatus();
  };
  const saveSender = async () => {
    setBusy(true);
    try {
      const { data } = await api.put("/admin/melhor-envio/sender", sender);
      setSender(data);
      toast.success("Remetente salvo");
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const ui = STATUS_UI[status?.status] || STATUS_UI.not_configured;
  const StatusIcon = ui.icon;
  const connected = status?.status === "connected";

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Truck className="text-[#FFC107]" size={28} />
          <h1 className="text-3xl font-display font-black uppercase text-white">Melhor Envio</h1>
          <span data-testid="me-env-badge" className="bg-[#b45309] text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">{status?.environment || "sandbox"}</span>
        </div>
      </div>

      <div className="bm-card p-6 mb-6" data-testid="me-connection-card">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 grid place-items-center rounded-xl" style={{ background: `${ui.color}22`, color: ui.color }}>
              <StatusIcon size={24} />
            </div>
            <div>
              <p className="text-white font-display font-bold uppercase" data-testid="me-status">{ui.label}</p>
              <p className="text-xs text-gray-500">
                {status?.account_email ? `Conta: ${status.account_email}` : "Nenhuma conta conectada"}
                {status?.access_token_masked && ` · token ${status.access_token_masked}`}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {!connected && (
              <button onClick={connect} disabled={!status?.configured} data-testid="me-connect-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2 disabled:opacity-40"><PlugZap size={16} /> Conectar Melhor Envio</button>
            )}
            {connected && (
              <>
                <button onClick={testConn} disabled={busy} data-testid="me-test-btn" className="bg-[#1E3A8A] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><RefreshCw size={16} /> Testar conexão</button>
                <button onClick={connect} data-testid="me-reconnect-btn" className="border border-[#2e2e2e] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Plug size={16} /> Reconectar</button>
                <button onClick={disconnect} data-testid="me-disconnect-btn" className="border border-red-500/40 text-red-400 font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Unplug size={16} /> Desconectar</button>
              </>
            )}
          </div>
        </div>
        {!status?.configured && (
          <div className="mt-4 flex items-start gap-2 text-sm text-gray-400 bg-[#111] border border-[#2e2e2e] rounded-lg p-3">
            <AlertTriangle size={18} className="text-[#FFC107] shrink-0 mt-0.5" />
            <span>Configure as variáveis <code className="text-[#FFC107]">MELHOR_ENVIO_CLIENT_ID</code>, <code className="text-[#FFC107]">CLIENT_SECRET</code> e <code className="text-[#FFC107]">REDIRECT_URI</code> no backend (app Sandbox) para habilitar a conexão.</span>
          </div>
        )}
      </div>

      <div className="bm-card p-6" data-testid="me-sender-card">
        <h3 className="font-display font-bold text-white uppercase mb-1">Dados do remetente</h3>
        <p className="text-xs text-gray-500 mb-5">Endereço de origem usado nas cotações e etiquetas. Não use dados fictícios.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {SENDER_FIELDS.map(([key, label]) => (
            <div key={key}>
              <label className="text-xs text-gray-500 block mb-1">{label}</label>
              <input value={sender[key] || ""} onChange={(e) => { const val = key === "postal_code" ? maskCep(e.target.value) : e.target.value; setSender({ ...sender, [key]: val }); if (key === "postal_code") fillFromCep(val); }} data-testid={`sender-${key}`} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
            </div>
          ))}
        </div>
        <button onClick={saveSender} disabled={busy} data-testid="save-sender-btn" className="mt-5 bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-3">{busy ? "Salvando..." : "Salvar remetente"}</button>
      </div>
    </div>
  );
}
