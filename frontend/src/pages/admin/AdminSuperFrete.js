import { useEffect, useState } from "react";
import { Truck, Plug, Save, RefreshCw, Power } from "lucide-react";
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

        <div className="flex flex-wrap gap-3 pt-2">
          <button onClick={save} disabled={busy} data-testid="sf-save" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-2.5 flex items-center gap-2"><Save size={16} /> Salvar</button>
          <button onClick={test} disabled={busy} data-testid="sf-test" className="border border-[#1E3A8A] text-[#8fb0ff] font-semibold rounded-full px-5 py-2.5 flex items-center gap-2"><Plug size={16} /> Testar conexão</button>
          <button onClick={load} disabled={busy} className="border border-[#2e2e2e] text-gray-300 rounded-full px-4 py-2.5 flex items-center gap-2"><RefreshCw size={15} /> Recarregar</button>
          {c.is_enabled && <button onClick={disconnect} data-testid="sf-disconnect" className="border border-red-500/40 text-red-400 rounded-full px-4 py-2.5 flex items-center gap-2 ml-auto"><Power size={15} /> Desativar</button>}
        </div>
        {c.last_error && <p className="text-xs text-red-400" data-testid="sf-last-error">Último erro: {c.last_error}</p>}
      </div>
    </div>
  );
}
