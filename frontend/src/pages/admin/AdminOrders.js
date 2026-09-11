import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Truck, ChevronDown, ChevronUp, Printer, MapPin, RefreshCw } from "lucide-react";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const STATUSES = ["confirmado", "em_separacao", "enviado", "entregue", "cancelado"];

const ACTION_LABELS = {
  prepare: "Preparar envio",
  cart: "Inserir no carrinho",
  checkout: "Comprar etiqueta",
  generate: "Gerar etiqueta",
  print: "Imprimir etiqueta",
  tracking: "Rastrear",
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const load = () => api.get("/admin/orders").then((r) => setOrders(r.data));
  useEffect(() => { load(); }, []);

  const changeStatus = async (id, status) => {
    await api.put(`/admin/orders/${id}/status`, { status });
    toast.success("Status atualizado");
    load();
  };

  return (
    <div>
      <h1 className="text-3xl font-display font-black uppercase text-white mb-6">Pedidos</h1>
      {orders.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum pedido recebido ainda.</div>
      ) : (
        <div className="bm-card overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111111] text-gray-500 uppercase text-xs">
              <tr>
                <th className="text-left p-4">Pedido</th>
                <th className="text-left p-4">Cliente</th>
                <th className="text-left p-4">Data</th>
                <th className="text-left p-4">Total</th>
                <th className="text-left p-4">Status</th>
                <th className="text-left p-4">Logística</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <>
                  <tr key={o.id} className="border-t border-[#2e2e2e]" data-testid={`admin-order-${o.order_number}`}>
                    <td className="p-4 text-white font-semibold">#{o.order_number}</td>
                    <td className="p-4 text-gray-300">{o.user_name}<br /><span className="text-gray-600 text-xs">{o.user_email}</span></td>
                    <td className="p-4 text-gray-400">{new Date(o.created_at).toLocaleDateString("pt-BR")}</td>
                    <td className="p-4 text-white">{formatBRL(o.total)}</td>
                    <td className="p-4">
                      <select value={o.status} onChange={(e) => changeStatus(o.id, e.target.value)} data-testid={`order-status-${o.order_number}`} className="bg-[#111111] border border-[#2e2e2e] rounded-lg px-2 py-1.5 text-xs text-white">
                        {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="p-4">
                      <button onClick={() => setExpanded(expanded === o.id ? null : o.id)} data-testid={`toggle-shipment-${o.order_number}`} className="flex items-center gap-1.5 text-xs text-[#FFC107] font-semibold">
                        <Truck size={14} /> {o.shipping_provider === "melhor_envio" ? "Melhor Envio" : "Ver"}
                        {expanded === o.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </td>
                  </tr>
                  {expanded === o.id && (
                    <tr className="bg-[#0d0d0d]">
                      <td colSpan={6} className="p-4"><ShipmentPanel order={o} /></td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ShipmentPanel({ order }) {
  const [sh, setSh] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get(`/admin/orders/${order.id}/shipment`).then((r) => setSh(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [order.id]);

  const act = async (action) => {
    setBusy(true);
    try {
      if (action === "print") {
        const { data } = await api.get(`/admin/orders/${order.id}/shipment/print`);
        if (data.url) window.open(data.url, "_blank");
        else toast.error("Etiqueta ainda não disponível");
      } else if (action === "tracking") {
        const { data } = await api.post(`/admin/orders/${order.id}/shipment/tracking`);
        setSh(data);
        toast.success("Rastreamento atualizado");
      } else {
        const { data } = await api.post(`/admin/orders/${order.id}/shipment/${action}`);
        setSh(data);
        toast.success(ACTION_LABELS[action] + " ✓");
      }
      if (action !== "print") load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setBusy(false); }
  };

  if (!sh) return <p className="text-gray-500 text-sm">Carregando...</p>;
  const rec = order.recipient_snapshot || {};
  const allowed = sh.allowed_actions || [];

  return (
    <div className="grid lg:grid-cols-3 gap-4" data-testid={`shipment-panel-${order.order_number}`}>
      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3 flex items-center gap-2"><Truck size={14} /> Envio</h4>
        <Row l="Transportadora" v={order.shipping_company_name || sh.company_name || "—"} />
        <Row l="Serviço" v={order.shipping_service_name || sh.service_name || "—"} />
        <Row l="Valor cliente" v={order.shipping_price_customer != null ? formatBRL(order.shipping_price_customer) : "—"} />
        <Row l="Custo real (negócio)" v={order.shipping_price_quoted != null ? formatBRL(order.shipping_price_quoted) : (sh.price != null ? formatBRL(sh.price) : "—")} />
        <Row l="Prazo" v={order.shipping_delivery_max ? `${order.shipping_delivery_min || order.shipping_delivery_max}–${order.shipping_delivery_max} dias` : "—"} />
        <Row l="CEP destino" v={order.shipping_destination_postal_code || rec.zip || "—"} />
        <Row l="Status" v={<span className="text-[#FFC107] uppercase text-xs font-bold" data-testid={`shipment-status-${order.order_number}`}>{sh.internal_status}</span>} />
        {sh.external_status && <Row l="Status ME" v={sh.external_status} />}
        {sh.tracking_code && <Row l="Rastreio" v={sh.tracking_code} />}
        {sh.cart_order_id && <Row l="Shipment ID" v={<span className="text-[10px] break-all">{sh.cart_order_id}</span>} />}
      </div>

      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3 flex items-center gap-2"><MapPin size={14} /> Destinatário</h4>
        <Row l="Nome" v={rec.name || order.user_name} />
        <Row l="Documento" v={rec.document || "—"} />
        <Row l="Endereço" v={rec.street ? `${rec.street}, ${rec.number} - ${rec.district}` : "—"} />
        <Row l="Cidade/UF" v={rec.city ? `${rec.city}/${rec.uf || rec.state || ""}` : "—"} />
        <Row l="CEP" v={rec.zip || "—"} />
      </div>

      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3">Ações / Timeline</h4>
        {order.shipping_provider !== "melhor_envio" ? (
          <p className="text-xs text-gray-500">Pedido sem cotação Melhor Envio (frete padrão).</p>
        ) : (
          <div className="flex flex-wrap gap-2 mb-4">
            {["prepare", "cart", "checkout", "generate", "print", "tracking"].map((a) => (
              <button key={a} onClick={() => act(a)} disabled={busy || !allowed.includes(a)}
                data-testid={`ship-action-${a}-${order.order_number}`}
                className={`text-xs font-semibold rounded-full px-3 py-1.5 flex items-center gap-1 border ${allowed.includes(a) ? "border-[#FFC107] text-[#FFC107] hover:bg-[#FFC107]/10" : "border-[#2e2e2e] text-gray-600 cursor-not-allowed"}`}>
                {a === "print" && <Printer size={12} />}{a === "tracking" && <RefreshCw size={12} />}{ACTION_LABELS[a]}
              </button>
            ))}
          </div>
        )}
        <div className="space-y-1.5">
          {(sh.timeline || []).map((t, i) => (
            <div key={i} className="text-xs text-gray-400 flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#009B3A]" /> {t.label}</div>
          ))}
          {(sh.timeline || []).length === 0 && <p className="text-xs text-gray-600">Nenhum evento ainda.</p>}
        </div>
      </div>
    </div>
  );
}

function Row({ l, v }) {
  return (
    <div className="flex justify-between gap-3 py-1 text-xs border-b border-[#1a1a1a] last:border-0">
      <span className="text-gray-500">{l}</span>
      <span className="text-gray-200 text-right">{v}</span>
    </div>
  );
}
