import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, QrCode, CreditCard, Barcode, Tag, Lock } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";

export default function Checkout() {
  const { items, subtotal, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [address, setAddress] = useState({
    label: "Casa", recipient: user?.name || "", street: "", number: "",
    complement: "", district: "", city: "", state: "", zip: "",
  });
  const [payment, setPayment] = useState("pix");
  const [couponCode, setCouponCode] = useState("");
  const [coupon, setCoupon] = useState(null);
  const [discount, setDiscount] = useState(0);
  const [placing, setPlacing] = useState(false);
  const [done, setDone] = useState(null);

  if (!user) {
    return (
      <div className="max-w-[600px] mx-auto px-4 py-24 text-center">
        <Lock className="mx-auto text-[#FFC107]" size={44} />
        <h1 className="text-2xl font-display font-bold text-white mt-6">Entre para finalizar</h1>
        <p className="text-gray-500 mt-2">Você precisa estar logado para concluir a compra.</p>
        <Link to="/login" state={{ from: "/checkout" }} className="inline-block mt-6 bg-[#FFC107] text-[#111111] font-bold uppercase rounded-full px-8 py-3.5">Fazer login</Link>
      </div>
    );
  }

  if (items.length === 0 && !done) {
    return (
      <div className="max-w-[600px] mx-auto px-4 py-24 text-center text-gray-400">
        Carrinho vazio. <Link to="/produtos" className="text-[#FFC107]">Ver produtos</Link>
      </div>
    );
  }

  const shipping = subtotal - discount >= 300 || subtotal === 0 ? 0 : 29.9;
  const total = subtotal - discount + shipping;

  const applyCoupon = async () => {
    if (!couponCode) return;
    try {
      const { data } = await api.post("/coupons/validate", { code: couponCode });
      setCoupon(data);
      const disc = data.type === "percent" ? subtotal * data.value / 100 : data.value;
      setDiscount(Math.min(disc, subtotal));
      toast.success(`Cupom ${data.code} aplicado!`);
    } catch (e) {
      setCoupon(null); setDiscount(0);
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const placeOrder = async () => {
    if (!address.street || !address.city || !address.zip) {
      return toast.error("Preencha o endereço de entrega");
    }
    setPlacing(true);
    try {
      const { data } = await api.post("/orders", {
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        payment_method: payment,
        shipping_method: "standard",
        coupon: coupon?.code || null,
        address,
      });
      clearCart();
      setDone(data);
      window.scrollTo(0, 0);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setPlacing(false);
    }
  };

  if (done) {
    return (
      <div className="max-w-[700px] mx-auto px-4 py-20 text-center">
        <CheckCircle2 className="mx-auto text-[#009B3A]" size={72} />
        <h1 className="text-3xl font-display font-black uppercase text-white mt-6">Pedido confirmado!</h1>
        <p className="text-gray-400 mt-3">
          Pedido <span className="text-[#FFC107] font-bold">#{done.order_number}</span> recebido com sucesso.
        </p>
        <div className="bm-card p-6 mt-8 text-left">
          <div className="bg-[#FFC107]/10 border border-[#FFC107]/30 rounded-lg p-3 mb-4 text-xs text-[#FFC107]">
            Pagamento SIMULADO (aprovado). Integração Mercado Pago será ativada em produção.
          </div>
          {done.payment?.pix_qr && (
            <div className="flex items-center gap-3 mb-4">
              <QrCode size={40} className="text-white" />
              <div>
                <p className="text-white text-sm font-semibold">PIX gerado</p>
                <p className="text-gray-500 text-xs break-all">{done.payment.pix_qr}</p>
              </div>
            </div>
          )}
          <div className="flex justify-between text-sm text-gray-400"><span>Total pago</span><span className="text-white font-bold">{formatBRL(done.total)}</span></div>
        </div>
        <div className="flex gap-3 justify-center mt-8">
          <Link to="/conta" className="bg-[#1E3A8A] text-white font-semibold rounded-full px-6 py-3">Ver meus pedidos</Link>
          <Link to="/produtos" className="border border-white/30 text-white font-semibold rounded-full px-6 py-3">Continuar comprando</Link>
        </div>
      </div>
    );
  }

  const payments = [
    { v: "pix", l: "PIX", icon: QrCode, note: "Aprovação imediata" },
    { v: "card", l: "Cartão de Crédito", icon: CreditCard, note: "Em até 12x" },
    { v: "boleto", l: "Boleto", icon: Barcode, note: "Vence em 3 dias" },
  ];

  return (
    <div className="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
      <h1 className="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Checkout</h1>
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* address */}
          <div className="bm-card p-6">
            <h3 className="font-display font-bold text-white uppercase mb-4">Endereço de entrega</h3>
            <div className="grid grid-cols-2 gap-3">
              <Input label="Destinatário" value={address.recipient} onChange={(v) => setAddress({ ...address, recipient: v })} full testid="addr-recipient" />
              <Input label="CEP" value={address.zip} onChange={(v) => setAddress({ ...address, zip: v })} testid="addr-zip" />
              <Input label="Estado" value={address.state} onChange={(v) => setAddress({ ...address, state: v })} testid="addr-state" />
              <Input label="Rua" value={address.street} onChange={(v) => setAddress({ ...address, street: v })} testid="addr-street" />
              <Input label="Número" value={address.number} onChange={(v) => setAddress({ ...address, number: v })} testid="addr-number" />
              <Input label="Bairro" value={address.district} onChange={(v) => setAddress({ ...address, district: v })} testid="addr-district" />
              <Input label="Cidade" value={address.city} onChange={(v) => setAddress({ ...address, city: v })} testid="addr-city" />
              <Input label="Complemento" value={address.complement} onChange={(v) => setAddress({ ...address, complement: v })} full testid="addr-complement" />
            </div>
          </div>

          {/* payment */}
          <div className="bm-card p-6">
            <h3 className="font-display font-bold text-white uppercase mb-4">Pagamento</h3>
            <div className="grid sm:grid-cols-3 gap-3">
              {payments.map((p) => (
                <button
                  key={p.v}
                  onClick={() => setPayment(p.v)}
                  data-testid={`pay-${p.v}`}
                  className={`p-4 rounded-xl border text-left transition-colors ${
                    payment === p.v ? "border-[#FFC107] bg-[#FFC107]/5" : "border-[#2e2e2e] hover:border-white/30"
                  }`}
                >
                  <p.icon className={payment === p.v ? "text-[#FFC107]" : "text-gray-400"} size={22} />
                  <p className="text-white text-sm font-semibold mt-2">{p.l}</p>
                  <p className="text-gray-500 text-xs">{p.note}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* summary */}
        <div className="bm-card p-6 h-fit sticky top-28">
          <h3 className="font-display font-bold text-white uppercase mb-4">Resumo</h3>
          <div className="max-h-48 overflow-y-auto space-y-3 mb-4">
            {items.map((i) => (
              <div key={i.product_id} className="flex gap-3 items-center">
                <img src={i.image} alt="" className="h-12 w-12 rounded-lg object-cover" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white line-clamp-1">{i.name}</p>
                  <p className="text-xs text-gray-500">{i.quantity}x {formatBRL(i.price)}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 mb-4">
            <input
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
              placeholder="Cupom"
              data-testid="coupon-input"
              className="flex-1 bg-[#111111] border border-[#2e2e2e] rounded-full px-4 py-2 text-sm text-white focus:outline-none focus:border-[#FFC107]"
            />
            <button onClick={applyCoupon} data-testid="apply-coupon" className="bg-[#1E3A8A] text-white rounded-full px-4 py-2 text-sm font-semibold flex items-center gap-1">
              <Tag size={14} /> Aplicar
            </button>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-400"><span>Subtotal</span><span className="text-white">{formatBRL(subtotal)}</span></div>
            {discount > 0 && <div className="flex justify-between text-[#009B3A]"><span>Desconto</span><span>-{formatBRL(discount)}</span></div>}
            <div className="flex justify-between text-gray-400"><span>Frete</span><span className="text-white">{shipping === 0 ? "Grátis" : formatBRL(shipping)}</span></div>
          </div>
          <div className="border-t border-[#2e2e2e] mt-4 pt-4 flex justify-between items-baseline">
            <span className="text-white font-semibold">Total</span>
            <span className="text-2xl font-display font-black text-white" data-testid="checkout-total">{formatBRL(total)}</span>
          </div>

          <button
            onClick={placeOrder}
            disabled={placing}
            data-testid="place-order-btn"
            className="w-full mt-6 bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-4 hover:bg-[#e0a800] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Lock size={16} /> {placing ? "Processando..." : "Pagar agora"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, full, testid }) {
  return (
    <div className={full ? "col-span-2" : ""}>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testid}
        className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]"
      />
    </div>
  );
}
