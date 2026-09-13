import { useState, useEffect } from "react";
import { Mail, Phone, MapPin, Send, MessageCircle, Clock } from "lucide-react";
import { toast } from "sonner";
import { useSiteContent } from "@/lib/siteContent";
import SocialLinks from "@/components/SocialLinks";
import MarkdownContent from "@/components/MarkdownContent";

export default function Contact() {
  const { pages, social } = useSiteContent();
  const page = pages.contact || {};
  const [form, setForm] = useState({ name: "", email: "", message: "" });

  useEffect(() => {
    document.title = page.seo_title || page.title || "Contato";
    return () => { document.title = "Brasil Minis"; };
  }, [page]);

  const submit = (e) => {
    e.preventDefault();
    toast.success("Mensagem enviada! Retornaremos em breve.");
    setForm({ name: "", email: "", message: "" });
  };

  const contactItems = [
    page.email && { key: "email", icon: Mail, l: "E-mail", v: page.email, href: `mailto:${page.email}` },
    page.phone && { key: "phone", icon: Phone, l: "Telefone", v: page.phone, href: `tel:${page.phone.replace(/\D/g, "")}` },
    page.whatsapp && { key: "whatsapp", icon: MessageCircle, l: "WhatsApp", v: "Chamar no WhatsApp", href: page.whatsapp },
    page.hours && { key: "hours", icon: Clock, l: "Atendimento", v: page.hours },
    page.address && { key: "address", icon: MapPin, l: "Endereço", v: page.address },
  ].filter(Boolean);

  return (
    <div className="max-w-[1100px] mx-auto px-4 lg:px-8 py-12" data-testid="contact-page">
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <h1 className="text-3xl lg:text-5xl font-display font-black uppercase text-white" data-testid="contact-title">{page.title || "Contato"}</h1>
      {page.subtitle && <p className="text-gray-500 mt-2 mb-8">{page.subtitle}</p>}

      {page.content && <div className="bm-card p-6 mb-8"><MarkdownContent>{page.content}</MarkdownContent></div>}

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          {contactItems.map((c) => (
            <div key={c.l} className="bm-card p-5 flex items-center gap-4" data-testid={`contact-item-${c.key}`}>
              <div className="h-11 w-11 grid place-items-center rounded-full border border-[#2e2e2e] text-[#FFC107] shrink-0"><c.icon size={20} /></div>
              <div className="min-w-0">
                <p className="text-xs text-gray-500 uppercase">{c.l}</p>
                {c.href ? (
                  <a href={c.href} target="_blank" rel="noopener noreferrer" className="text-white font-medium hover:text-[#FFC107] break-words">{c.v}</a>
                ) : (
                  <p className="text-white font-medium break-words">{c.v}</p>
                )}
              </div>
            </div>
          ))}
          <SocialLinks social={social} className="pt-2" />
        </div>

        <form onSubmit={submit} className="bm-card p-6 space-y-4">
          <input required placeholder="Seu nome" value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} data-testid="contact-name" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <input required type="email" placeholder="Seu e-mail" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} data-testid="contact-email" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <textarea required rows={5} placeholder="Sua mensagem" value={form.message} onChange={(e)=>setForm({...form,message:e.target.value})} data-testid="contact-message" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
          <button data-testid="contact-submit" className="bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-6 py-3 flex items-center gap-2"><Send size={16} /> Enviar mensagem</button>
        </form>
      </div>
    </div>
  );
}
