import { useEffect, useState } from "react";
import { Package, ShoppingBag, Users, DollarSign, AlertTriangle } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import api from "@/lib/api";
import { formatBRL } from "@/lib/brand";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    api.get("/admin/stats").then((r) => setStats(r.data));
  }, []);

  if (!stats) return <div className="text-gray-400">Carregando...</div>;

  const cards = [
    { l: "Faturamento", v: formatBRL(stats.revenue), icon: DollarSign, color: "#009B3A" },
    { l: "Pedidos", v: stats.total_orders, icon: ShoppingBag, color: "#1E3A8A" },
    { l: "Produtos", v: stats.total_products, icon: Package, color: "#FFC107" },
    { l: "Clientes", v: stats.total_customers, icon: Users, color: "#1E3A8A" },
  ];

  return (
    <div>
      <h1 className="text-3xl font-display font-black uppercase text-white mb-8">Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {cards.map((c) => (
          <div key={c.l} className="bm-card p-5" data-testid={`stat-${c.l.toLowerCase()}`}>
            <div className="h-10 w-10 grid place-items-center rounded-lg mb-3" style={{ background: `${c.color}22`, color: c.color }}>
              <c.icon size={20} />
            </div>
            <p className="text-2xl font-display font-black text-white">{c.v}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">{c.l}</p>
          </div>
        ))}
      </div>

      {stats.low_stock > 0 && (
        <div className="bm-card p-4 mb-6 flex items-center gap-3 border-[#FFC107]/40">
          <AlertTriangle className="text-[#FFC107]" size={20} />
          <span className="text-sm text-gray-300">{stats.low_stock} produto(s) com estoque baixo (≤ 5 unidades).</span>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bm-card p-6 lg:col-span-2">
          <h3 className="font-display font-bold text-white uppercase mb-4">Faturamento</h3>
          {stats.revenue_series.length === 0 ? (
            <p className="text-gray-500 text-sm py-12 text-center">Sem vendas ainda. Os dados aparecerão aqui.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={stats.revenue_series}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FFC107" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#FFC107" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#666" fontSize={11} tickFormatter={(d) => d.slice(5)} />
                <YAxis stroke="#666" fontSize={11} />
                <Tooltip contentStyle={{ background: "#1f1f1f", border: "1px solid #2e2e2e", borderRadius: 12 }} />
                <Area type="monotone" dataKey="revenue" stroke="#FFC107" strokeWidth={2} fill="url(#rev)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bm-card p-6">
          <h3 className="font-display font-bold text-white uppercase mb-4">Pedidos recentes</h3>
          {stats.recent_orders.length === 0 ? (
            <p className="text-gray-500 text-sm">Nenhum pedido ainda.</p>
          ) : (
            <div className="space-y-3">
              {stats.recent_orders.map((o) => (
                <div key={o.id} className="flex justify-between items-center text-sm">
                  <div>
                    <p className="text-white">#{o.order_number}</p>
                    <p className="text-gray-500 text-xs">{o.user_name}</p>
                  </div>
                  <span className="text-[#FFC107] font-semibold">{formatBRL(o.total)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
