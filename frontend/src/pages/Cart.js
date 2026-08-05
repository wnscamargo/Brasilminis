import { Link, useNavigate } from "react-router-dom";
import { Trash2, Minus, Plus, ShoppingBag, ArrowRight } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { formatBRL } from "@/lib/brand";

const FREE_SHIPPING = 300;

export default function Cart() {
  const { items, updateQty, removeItem, subtotal } = useCart();
  const navigate = useNavigate();
  const missing = Math.max(0, FREE_SHIPPING - subtotal);
  const shipping = subtotal >= FREE_SHIPPING || subtotal === 0 ? 0 : 29.9;

  if (items.length === 0)
    return (
      <div className="max-w-[900px] mx-auto px-4 py-24 text-center">
        <ShoppingBag size={56} className="mx-auto text-[#2e2e2e]" />
        <h1 className="text-2xl font-display font-bold text-white mt-6">Seu carrinho está vazio</h1>
        <p className="text-gray-500 mt-2">Explore nossa coleção e encontre sua próxima miniatura.</p>
        <Link to="/produtos" className="inline-flex items-center gap-2 mt-8 bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-8 py-3.5 hover:bg-[#e0a800] transition-colors">
          Ver produtos <ArrowRight size={18} />
        </Link>
      </div>
    );

  return (
    <div className="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
      <h1 className="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Carrinho</h1>
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {items.map((i) => (
            <div key={i.product_id} className="bm-card p-4 flex gap-4" data-testid={`cart-item-${i.product_id}`}>
              <Link to={`/produto/${i.slug}`} className="h-24 w-24 rounded-lg overflow-hidden bg-[#171717] shrink-0">
                <img src={i.image} alt={i.name} className="h-full w-full object-cover" />
              </Link>
              <div className="flex-1 min-w-0">
                <Link to={`/produto/${i.slug}`} className="text-white font-medium hover:text-[#FFC107] transition-colors line-clamp-2">
                  {i.name}
                </Link>
                <p className="text-[#FFC107] font-display font-bold mt-1">{formatBRL(i.price)}</p>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center bm-card">
                    <button onClick={() => updateQty(i.product_id, i.quantity - 1)} className="p-2 text-white hover:text-[#FFC107]"><Minus size={14} /></button>
                    <span className="w-8 text-center text-white text-sm">{i.quantity}</span>
                    <button onClick={() => updateQty(i.product_id, i.quantity + 1)} className="p-2 text-white hover:text-[#FFC107]"><Plus size={14} /></button>
                  </div>
                  <button onClick={() => removeItem(i.product_id)} data-testid={`remove-${i.product_id}`} className="text-gray-500 hover:text-red-400 transition-colors flex items-center gap-1 text-sm">
                    <Trash2 size={16} /> Remover
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bm-card p-6 h-fit sticky top-28">
          <h3 className="font-display font-bold text-white uppercase mb-4">Resumo</h3>
          {missing > 0 ? (
            <p className="text-xs text-gray-400 mb-4 bg-[#111111] rounded-lg p-3 border border-[#2e2e2e]">
              Faltam <span className="text-[#009B3A] font-bold">{formatBRL(missing)}</span> para o frete grátis!
            </p>
          ) : (
            <p className="text-xs text-[#009B3A] mb-4 bg-[#009B3A]/10 rounded-lg p-3 border border-[#009B3A]/30 font-semibold">
              Você ganhou frete grátis! 🎉
            </p>
          )}
          <div className="space-y-2 text-sm">
            <Row label="Subtotal" value={formatBRL(subtotal)} />
            <Row label="Frete" value={shipping === 0 ? "Grátis" : formatBRL(shipping)} />
          </div>
          <div className="border-t border-[#2e2e2e] mt-4 pt-4 flex justify-between items-baseline">
            <span className="text-white font-semibold">Total</span>
            <span className="text-2xl font-display font-black text-white" data-testid="cart-total">{formatBRL(subtotal + shipping)}</span>
          </div>
          <button
            onClick={() => navigate("/checkout")}
            data-testid="checkout-btn"
            className="w-full mt-6 bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-4 hover:bg-[#e0a800] transition-colors flex items-center justify-center gap-2"
          >
            Finalizar compra <ArrowRight size={18} />
          </button>
          <Link to="/produtos" className="block text-center text-sm text-gray-400 hover:text-white mt-4 transition-colors">
            Continuar comprando
          </Link>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-gray-400">
      <span>{label}</span>
      <span className="text-white">{value}</span>
    </div>
  );
}
