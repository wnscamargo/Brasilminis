import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, Heart, ShoppingCart, User, Menu, X } from "lucide-react";
import { LOGO_HEADER, MENU } from "@/lib/brand";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";

export default function Header() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const { count } = useCart();
  const { user } = useAuth();
  const { ids } = useFavorites();
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
          <div className="flex items-center gap-4 h-20">
            <button
              className="lg:hidden text-white"
              onClick={() => setOpen(!open)}
              data-testid="mobile-menu-toggle"
              aria-label="Menu"
            >
              {open ? <X size={26} /> : <Menu size={26} />}
            </button>

            <Link to="/" data-testid="logo-link" className="shrink-0">
              <img src={LOGO_HEADER} alt="Brasil Minis" className="h-11 w-auto object-contain" />
            </Link>

            <form onSubmit={submitSearch} className="hidden md:flex flex-1 max-w-xl mx-4 relative">
              <input
                data-testid="search-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Buscar miniaturas, marcas, acessórios..."
                className="w-full bg-[#1f1f1f] border border-[#2e2e2e] rounded-full py-2.5 pl-5 pr-12 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-[#1E3A8A] transition-colors"
              />
              <button
                type="submit"
                data-testid="search-submit"
                className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white hover:bg-[#152b66] transition-colors"
              >
                <Search size={16} />
              </button>
            </form>

            <div className="flex items-center gap-1 md:gap-2 ml-auto">
              <Link
                to={user ? "/conta" : "/login"}
                data-testid="account-link"
                className="flex items-center gap-2 px-3 py-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors"
              >
                <User size={22} />
                <span className="hidden xl:inline text-sm">
                  {user ? user.name.split(" ")[0] : "Entrar"}
                </span>
              </Link>
              <Link
                to="/favoritos"
                data-testid="favorites-link"
                className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors"
              >
                <Heart size={22} />
                {ids.length > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-[#009B3A] text-white text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">
                    {ids.length}
                  </span>
                )}
              </Link>
              <Link
                to="/carrinho"
                data-testid="cart-link"
                className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors"
              >
                <ShoppingCart size={22} />
                {count > 0 && (
                  <span
                    data-testid="cart-count"
                    className="absolute -top-0.5 -right-0.5 bg-[#FFC107] text-[#111111] text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center"
                  >
                    {count}
                  </span>
                )}
              </Link>
            </div>
          </div>

          {/* nav row */}
          <nav className="hidden lg:flex items-center gap-1 pb-3 -mt-1">
            {MENU.map((m) => (
              <Link
                key={m.label}
                to={m.to}
                data-testid={`nav-${m.label.toLowerCase().replace(/[^a-z]/g, "")}`}
                className="px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-[#FFC107] transition-colors"
              >
                {m.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* mobile menu */}
      {open && (
        <div className="lg:hidden bg-[#1f1f1f] border-b border-[#2e2e2e] px-4 py-4">
          <form onSubmit={submitSearch} className="relative mb-3">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar..."
              className="w-full bg-[#111111] border border-[#2e2e2e] rounded-full py-2.5 pl-4 pr-12 text-sm text-white"
            />
            <button type="submit" className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white">
              <Search size={16} />
            </button>
          </form>
          <div className="grid grid-cols-2 gap-1">
            {MENU.map((m) => (
              <Link
                key={m.label}
                to={m.to}
                onClick={() => setOpen(false)}
                className="px-3 py-2 text-sm uppercase tracking-wide text-gray-300 hover:text-[#FFC107]"
              >
                {m.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
