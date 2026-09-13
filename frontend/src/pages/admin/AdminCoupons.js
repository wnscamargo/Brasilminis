import { useEffect, useState } from "react";
import { Ticket, Plus, Trash2, Wand2, X, Save } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const EMPTY = {
  code: "", type: "percent", value: 10, min_order: 0, max_discount: "",
  active: true, description: "", starts_at: "", expires_at: "",
  usage_limit: "", per_user_limit: "", first_purchase_only: false,
  free_shipping: false, allow_stacking: false, scope_type: "all",
  scope_category_ids: [], scope_product_ids: [],
};

export default function AdminCoupons() {
  const [coupons, setCoupons] = useState([]);
  const [cats, setCats] = useState([]);
  const [products, setProducts] = useState([]);
  const [editing, setEditing] = useState(null);

  const load = () => api.get("/admin/coupons").then((r) => setCoupons(r.data));
  useEffect(() => {
    load();
    api.get("/categories?tree=true").then((r) => {
      const flat = [];
      (r.data || []).forEach((m) => { flat.push({ id: m.id, name: m.name }); (m.children || []).forEach((s) => flat.push({ id: s.id, name: `— ${s.name}` })); });
      setCats(flat);
    });
    api.get("/products?limit=200").then((r) => setProducts(r.data.items || []));
  }, []);

  const del = async (code) => {
    if (!window.confirm(`Excluir o cupom ${code}?`)) return;
    await api.delete(`/admin/coupons/${code}`);
    toast.success("Cupom removido");
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Ticket className="text-[#FFC107]" size={28} />
          <h1 className="text-3xl font-display font-black uppercase text-white">Cupons de Desconto</h1>
        </div>
        <button onClick={() => setEditing({ ...EMPTY, _new: true })} data-testid="new-coupon-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Plus size={16} /> Novo cupom</button>
      </div>

      {coupons.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum cupom cadastrado.</div>
      ) : (
        <div className="bm-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111] text-gray-500 uppercase text-xs">
              <tr><th className="text-left p-4">Código</th><th className="text-left p-4">Desconto</th><th className="text-left p-4">Mín.</th><th className="text-left p-4">Usos</th><th className="text-left p-4">Validade</th><th className="text-left p-4">Status</th><th className="p-4"></th></tr>
            </thead>
            <tbody>
              {coupons.map((c) => (
                <tr key={c.code} className="border-t border-[#2e2e2e]" data-testid={`coupon-row-${c.code}`}>
                  <td className="p-4 text-white font-bold">{c.code}{c.free_shipping && <span className="ml-2 text-[10px] bg-[#009B3A]/20 text-[#009B3A] px-2 py-0.5 rounded-full">FRETE GRÁTIS</span>}</td>
                  <td className="p-4 text-gray-300">{c.type === "percent" ? `${c.value}%` : `R$ ${c.value.toFixed(2)}`}</td>
                  <td className="p-4 text-gray-400">R$ {Number(c.min_order).toFixed(2)}</td>
                  <td className="p-4 text-gray-400">{c.used_count}{c.usage_limit ? `/${c.usage_limit}` : ""}</td>
                  <td className="p-4 text-gray-400 text-xs">{c.expires_at ? new Date(c.expires_at).toLocaleDateString("pt-BR") : "—"}</td>
                  <td className="p-4"><span className={`text-xs px-2 py-1 rounded-full ${c.active ? "bg-[#009B3A]/20 text-[#009B3A]" : "bg-gray-600/30 text-gray-400"}`}>{c.active ? "Ativo" : "Inativo"}</span></td>
                  <td className="p-4 text-right whitespace-nowrap">
                    <button onClick={() => setEditing({ ...c, max_discount: c.max_discount ?? "", usage_limit: c.usage_limit ?? "", per_user_limit: c.per_user_limit ?? "", starts_at: c.starts_at || "", expires_at: c.expires_at || "" })} data-testid={`edit-coupon-${c.code}`} className="text-[#FFC107] text-xs font-semibold mr-4">Editar</button>
                    <button onClick={() => del(c.code)} data-testid={`delete-coupon-${c.code}`} className="text-red-400"><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && <CouponForm data={editing} cats={cats} products={products} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function CouponForm({ data, cats, products, onClose, onSaved }) {
  const [f, setF] = useState(data);
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const toggleId = (key, id) => setF((p) => ({ ...p, [key]: p[key].includes(id) ? p[key].filter((x) => x !== id) : [...p[key], id] }));

  const gen = async () => {
    const { data: d } = await api.post("/admin/coupons/generate-code", { prefix: "BM", length: 8 });
    set("code", d.code);
  };

  const save = async () => {
    setBusy(true);
    const body = {
      ...f,
      value: Number(f.value),
      min_order: Number(f.min_order) || 0,
      max_discount: f.max_discount === "" ? null : Number(f.max_discount),
      usage_limit: f.usage_limit === "" ? null : Number(f.usage_limit),
      per_user_limit: f.per_user_limit === "" ? null : Number(f.per_user_limit),
      starts_at: f.starts_at || null,
      expires_at: f.expires_at || null,
    };
    try {
      if (f._new) await api.post("/admin/coupons", body);
      else await api.put(`/admin/coupons/${f.code}`, body);
      toast.success("Cupom salvo");
      onSaved();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); setBusy(false); }
  };

  const inp = "w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";
  const Chk = ({ k, l }) => (<label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer"><input type="checkbox" checked={!!f[k]} onChange={(e) => set(k, e.target.checked)} data-testid={`coupon-${k}`} className="accent-[#FFC107] h-4 w-4" />{l}</label>);

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 overflow-y-auto p-4" data-testid="coupon-form-modal">
      <div className="bm-card p-6 max-w-2xl w-full mx-auto my-8">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-display font-black uppercase text-white">{f._new ? "Novo cupom" : `Editar ${f.code}`}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2 sm:col-span-1">
            <label className="text-xs text-gray-500 block mb-1">Código</label>
            <div className="flex gap-2">
              <input value={f.code} disabled={!f._new} onChange={(e) => set("code", e.target.value.toUpperCase())} data-testid="coupon-code" className={`${inp} disabled:opacity-60`} />
              {f._new && <button onClick={gen} data-testid="coupon-generate" title="Gerar código" className="bg-[#1E3A8A] text-white rounded-lg px-3"><Wand2 size={16} /></button>}
            </div>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="text-xs text-gray-500 block mb-1">Tipo</label>
            <select value={f.type} onChange={(e) => set("type", e.target.value)} data-testid="coupon-type" className={inp}><option value="percent">Percentual (%)</option><option value="fixed">Valor fixo (R$)</option></select>
          </div>
          <Num label="Valor do desconto" k="value" f={f} set={set} inp={inp} />
          <Num label="Desconto máximo (R$, opcional)" k="max_discount" f={f} set={set} inp={inp} />
          <Num label="Valor mínimo do pedido (R$)" k="min_order" f={f} set={set} inp={inp} />
          <div />
          <div className="col-span-2 sm:col-span-1">
            <label className="text-xs text-gray-500 block mb-1">Início (opcional)</label>
            <input type="datetime-local" value={f.starts_at ? f.starts_at.slice(0, 16) : ""} onChange={(e) => set("starts_at", e.target.value ? new Date(e.target.value).toISOString() : "")} data-testid="coupon-starts" className={inp} />
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="text-xs text-gray-500 block mb-1">Expiração (opcional)</label>
            <input type="datetime-local" value={f.expires_at ? f.expires_at.slice(0, 16) : ""} onChange={(e) => set("expires_at", e.target.value ? new Date(e.target.value).toISOString() : "")} data-testid="coupon-expires" className={inp} />
          </div>
          <Num label="Limite total de usos (opcional)" k="usage_limit" f={f} set={set} inp={inp} />
          <Num label="Limite por cliente (opcional)" k="per_user_limit" f={f} set={set} inp={inp} />
          <div className="col-span-2">
            <label className="text-xs text-gray-500 block mb-1">Descrição</label>
            <input value={f.description || ""} onChange={(e) => set("description", e.target.value)} data-testid="coupon-description" className={inp} />
          </div>
          <div className="col-span-2 grid grid-cols-2 gap-3 py-2 border-y border-[#2e2e2e]">
            <Chk k="active" l="Ativo" />
            <Chk k="first_purchase_only" l="Somente 1ª compra" />
            <Chk k="free_shipping" l="Frete grátis" />
            <Chk k="allow_stacking" l="Permitir cumulativo" />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-gray-500 block mb-1">Aplicável a</label>
            <select value={f.scope_type} onChange={(e) => set("scope_type", e.target.value)} data-testid="coupon-scope" className={inp}>
              <option value="all">Todos os produtos</option>
              <option value="categories">Categorias específicas</option>
              <option value="products">Produtos específicos</option>
            </select>
          </div>
          {f.scope_type === "categories" && (
            <div className="col-span-2 max-h-40 overflow-y-auto border border-[#2e2e2e] rounded-lg p-3 space-y-1" data-testid="coupon-categories">
              {cats.map((c) => (
                <label key={c.id} className="flex items-center gap-2 text-sm text-gray-300"><input type="checkbox" checked={f.scope_category_ids.includes(c.id)} onChange={() => toggleId("scope_category_ids", c.id)} className="accent-[#FFC107]" />{c.name}</label>
              ))}
            </div>
          )}
          {f.scope_type === "products" && (
            <div className="col-span-2 max-h-40 overflow-y-auto border border-[#2e2e2e] rounded-lg p-3 space-y-1" data-testid="coupon-products">
              {products.map((p) => (
                <label key={p.id} className="flex items-center gap-2 text-sm text-gray-300"><input type="checkbox" checked={f.scope_product_ids.includes(p.id)} onChange={() => toggleId("scope_product_ids", p.id)} className="accent-[#FFC107]" />{p.name}</label>
              ))}
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-300">Cancelar</button>
          <button onClick={save} disabled={busy} data-testid="save-coupon-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-2.5 flex items-center gap-2"><Save size={16} /> {busy ? "Salvando..." : "Salvar"}</button>
        </div>
      </div>
    </div>
  );
}

function Num({ label, k, f, set, inp }) {
  return (
    <div className="col-span-2 sm:col-span-1">
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input type="number" value={f[k]} onChange={(e) => set(k, e.target.value)} data-testid={`coupon-${k}`} className={inp} />
    </div>
  );
}
