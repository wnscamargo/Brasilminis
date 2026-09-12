import { useState } from "react";
import { Link } from "react-router-dom";
import { Send } from "lucide-react";
import { toast } from "sonner";
import BrandLogo from "@/components/BrandLogo";
import SocialLinks from "@/components/SocialLinks";
import { useSiteConfig } from "@/context/SiteConfigContext";

export default function Footer() {
  const [email, setEmail] = useState("");
  const { social_links } = useSiteConfig();

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
          <div className="mb-4 inline-flex items-start" data-testid="footer-brand">
            <BrandLogo variant="footer" />
            <sup className="text-gray-400 text-[10px] ml-0.5 mt-0.5">®</sup>
          </div>
          <p className="text-sm text-gray-500 leading-relaxed">
            Sua paixão em miniatura. As melhores marcas e edições exclusivas do universo automotivo.
          </p>
        </div>
        <FooterCol title="Institucional" links={[["Sobre nós", "/sobre"], ["Marcas", "/marcas"], ["Lançamentos", "/produtos?badge=LANÇAMENTO"], ["Promoções", "/produtos?on_sale=true"]]} />
        <FooterCol title="Ajuda" links={[["Contato", "/contato"], ["Trocas e devoluções", "/trocas-devolucoes"], ["Frete e entrega", "/frete-entrega"], ["Minha conta", "/conta"]]} />
        <div>
          <h4 className="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">
            Redes Sociais
          </h4>
          <SocialLinks social={social_links || {}} />
          <p className="text-xs text-gray-600 mt-6">Pagamento seguro • PIX • Cartão • Boleto</p>
        </div>
      </div>

      <div className="border-t border-[#2e2e2e] py-5">
        <p className="text-center text-xs text-gray-600">
          © {new Date().getFullYear()} Brasil Minis<sup className="text-[8px]">®</sup>. Todos os direitos reservados.
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
