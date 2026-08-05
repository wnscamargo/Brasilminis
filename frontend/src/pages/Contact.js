import { useState } from "react";
import { Mail, Phone, MapPin, Send, Instagram, MessageCircle } from "lucide-react";
import { toast } from "sonner";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const submit = (e) => {
    e.preventDefault();
    toast.success("Mensagem enviada! Retornaremos em breve.");
    setForm({ name: "", email: "", message: "" });
  };
  return (
    <div className="max-w-[1100px] mx-auto px-4 lg:px-8 py-12">
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <h1 className="text-3xl lg:text-5xl font-display font-black uppercase text-white">Contato</h1>
      <p className="text-gray-500 mt-2 mb-10">Fale com nossa equipe de especialistas em colecionismo.</p>
      <div className="grid lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          {[
            { icon: Mail, l: "E-mail", v: "contato@brasilminis.com.br" },
            { icon: Phone, l: "WhatsApp", v: "(11) 99999-0000" },
            { icon: MapPin, l: "Endereço", v: "São Paulo · SP · Brasil" },
          ].map((c) => (
            <div key={c.l} className="bm-card p-5 flex items-center gap-4">
              <div className="h-11 w-11 grid place-items-center rounded-full border border-[#2e2e2e] text-[#FFC107]"><c.icon size={20} /></div>
              <div><p className="text-xs text-gray-500 uppercase">{c.l}</p><p className="text-white font-medium">{c.v}</p></div>
            </div>
          ))}
          <div className="flex gap-3 pt-2">
            {[Instagram, MessageCircle].map((Icon, i) => (
              <a key={i} href="#" className="h-11 w-11 grid place-items-center rounded-full border border-[#2e2e2e] text-gray-300 hover:text-[#FFC107] hover:border-[#FFC107] transition-colors"><Icon size={18} /></a>
            ))}
          </div>
        </div>
        <form onSubmit={submit} className="bm-card p-6 space-y-4">
          <input required placeholder="Seu nome" value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <input required type="email" placeholder="Seu e-mail" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <textarea required rows={5} placeholder="Sua mensagem" value={form.message} onChange={(e)=>setForm({...form,message:e.target.value})} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <button className="bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-6 py-3 flex items-center gap-2"><Send size={16} /> Enviar mensagem</button>
        </form>
      </div>
    </div>
  );
}
