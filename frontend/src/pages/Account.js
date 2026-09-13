import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Package, MapPin, User, KeyRound, LogOut, Plus, Trash2, ShieldCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";
import { useAuth } from "@/context/AuthContext";
import { useCepAutofill, maskCep } from "@/lib/cep";
import { maskCpf, normalizeCpf } from "@/lib/cpf";

const TABS = [
  { k: "orders", l: "Pedidos", icon: Package },
  { k: "addresses", l: "Endereços", icon: MapPin },
  { k: "data", l: "Meus Dados", icon: User },
  { k: "password", l: "Senha", icon: KeyRound },
];

export default function Account() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [addresses, setAddresses] = useState([]);

  useEffect(() => {
    api.get("/orders").then((r) => setOrders(r.data)).catch(() => {});
    api.get("/account/addresses").then((r) => setAddresses(r.data)).catch(() => {});
  }, []);

  const doLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
      <div className="flex items-center gap-4 mb-8">
        <div className="h-14 w-14 rounded-full bg-[#1E3A8A] grid place-items-center text-white font-display font-bold text-xl">
          {user.name[0]}
        </div>
        <div>
          <h1 className="text-2xl font-display font-black uppercase text-white">Olá, {user.name.split(" ")[0]}</h1>
          <p className="text-gray-500 text-sm">{user.email}</p>
        </div>
        {user.role === "admin" && (
          <Link to="/admin" className="ml-auto bg-[#009B3A] text-white text-sm font-semibold rounded-full px-5 py-2.5 flex items-center gap-2" data-testid="go-admin">
            <ShieldCheck size={16} /> Painel Admin
          </Link>
        )}
      </div>

      <div className="grid lg:grid-cols-4 gap-8">
        <aside className="bm-card p-3 h-fit">
          {TABS.map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              data-testid={`account-tab-${t.k}`}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                tab === t.k ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <t.icon size={18} /> {t.l}
            </button>
          ))}
          <button onClick={doLogout} data-testid="logout-btn" className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors">
            <LogOut size={18} /> Sair
          </button>
        </aside>

        <div className="lg:col-span-3">
          {tab === "orders" && <Orders orders={orders} />}
          {tab === "addresses" && <Addresses addresses={addresses} setAddresses={setAddresses} />}
          {tab === "data" && <ProfileTab user={user} refreshUser={refreshUser} />}
          {tab === "password" && <PasswordTab />}
        </div>
      </div>
    </div>
  );
}

