import { useState } from "react";
import { Link } from "react-router-dom";
import { Instagram, Facebook, Youtube, MessageCircle, Send } from "lucide-react";
import { toast } from "sonner";
import { LOGO_HEADER } from "@/lib/brand";

export default function Footer() {
  const [email, setEmail] = useState("");

  const subscribe = (e) => {
    e.preventDefault();
    if (!email) return;
    toast.success("Inscrição confirmada! Bem-vindo ao clube Brasil Minis.");
    setEmail("");
  };

  return (
    <footer className="mt-24 border-t border-[#2e2e2e] bg-[#0d0d0d]">
      <div className="bm-stripe" />
      {/* newsletter */}
      <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-14">
        <div className="bm-card p-8 lg:p-12 flex flex-col lg:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-2xl font-display font-bold text-white uppercase tracking-tight">
              Entre para o clube
            </h3>
            <p className="text-gray-400 mt-2">
              Receba lançamentos, Treasure Hunts e promoções exclusivas antes de todo mundo.
            </p>
          </div>
          <form onSubmit={subscribe} className="flex w-full lg:w-auto gap-2">
            <input
              data-testid="newsletter-input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Seu melhor e-mail"
              className="flex-1 lg:w-80 bg-[#111111] border border-[#2e2e2e] rounded-full px-5 py-3 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-[#FFC107]"
            />
            <button
              data-testid="newsletter-submit"
              className="bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-6 py-3 hover:bg-[#e0a800] transition-colors flex items-center gap-2"
            >
              <Send size={16} /> Assinar
            </button>
          </form>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-4 lg:px-8 pb-12 grid grid-cols-2 md:grid-cols-4 gap-8">
        <div className="col-span-2 md:col-span-1">
          <img src={LOGO_HEADER} alt="Brasil Minis" className="h-10 w-auto mb-4" />
          <p className="text-sm text-gray-500 leading-relaxed">
            Sua paixão em miniatura. As melhores marcas e edições exclusivas do universo automotivo.
          </p>
        </div>
        <FooterCol title="Institucional" links={[["Sobre nós", "/contato"], ["Marcas", "/marcas"], ["Lançamentos", "/produtos?badge=LANÇAMENTO"], ["Promoções", "/produtos?on_sale=true"]]} />
        <FooterCol title="Ajuda" links={[["Contato", "/contato"], ["Trocas e devoluções", "/contato"], ["Frete e entrega", "/contato"], ["Minha conta", "/conta"]]} />
        <div>
          <h4 className="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">
            Redes Sociais
          </h4>
          <div className="flex gap-3">
            {[Instagram, Facebook, Youtube, MessageCircle].map((Icon, i) => (
              <a
                key={i}
                href="#"
                className="h-10 w-10 grid place-items-center rounded-full border border-[#2e2e2e] text-gray-300 hover:border-[#FFC107] hover:text-[#FFC107] transition-colors"
              >
                <Icon size={18} />
              </a>
            ))}
          </div>
          <p className="text-xs text-gray-600 mt-6">Pagamento seguro • PIX • Cartão • Boleto</p>
        </div>
      </div>

      <div className="border-t border-[#2e2e2e] py-5">
        <p className="text-center text-xs text-gray-600">
          © {new Date().getFullYear()} Brasil Minis. Todos os direitos reservados.
        </p>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }) {
  return (
    <div>
      <h4 className="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">
        {title}
      </h4>
      <ul className="space-y-2.5">
        {links.map(([label, to]) => (
          <li key={label}>
            <Link to={to} className="text-sm text-gray-400 hover:text-[#FFC107] transition-colors">
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
