import { useEffect, useState } from "react";
import { Pencil, X } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { maskCpf } from "@/lib/cpf";

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/customers").then((r) => setCustomers(r.data));
  useEffect(() => { load(); }, []);

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
                <th className="text-left p-4">CPF</th>
                <th className="text-left p-4">Telefone</th>
                <th className="text-left p-4">Pedidos</th>
                <th className="text-left p-4">Newsletter</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} className="border-t border-[#2e2e2e]" data-testid={`admin-customer-${c.id}`}>
                  <td className="p-4 text-white">{c.name}</td>
                  <td className="p-4 text-gray-400">{c.email}</td>
                  <td className="p-4 text-gray-400" data-testid={`customer-cpf-${c.id}`}>{c.cpf ? maskCpf(c.cpf) : "—"}</td>
                  <td className="p-4 text-gray-400">{c.phone || "—"}</td>
                  <td className="p-4 text-white">{c.orders_count}</td>
                  <td className="p-4">{c.newsletter ? <span className="text-[#009B3A]">Sim</span> : <span className="text-gray-600">Não</span>}</td>
                  <td className="p-4 text-right">
                    <button onClick={() => setEditing(c)} data-testid={`edit-customer-${c.id}`} className="text-[#FFC107]"><Pencil size={15} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && <EditCustomer c={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function EditCustomer({ c, onClose, onSaved }) {
  const [name, setName] = useState(c.name || "");
  const [phone, setPhone] = useState(c.phone || "");
  const [cpf, setCpf] = useState(c.cpf ? maskCpf(c.cpf) : "");
  const [busy, setBusy] = useState(false);
  const inp = "w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";

  const save = async () => {
    setBusy(true);
    try {
      await api.put(`/admin/customers/${c.id}`, { name, phone, cpf });
      toast.success("Cliente atualizado");
      onSaved();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="edit-customer-modal">
      <div className="bm-card p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white">Editar cliente</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div><label className="text-xs text-gray-500 block mb-1">Nome</label><input value={name} onChange={(e) => setName(e.target.value)} data-testid="edit-customer-name" className={inp} /></div>
          <div><label className="text-xs text-gray-500 block mb-1">CPF</label><input value={cpf} onChange={(e) => setCpf(maskCpf(e.target.value))} data-testid="edit-customer-cpf" placeholder="000.000.000-00" className={inp} /></div>
          <div><label className="text-xs text-gray-500 block mb-1">Telefone</label><input value={phone} onChange={(e) => setPhone(e.target.value)} data-testid="edit-customer-phone" className={inp} /></div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-300">Cancelar</button>
          <button onClick={save} disabled={busy} data-testid="save-customer-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-5 py-2.5 text-sm">{busy ? "Salvando..." : "Salvar"}</button>
        </div>
      </div>
    </div>
  );
}