function Orders({ orders }) {
  if (orders.length === 0)
    return <div className="bm-card p-12 text-center text-gray-400">Você ainda não fez pedidos. <Link to="/produtos" className="text-[#FFC107]">Comprar agora</Link></div>;
  return (
    <div className="space-y-4">
      {orders.map((o) => (
        <div key={o.id} className="bm-card p-5" data-testid={`order-${o.order_number}`}>
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#2e2e2e]">
            <div>
              <span className="text-white font-display font-bold">#{o.order_number}</span>
              <span className="text-gray-500 text-xs ml-3">{new Date(o.created_at).toLocaleDateString("pt-BR")}</span>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-[#009B3A]/20 text-[#009B3A]">{o.status}</span>
          </div>
          <div className="flex gap-2 mt-3 flex-wrap">
            {o.items.map((i) => (
              <img key={i.product_id} src={i.image} alt={i.name} title={`${i.quantity}x ${i.name}`} className="h-14 w-14 rounded-lg object-cover" />
            ))}
          </div>
          <div className="flex justify-between mt-3 text-sm">
            <span className="text-gray-400">{o.items.length} item(s) · {o.payment_method.toUpperCase()}</span>
            <span className="text-white font-bold">{formatBRL(o.total)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function Addresses({ addresses, setAddresses }) {
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ label: "Casa", recipient: "", street: "", number: "", complement: "", district: "", city: "", state: "", zip: "" });
  const [cepLoading, setCepLoading] = useState(false);
  const [cepError, setCepError] = useState("");

  const cepAutofill = useCepAutofill(
    (data) => {
      setForm((f) => ({ ...f, street: data.street || f.street, district: data.district || f.district, city: data.city || f.city, state: data.uf || f.state }));
      setCepLoading(false); setCepError("");
    },
    { onStart: () => { setCepLoading(true); setCepError(""); }, onError: () => { setCepLoading(false); setCepError("CEP não encontrado. Preencha manualmente."); } }
  );

  const onZip = (v) => {
    const masked = maskCep(v);
    setForm((f) => ({ ...f, zip: masked }));
    cepAutofill(v);
  };

  const save = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post("/account/addresses", form);
      setAddresses(data);
      setShow(false);
      setForm({ label: "Casa", recipient: "", street: "", number: "", complement: "", district: "", city: "", state: "", zip: "" });
      toast.success("Endereço salvo");
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  const del = async (id) => {
    const { data } = await api.delete(`/account/addresses/${id}`);
    setAddresses(data);
  };

  const inputCls = "bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";

  return (
    <div>
      <button onClick={() => setShow(!show)} data-testid="add-address-btn" className="mb-4 bg-[#1E3A8A] text-white font-semibold rounded-full px-5 py-2.5 flex items-center gap-2">
        <Plus size={16} /> Novo endereço
      </button>
      {show && (
        <form onSubmit={save} className="bm-card p-5 mb-4 grid grid-cols-2 gap-3">
          <input required placeholder="Destinatário" value={form.recipient} onChange={(e)=>setForm({...form,recipient:e.target.value})} data-testid="new-addr-recipient" className={`${inputCls} col-span-2`} />
          <div className="relative col-span-2 sm:col-span-1">
            <input required placeholder="CEP" value={form.zip} onChange={(e)=>onZip(e.target.value)} data-testid="new-addr-zip" inputMode="numeric" className={`${inputCls} w-full`} />
            {cepLoading && <Loader2 size={16} className="absolute right-3 top-3 animate-spin text-[#FFC107]" data-testid="addr-cep-loading" />}
          </div>
          <input required placeholder="Rua" value={form.street} onChange={(e)=>setForm({...form,street:e.target.value})} data-testid="new-addr-street" className={inputCls} />
          <input required placeholder="Número" value={form.number} onChange={(e)=>setForm({...form,number:e.target.value})} data-testid="new-addr-number" className={inputCls} />
          <input placeholder="Complemento (opcional)" value={form.complement} onChange={(e)=>setForm({...form,complement:e.target.value})} data-testid="new-addr-complement" className={inputCls} />
          <input required placeholder="Bairro" value={form.district} onChange={(e)=>setForm({...form,district:e.target.value})} data-testid="new-addr-district" className={inputCls} />
          <input required placeholder="Cidade" value={form.city} onChange={(e)=>setForm({...form,city:e.target.value})} data-testid="new-addr-city" className={inputCls} />
          <input required placeholder="Estado (UF)" value={form.state} onChange={(e)=>setForm({...form,state:e.target.value})} data-testid="new-addr-state" className={inputCls} />
          {cepError && <p className="col-span-2 text-xs text-[#FFC107]" data-testid="addr-cep-error">{cepError}</p>}
          <button className="col-span-2 bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">Salvar endereço</button>
        </form>
      )}
      {addresses.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum endereço cadastrado.</div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {addresses.map((a) => (
            <div key={a.id} className="bm-card p-5">
              <div className="flex justify-between">
                <span className="text-[#FFC107] text-xs font-bold uppercase">{a.label}{a.is_default && " · Padrão"}</span>
                <button onClick={() => del(a.id)} className="text-gray-500 hover:text-red-400"><Trash2 size={16} /></button>
              </div>
              <p className="text-white text-sm mt-2">{a.recipient}</p>
              <p className="text-gray-400 text-sm">{a.street}, {a.number} {a.complement}</p>
              <p className="text-gray-400 text-sm">{a.district} · {a.city}/{a.state}</p>
              <p className="text-gray-500 text-xs mt-1">CEP {a.zip}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ProfileTab({ user, refreshUser }) {
  const [form, setForm] = useState({ name: user.name, phone: user.phone || "", cpf: user.cpf ? maskCpf(user.cpf) : "", newsletter: user.newsletter });
  const save = async (e) => {
    e.preventDefault();
    try {
      await api.put("/account/profile", { ...form, cpf: normalizeCpf(form.cpf) });
      await refreshUser();
      toast.success("Dados atualizados");
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  return (
    <form onSubmit={save} className="bm-card p-6 space-y-4 max-w-lg">
      <div><label className="text-xs text-gray-500 block mb-1">Nome</label>
        <input value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="profile-name" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" /></div>
      <div><label className="text-xs text-gray-500 block mb-1">E-mail</label>
        <input value={user.email} disabled className="w-full bg-[#0a0a0a] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-gray-500" /></div>
      <div><label className="text-xs text-gray-500 block mb-1">CPF{!user.cpf && <span className="text-[#FFC107]"> · complete seu cadastro</span>}</label>
        <input value={form.cpf} onChange={(e)=>setForm({...form,cpf:maskCpf(e.target.value)})} data-testid="profile-cpf" placeholder="000.000.000-00" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" /></div>
      <div><label className="text-xs text-gray-500 block mb-1">Telefone</label>
        <input value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})} data-testid="profile-phone" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" /></div>
      <label className="flex items-center gap-2 text-sm text-gray-400">
        <input type="checkbox" checked={form.newsletter} onChange={(e)=>setForm({...form,newsletter:e.target.checked})} className="accent-[#FFC107]" /> Receber newsletter
      </label>
      <button data-testid="profile-save" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-6 py-3">Salvar alterações</button>
    </form>
  );
}

function PasswordTab() {
  const [form, setForm] = useState({ current_password: "", new_password: "" });
  const save = async (e) => {
    e.preventDefault();
    try {
      await api.put("/account/password", form);
      setForm({ current_password: "", new_password: "" });
      toast.success("Senha atualizada");
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  return (
    <form onSubmit={save} className="bm-card p-6 space-y-4 max-w-lg">
      <input type="password" required placeholder="Senha atual" value={form.current_password} onChange={(e)=>setForm({...form,current_password:e.target.value})} data-testid="current-password" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
      <input type="password" required placeholder="Nova senha" value={form.new_password} onChange={(e)=>setForm({...form,new_password:e.target.value})} data-testid="new-password" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
      <button data-testid="password-save" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-6 py-3">Alterar senha</button>
    </form>
  );
}
