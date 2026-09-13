import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, Heart, ShoppingCart, User, Menu, X, ChevronDown, ChevronRight } from "lucide-react";
import BrandLogo from "@/components/BrandLogo";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";
import { useCategories } from "@/context/CategoriesContext";

// Itens institucionais fixos (NÃO são categorias) — mantidos separados das categorias dinâmicas.
const INSTITUTIONAL_LEFT = [{ label: "Início", to: "/" }];
const INSTITUTIONAL_RIGHT = [
  { label: "Lançamentos", to: "/produtos?badge=LANÇAMENTO" },
  { label: "Promoções", to: "/produtos?on_sale=true" },
  { label: "Marcas", to: "/marcas" },
  { label: "Contato", to: "/contato" },
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const { count } = useCart();
  const { user } = useAuth();
  const { ids } = useFavorites();
  const { tree } = useCategories();
  const navigate = useNavigate();

  const submitSearch = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/produtos?search=${encodeURIComponent(q.trim())}`);
  };

  return (
    <header className="sticky top-0 z-50">
      <div className="bm-stripe" />
      <div className="bm-glass">
        <div className="max-w-[1400px] mx-auto px-4 lg:px-8">
          {/* top row */}
          <div className="flex items-center gap-4 h-20 md:h-24">
            <button className="lg:hidden text-white" onClick={() => setOpen(!open)} data-testid="mobile-menu-toggle" aria-label="Menu">
              {open ? <X size={26} /> : <Menu size={26} />}
            </button>

            <Link to="/" data-testid="logo-link" className="shrink-0 inline-flex items-start" aria-label="Brasil Minis® | Miniaturas Diecast">
              <BrandLogo variant="header" />
              <sup className="text-gray-400 text-[10px] ml-0.5 mt-1 select-none">®</sup>
            </Link>

            <form onSubmit={submitSearch} className="hidden md:flex flex-1 max-w-xl mx-4 relative">
              <input
                data-testid="search-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Buscar miniaturas, marcas, acessórios..."
                className="w-full bg-[#1f1f1f] border border-[#2e2e2e] rounded-full py-2.5 pl-5 pr-12 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-[#1E3A8A] transition-colors"
              />
              <button type="submit" data-testid="search-submit" className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white hover:bg-[#152b66] transition-colors">
                <Search size={16} />
              </button>
            </form>

            <div className="flex items-center gap-1 md:gap-2 ml-auto">
              <Link to={user ? "/conta" : "/login"} data-testid="account-link" className="flex items-center gap-2 px-3 py-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <User size={22} />
                <span className="hidden xl:inline text-sm">{user ? user.name.split(" ")[0] : "Entrar"}</span>
              </Link>
              <Link to="/favoritos" data-testid="favorites-link" className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <Heart size={22} />
                {ids.length > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-[#009B3A] text-white text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">{ids.length}</span>
                )}
              </Link>
              <Link to="/carrinho" data-testid="cart-link" className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <ShoppingCart size={22} />
                {count > 0 && (
                  <span data-testid="cart-count" className="absolute -top-0.5 -right-0.5 bg-[#FFC107] text-[#111111] text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">{count}</span>
                )}
              </Link>
            </div>
          </div>

          {/* nav row (desktop) */}
          <nav className="hidden lg:flex items-center gap-1 pb-3 -mt-1" data-testid="desktop-nav">
            {INSTITUTIONAL_LEFT.map((m) => (
              <NavLink key={m.label} to={m.to} label={m.label} />
            ))}
            {tree.map((cat) => (
              <CategoryMenuItem key={cat.id} cat={cat} />
            ))}
            {INSTITUTIONAL_RIGHT.map((m) => (
              <NavLink key={m.label} to={m.to} label={m.label} />
            ))}
          </nav>
        </div>
      </div>

      {/* mobile menu */}
      {open && (
        <div className="lg:hidden bg-[#1f1f1f] border-b border-[#2e2e2e] px-4 py-4 max-h-[80vh] overflow-y-auto" data-testid="mobile-nav">
          <form onSubmit={submitSearch} className="relative mb-4">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar..." className="w-full bg-[#111111] border border-[#2e2e2e] rounded-full py-2.5 pl-4 pr-12 text-sm text-white" />
            <button type="submit" className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white"><Search size={16} /></button>
          </form>

          {INSTITUTIONAL_LEFT.map((m) => (
            <Link key={m.label} to={m.to} onClick={() => setOpen(false)} className="block px-2 py-2.5 text-sm uppercase tracking-wide font-medium text-gray-200 hover:text-[#FFC107]">{m.label}</Link>
          ))}

          <div className="my-2 border-t border-[#2e2e2e]" />
          {tree.map((cat) => (
            <MobileCategory key={cat.id} cat={cat} close={() => setOpen(false)} />
          ))}
          <div className="my-2 border-t border-[#2e2e2e]" />

          {INSTITUTIONAL_RIGHT.map((m) => (
            <Link key={m.label} to={m.to} onClick={() => setOpen(false)} className="block px-2 py-2.5 text-sm uppercase tracking-wide font-medium text-gray-200 hover:text-[#FFC107]">{m.label}</Link>
          ))}
        </div>
      )}
    </header>
  );
}

function NavLink({ to, label }) {
  return (
    <Link to={to} data-testid={`nav-${label.toLowerCase().replace(/[^a-z]/g, "")}`} className="px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-[#FFC107] transition-colors">
      {label}
    </Link>
  );
}

// Desktop: categoria principal clicável + dropdown de subcategorias no hover.
function CategoryMenuItem({ cat }) {
  const kids = cat.children || [];
  const slugTest = cat.slug.replace(/[^a-z0-9]/g, "");
  return (
    <div className="relative group" data-testid={`nav-cat-${slugTest}`}>
      <Link
        to={`/produtos?category=${cat.slug}`}
        data-testid={`nav-cat-link-${slugTest}`}
        className="flex items-center gap-1 px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 group-hover:text-[#FFC107] transition-colors"
      >
        {cat.name}
        {kids.length > 0 && <ChevronDown size={14} className="opacity-70 group-hover:rotate-180 transition-transform" />}
      </Link>
      {kids.length > 0 && (
        <div className="absolute left-0 top-full pt-2 hidden group-hover:block z-50" data-testid={`nav-dropdown-${slugTest}`}>
          <div className="min-w-[220px] bg-[#1f1f1f] border border-[#2e2e2e] rounded-xl shadow-2xl py-2">
            <Link to={`/produtos?category=${cat.slug}`} className="block px-4 py-2 text-xs uppercase tracking-wider text-[#FFC107] font-bold hover:bg-white/5">
              Ver tudo de {cat.name}
            </Link>
            <div className="my-1 border-t border-[#2e2e2e]" />
            {kids.map((sub) => (
              <Link
                key={sub.id}
                to={`/produtos?category=${sub.slug}`}
                data-testid={`nav-sub-link-${sub.slug.replace(/[^a-z0-9]/g, "")}`}
                className="block px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
              >
                {sub.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Mobile: acordeão touch-friendly por categoria.
function MobileCategory({ cat, close }) {
  const [expanded, setExpanded] = useState(false);
  const kids = cat.children || [];
  const slugTest = cat.slug.replace(/[^a-z0-9]/g, "");
  return (
    <div className="border-b border-[#2e2e2e]/50 last:border-0">
      <div className="flex items-center">
        <Link
          to={`/produtos?category=${cat.slug}`}
          onClick={close}
          data-testid={`mnav-cat-link-${slugTest}`}
          className="flex-1 px-2 py-3 text-sm uppercase tracking-wide font-semibold text-white hover:text-[#FFC107]"
        >
          {cat.name}
        </Link>
        {kids.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            data-testid={`mnav-toggle-${slugTest}`}
            aria-label={`Expandir ${cat.name}`}
            className="p-3 text-gray-400"
          >
            {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </button>
        )}
      </div>
      {expanded && kids.length > 0 && (
        <div className="pb-2 pl-4">
          {kids.map((sub) => (
            <Link
              key={sub.id}
              to={`/produtos?category=${sub.slug}`}
              onClick={close}
              data-testid={`mnav-sub-link-${sub.slug.replace(/[^a-z0-9]/g, "")}`}
              className="block px-2 py-2 text-sm text-gray-400 hover:text-white"
            >
              {sub.name}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
