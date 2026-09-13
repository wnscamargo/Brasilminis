import { useEffect, useState } from "react";
import { DollarSign, ShoppingBag, TrendingUp, Percent, Receipt, Package, AlertTriangle, Truck, RotateCcw, History, X } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const PERIODS = [
  { k: "today", l: "Hoje" },
  { k: "7d", l: "7 dias" },
  { k: "30d", l: "30 dias" },
  { k: "this_month", l: "Este mês" },
  { k: "last_month", l: "Mês anterior" },
  { k: "custom", l: "Personalizado" },
];

export default function Dashboard() {
  const [period, setPeriod] = useState("30d");
  const [range, setRange] = useState({ start: "", end: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [baseline, setBaseline] = useState(null);
  const [resets, setResets] = useState([]);
  const [showReset, setShowReset] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const fetchData = () => {
    setLoading(true);
    const params = { period };
    if (period === "custom") { params.start = range.start; params.end = range.end; }
    api.get("/admin/analytics", { params }).then((r) => { setData(r.data); setLoading(false); });
  };

  const fetchBaseline = () => api.get("/admin/dashboard/baseline").then((r) => { setBaseline(r.data.baseline); setResets(r.data.history || []); });

  useEffect(() => { if (period !== "custom") fetchData(); /* eslint-disable-next-line */ }, [period]);
  useEffect(() => { fetchData(); fetchBaseline(); /* eslint-disable-next-line */ }, []);

  const cards = data ? [
    { l: "Faturamento bruto", v: formatBRL(data.revenue_gross), icon: DollarSign, color: "#009B3A", testid: "kpi-revenue" },
    { l: "Receita líquida", v: formatBRL(data.net_revenue), icon: Receipt, color: "#1E3A8A", testid: "kpi-net-revenue" },
    { l: "CMV", v: formatBRL(data.cogs), icon: Package, color: "#b91c1c", testid: "kpi-cogs" },
    { l: "Lucro bruto", v: formatBRL(data.gross_profit), icon: TrendingUp, color: "#009B3A", testid: "kpi-profit" },
    { l: "Margem bruta", v: `${data.gross_margin_pct.toFixed(1)}%`, icon: Percent, color: "#FFC107", testid: "kpi-margin" },
    { l: "Ticket médio", v: formatBRL(data.avg_ticket), icon: DollarSign, color: "#1E3A8A", testid: "kpi-ticket" },
    { l: "Pedidos", v: data.orders_count, icon: ShoppingBag, color: "#FFC107", testid: "kpi-orders" },
    { l: "Produtos vendidos", v: data.products_sold, icon: Package, color: "#009B3A", testid: "kpi-sold" },
  ] : [];

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Dashboard</h1>
        <div className="flex flex-wrap gap-2">
          {PERIODS.map((p) => (
            <button key={p.k} onClick={() => setPeriod(p.k)} data-testid={`period-${p.k}`} className={`px-4 py-2 rounded-full text-xs font-semibold border transition-colors ${period === p.k ? "bg-[#FFC107] border-[#FFC107] text-[#111]" : "border-[#2e2e2e] text-gray-400 hover:text-white"}`}>{p.l}</button>
          ))}
        </div>
      </div>

      {period === "custom" && (
        <div className="bm-card p-4 mb-6 flex flex-wrap items-end gap-3">
          <div><label className="text-xs text-gray-500 block mb-1">Início</label><input type="date" value={range.start} onChange={(e) => setRange({ ...range, start: e.target.value })} data-testid="custom-start" className="bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white" /></div>
          <div><label className="text-xs text-gray-500 block mb-1">Fim</label><input type="date" value={range.end} onChange={(e) => setRange({ ...range, end: e.target.value })} data-testid="custom-end" className="bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white" /></div>
          <button onClick={fetchData} data-testid="apply-custom" className="bg-[#1E3A8A] text-white rounded-lg px-5 py-2 text-sm font-semibold">Aplicar</button>
        </div>
      )}

      {/* Controle dos indicadores */}
      <div className="bm-card p-4 mb-6" data-testid="dashboard-controls">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-display font-bold text-white uppercase text-sm flex items-center gap-2"><History size={16} className="text-[#FFC107]" /> Controle dos indicadores</h3>
            {baseline ? (
              <p className="text-xs text-gray-400 mt-1" data-testid="dashboard-baseline-label">Indicadores contando a partir de <b className="text-gray-200">{new Date(baseline).toLocaleString("pt-BR")}</b>. O histórico anterior permanece no banco (use o período Personalizado).</p>
            ) : (
              <p className="text-xs text-gray-500 mt-1" data-testid="dashboard-baseline-label">Nenhuma zeragem aplicada — indicadores consideram todo o histórico.</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {resets.length > 0 && (
              <button onClick={() => setShowHistory(true)} data-testid="dashboard-history-btn" className="text-xs font-semibold rounded-full px-4 py-2 border border-[#2e2e2e] text-gray-300 hover:text-white">Histórico de zeragens ({resets.length})</button>
            )}
            <button onClick={() => setShowReset(true)} data-testid="dashboard-reset-btn" className="text-xs font-bold rounded-full px-4 py-2 border border-[#FFC107] text-[#FFC107] hover:bg-[#FFC107]/10 inline-flex items-center gap-1.5"><RotateCcw size={14} /> Zerar Dashboard</button>
          </div>
        </div>
      </div>

      {loading || !data ? (
        <div className="text-gray-400">Carregando...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {cards.map((c) => (
              <div key={c.l} className="bm-card p-5" data-testid={c.testid}>
                <div className="h-10 w-10 grid place-items-center rounded-lg mb-3" style={{ background: `${c.color}22`, color: c.color }}><c.icon size={20} /></div>
                <p className="text-2xl font-display font-black text-white">{c.v}</p>
                <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">{c.l}</p>
              </div>
            ))}
          </div>

          {(data.products_without_cost_catalog > 0 || data.items_without_cost_qty > 0) && (
            <div className="bm-card p-4 mb-6 flex items-start gap-3 border-[#FFC107]/40" data-testid="cost-warning">
              <AlertTriangle className="text-[#FFC107] shrink-0 mt-0.5" size={20} />
              <div className="text-sm text-gray-300">
                {data.items_without_cost_qty > 0 && <p><b className="text-white">{data.items_without_cost_qty}</b> unidade(s) vendida(s) sem custo cadastrado no momento da venda — não entram no CMV nem no lucro.</p>}
                {data.products_without_cost_catalog > 0 && <p className="mt-1"><b className="text-white">{data.products_without_cost_catalog}</b> produto(s) ativo(s) ainda sem custo cadastrado no catálogo.</p>}
              </div>
            </div>
          )}

          {/* Resultado separado: produtos x logística */}
          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <MiniCard label="Resultado dos produtos" value={formatBRL(data.product_result)} icon={TrendingUp} color="#009B3A" testid="res-products" />
            <MiniCard label="Receita de frete" value={formatBRL(data.shipping_revenue)} icon={Truck} color="#1E3A8A" testid="res-shipping" />
            <MiniCard label="Descontos concedidos" value={formatBRL(data.discounts)} icon={Percent} color="#FFC107" testid="res-discounts" />
          </div>

          <div className="bm-card p-6 mb-6">
            <h3 className="font-display font-bold text-white uppercase mb-4">Faturamento × CMV × Lucro bruto</h3>
            {data.series.length === 0 ? (
              <p className="text-gray-500 text-sm py-12 text-center">Sem vendas no período selecionado.</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data.series}>
                  <defs>
                    <linearGradient id="gRev" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#FFC107" stopOpacity={0.5} /><stop offset="100%" stopColor="#FFC107" stopOpacity={0} /></linearGradient>
                    <linearGradient id="gProfit" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#009B3A" stopOpacity={0.5} /><stop offset="100%" stopColor="#009B3A" stopOpacity={0} /></linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#666" fontSize={11} tickFormatter={(d) => d.slice(5)} />
                  <YAxis stroke="#666" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#1f1f1f", border: "1px solid #2e2e2e", borderRadius: 12 }} formatter={(v) => formatBRL(v)} />
                  <Legend />
                  <Area type="monotone" name="Faturamento" dataKey="revenue" stroke="#FFC107" strokeWidth={2} fill="url(#gRev)" />
                  <Area type="monotone" name="CMV" dataKey="cogs" stroke="#b91c1c" strokeWidth={2} fill="none" />
                  <Area type="monotone" name="Lucro bruto" dataKey="profit" stroke="#009B3A" strokeWidth={2} fill="url(#gProfit)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <RankCard title="Top produtos por faturamento" rows={data.top_products_revenue} fmt={formatBRL} testid="rank-prod-revenue" />
            <RankCard title="Top produtos por lucro bruto" rows={data.top_products_profit} fmt={formatBRL} testid="rank-prod-profit" />
            <RankCard title="Top categorias por faturamento" rows={data.top_categories_revenue} fmt={formatBRL} testid="rank-categories" />
            <RankCard title="Top subcategorias por faturamento" rows={data.top_subcategories_revenue} fmt={formatBRL} testid="rank-subcategories" />
            <RankCard title="Mais vendidos (unidades)" rows={data.best_sellers} fmt={(v) => `${v} un`} testid="rank-bestsellers" />
            <RankCard title="Menor margem (catálogo)" rows={data.low_margin_products.map((p) => ({ name: p.name, value: p.margin_pct }))} fmt={(v) => `${v.toFixed(1)}%`} testid="rank-low-margin" />
          </div>
        </>
      )}

      {showReset && <ResetModal onClose={() => setShowReset(false)} onDone={() => { setShowReset(false); fetchBaseline(); fetchData(); }} />}
      {showHistory && <HistoryModal resets={resets} onClose={() => setShowHistory(false)} />}
    </div>
  );
}

function ResetModal({ onClose, onDone }) {
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const canReset = reason.trim().length > 0 && confirm === "ZERAR DASHBOARD";

  const doReset = async () => {
    if (!canReset) return;
    setBusy(true);
    try {
      await api.post("/admin/dashboard/reset", { reason: reason.trim(), confirm });
      toast.success("Dashboard zerado a partir de agora");
      onDone();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="dashboard-reset-modal">
      <div className="bm-card p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white flex items-center gap-2"><AlertTriangle className="text-[#FFC107]" size={20} /> Zerar Dashboard</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="text-sm text-gray-300 bg-[#111] border border-[#FFC107]/40 rounded-lg p-3 mb-4">
          Esta ação redefine os indicadores visuais do Dashboard a partir deste momento. Nenhum pedido, pagamento ou histórico será apagado.
        </div>
        <label className="text-xs text-gray-500 block mb-1">Motivo da zeragem</label>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="dashboard-reset-reason" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-3" />
        <label className="text-xs text-gray-500 block mb-1">Para confirmar, digite <b className="text-[#FFC107]">ZERAR DASHBOARD</b></label>
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="dashboard-reset-confirm-input" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-4" />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-300 hover:text-white">Cancelar</button>
          <button onClick={doReset} disabled={!canReset || busy} data-testid="dashboard-reset-confirm-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-5 py-2 text-sm disabled:opacity-40">
            {busy ? "Zerando..." : "ZERAR DASHBOARD"}
          </button>
        </div>
      </div>
    </div>
  );
}

function HistoryModal({ resets, onClose }) {
  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="dashboard-history-modal">
      <div className="bm-card p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white flex items-center gap-2"><History size={18} className="text-[#FFC107]" /> Histórico de zeragens</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          {resets.map((r) => (
            <div key={r.id} className="bg-[#111] border border-[#2e2e2e] rounded-lg p-3 text-sm" data-testid={`reset-row-${r.id}`}>
              <div className="flex justify-between text-white"><span className="font-semibold">{new Date(r.created_at).toLocaleString("pt-BR")}</span><span className="text-gray-500 text-xs">{r.admin_email}</span></div>
              <p className="text-gray-400 mt-1">Motivo: {r.reason}</p>
              <p className="text-gray-600 text-xs mt-1">Marco: {new Date(r.reset_at).toLocaleString("pt-BR")}{r.previous_reset_at ? ` • anterior: ${new Date(r.previous_reset_at).toLocaleString("pt-BR")}` : ""}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MiniCard({ label, value, icon: Icon, color, testid }) {
  return (
    <div className="bm-card p-4 flex items-center gap-3" data-testid={testid}>
      <div className="h-10 w-10 grid place-items-center rounded-lg shrink-0" style={{ background: `${color}22`, color }}><Icon size={18} /></div>
      <div><p className="text-lg font-display font-black text-white">{value}</p><p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p></div>
    </div>
  );
}

function RankCard({ title, rows, fmt, testid }) {
  return (
    <div className="bm-card p-6" data-testid={testid}>
      <h3 className="font-display font-bold text-white uppercase mb-4 text-sm">{title}</h3>
      {(!rows || rows.length === 0) ? (
        <p className="text-gray-500 text-sm">Sem dados no período.</p>
      ) : (
        <div className="space-y-2.5">
          {rows.map((r, i) => (
            <div key={(r.product_id || r.id || r.name) + i} className="flex justify-between items-center text-sm gap-3">
              <span className="text-gray-300 truncate flex items-center gap-2"><span className="text-gray-600 w-4">{i + 1}.</span>{r.name}</span>
              <span className="text-[#FFC107] font-semibold whitespace-nowrap">{fmt(r.value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
