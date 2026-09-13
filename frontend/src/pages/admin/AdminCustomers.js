import { useEffect, useState } from "react";
import { Pencil, X, Trash2, AlertTriangle, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { maskCpf } from "@/lib/cpf";

const SCOPES = [["active", "Ativos"], ["deleted", "Excluídos"], ["all", "Todos"]];

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  const [scope, setScope] = useState("active");
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const load = () => api.get(`/admin/customers?scope=${scope}`).then((r) => setCustomers(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [scope]);

  const restore = async (c) => {
    try {
      await api.post(`/admin/customers/${c.id}/restore`);
      toast.success("Cliente restaurado");
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Clientes</h1>
        <div className="inline-flex bg-[#1f1f1f] border border-[#2e2e2e] rounded-full p-1" data-testid="customers-scope">
          {SCOPES.map(([v, l]) => (
            <button key={v} onClick={() => setScope(v)} data-testid={`customers-scope-${v}`}
              className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide ${scope === v ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white"}`}>{l}</button>
          ))}
        </div>
      </div>
      {customers.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum cliente nesta visão.</div>
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
                <tr key={c.id} className={`border-t border-[#2e2e2e] ${c.deleted_at ? "opacity-60" : ""}`} data-testid={`admin-customer-${c.id}`}>
                  <td className="p-4 text-white">
                    {c.name}
                    {c.deleted_at && <span className="ml-2 text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full uppercase" data-testid={`customer-deleted-badge-${c.id}`}>Excluído</span>}
                    {c.anonymized_at && <span className="ml-2 text-[10px] bg-gray-500/20 text-gray-400 px-2 py-0.5 rounded-full uppercase">Anonimizado</span>}
                  </td>
                  <td className="p-4 text-gray-400">{c.email}</td>
                  <td className="p-4 text-gray-400" data-testid={`customer-cpf-${c.id}`}>{c.cpf ? maskCpf(c.cpf) : "—"}</td>
                  <td className="p-4 text-gray-400">{c.phone || "—"}</td>
                  <td className="p-4 text-white">{c.orders_count}</td>
                  <td className="p-4">{c.newsletter ? <span className="text-[#009B3A]">Sim</span> : <span className="text-gray-600">Não</span>}</td>
                  <td className="p-4 text-right whitespace-nowrap">
                    {c.deleted_at ? (
                      <button onClick={() => restore(c)} data-testid={`restore-customer-${c.id}`} className="inline-flex items-center gap-1 text-xs text-[#009B3A] hover:text-[#00c04a] font-semibold">
                        <RotateCcw size={14} /> Restaurar
                      </button>
                    ) : (
                      <div className="inline-flex items-center gap-3">
                        <button onClick={() => setEditing(c)} data-testid={`edit-customer-${c.id}`} className="text-[#FFC107]"><Pencil size={15} /></button>
                        <button onClick={() => setDeleting(c)} data-testid={`delete-customer-${c.id}`} className="inline-flex items-center gap-1 text-xs text-red-400 hover:text-red-300 font-semibold">
                          <Trash2 size={14} /> Excluir
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && <EditCustomer c={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
      {deleting && <DeleteCustomerModal c={deleting} onClose={() => setDeleting(null)} onDeleted={() => { setDeleting(null); load(); }} />}
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

function DeleteCustomerModal({ c, onClose, onDeleted }) {
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState("");
  const [anonymize, setAnonymize] = useState(false);
  const [busy, setBusy] = useState(false);
  const canDelete = reason.trim().length > 0 && confirm === "EXCLUIR";

  const doDelete = async () => {
    if (!canDelete) return;
    setBusy(true);
    try {
      await api.delete(`/admin/customers/${c.id}`, { data: { reason: reason.trim(), confirm, anonymize } });
      toast.success("Cliente excluído");
      onDeleted();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="delete-customer-modal">
      <div className="bm-card p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white flex items-center gap-2"><AlertTriangle className="text-red-400" size={20} /> Excluir cliente</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="text-sm text-gray-300 space-y-1 bg-[#111] border border-[#2e2e2e] rounded-lg p-3 mb-4">
          <div className="flex justify-between"><span className="text-gray-500">Cliente</span><span className="text-white font-semibold">{c.name}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">E-mail</span><span>{c.email}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">CPF</span><span>{c.cpf ? maskCpf(c.cpf) : "—"}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Pedidos</span><span>{c.orders_count}</span></div>
        </div>
        <p className="text-xs text-gray-400 mb-3">O histórico de pedidos, pagamentos e envios é preservado. O cliente não conseguirá mais fazer login.</p>
        <label className="text-xs text-gray-500 block mb-1">Motivo da exclusão</label>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="delete-customer-reason" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-3" />
        <label className="flex items-start gap-2 mb-3 cursor-pointer">
          <input type="checkbox" checked={anonymize} onChange={(e) => setAnonymize(e.target.checked)} data-testid="delete-customer-anonymize" className="mt-0.5" />
          <span className="text-xs text-gray-400">Anonimizar dados pessoais (LGPD) — apaga nome, e-mail e CPF, liberando-os para novo cadastro. O histórico operacional é mantido.</span>
        </label>
        <label className="text-xs text-gray-500 block mb-1">Para confirmar a exclusão, digite <b className="text-red-400">EXCLUIR</b></label>
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="delete-customer-confirm-input" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-4" />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-300 hover:text-white">Cancelar</button>
          <button onClick={doDelete} disabled={!canDelete || busy} data-testid="delete-customer-confirm-btn" className="bg-red-500 text-white font-bold rounded-full px-5 py-2 text-sm disabled:opacity-40">
            {busy ? "Excluindo..." : "EXCLUIR CLIENTE"}
          </button>
        </div>
      </div>
    </div>
  );
}
