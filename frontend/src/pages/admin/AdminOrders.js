import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const STATUSES = ["confirmado", "em_separacao", "enviado", "entregue", "cancelado"];

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
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
                <th className="text-left p-4">Pagto</th>
                <th className="text-left p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t border-[#2e2e2e]" data-testid={`admin-order-${o.order_number}`}>
                  <td className="p-4 text-white font-semibold">#{o.order_number}</td>
                  <td className="p-4 text-gray-300">{o.user_name}<br /><span className="text-gray-600 text-xs">{o.user_email}</span></td>
                  <td className="p-4 text-gray-400">{new Date(o.created_at).toLocaleDateString("pt-BR")}</td>
                  <td className="p-4 text-white">{formatBRL(o.total)}</td>
                  <td className="p-4 text-gray-400 uppercase text-xs">{o.payment_method}</td>
                  <td className="p-4">
                    <select value={o.status} onChange={(e) => changeStatus(o.id, e.target.value)} data-testid={`order-status-${o.order_number}`} className="bg-[#111111] border border-[#2e2e2e] rounded-lg px-2 py-1.5 text-xs text-white">
                      {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
