import { Link, useLocation, Outlet } from "react-router-dom";
import { LayoutDashboard, Package, Tags, Award, ShoppingBag, Users, Image, Home } from "lucide-react";
import { LOGO_EMBLEM } from "@/lib/brand";

const NAV = [
  { to: "/admin", l: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/produtos", l: "Produtos", icon: Package },
  { to: "/admin/categorias", l: "Categorias", icon: Tags },
  { to: "/admin/marcas", l: "Marcas", icon: Award },
  { to: "/admin/pedidos", l: "Pedidos", icon: ShoppingBag },
  { to: "/admin/clientes", l: "Clientes", icon: Users },
  { to: "/admin/banners", l: "Banners", icon: Image },
];

export default function AdminLayout() {
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-[#0d0d0d] flex">
      <aside className="w-64 shrink-0 border-r border-[#2e2e2e] bg-[#111111] hidden lg:flex flex-col sticky top-0 h-screen">
        <div className="p-5 flex items-center gap-3 border-b border-[#2e2e2e]">
          <img src={LOGO_EMBLEM} alt="" className="h-10 w-10 rounded-lg object-cover" />
          <div>
            <p className="font-display font-black text-white uppercase text-sm leading-none">Brasil Minis</p>
            <p className="text-xs text-[#FFC107]">Admin</p>
          </div>
        </div>
        <nav className="p-3 flex-1">
          {NAV.map((n) => {
            const active = n.end ? pathname === n.to : pathname.startsWith(n.to);
            return (
              <Link
                key={n.to}
                to={n.to}
                data-testid={`admin-nav-${n.l.toLowerCase()}`}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium mb-1 transition-colors ${
                  active ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <n.icon size={18} /> {n.l}
              </Link>
            );
          })}
        </nav>
        <Link to="/" className="m-3 flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5">
          <Home size={18} /> Voltar à loja
        </Link>
      </aside>

      <div className="flex-1 min-w-0">
        <div className="lg:hidden bm-glass sticky top-0 z-40 px-4 py-3 flex gap-2 overflow-x-auto">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className="whitespace-nowrap text-xs text-gray-300 px-3 py-1.5 rounded-full border border-[#2e2e2e]">{n.l}</Link>
          ))}
        </div>
        <div className="p-4 lg:p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
