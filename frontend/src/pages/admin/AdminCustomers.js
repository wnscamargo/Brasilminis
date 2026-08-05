import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  useEffect(() => { api.get("/admin/customers").then((r) => setCustomers(r.data)); }, []);

  return (
    <div>
      <h1 className="text-3xl font-display font-black uppercase text-white mb-6">Clientes</h1>
      {customers.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum cliente cadastrado ainda.</div>
      ) : (
        <div className="bm-card overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111111] text-gray-500 uppercase text-xs">
              <tr>
                <th className="text-left p-4">Nome</th>
                <th className="text-left p-4">E-mail</th>
                <th className="text-left p-4">Telefone</th>
                <th className="text-left p-4">Pedidos</th>
                <th className="text-left p-4">Newsletter</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} className="border-t border-[#2e2e2e]" data-testid={`admin-customer-${c.id}`}>
                  <td className="p-4 text-white">{c.name}</td>
                  <td className="p-4 text-gray-400">{c.email}</td>
                  <td className="p-4 text-gray-400">{c.phone || "—"}</td>
                  <td className="p-4 text-white">{c.orders_count}</td>
                  <td className="p-4">{c.newsletter ? <span className="text-[#009B3A]">Sim</span> : <span className="text-gray-600">Não</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
