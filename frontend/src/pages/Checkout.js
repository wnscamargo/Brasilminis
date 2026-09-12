import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, QrCode, CreditCard, Barcode, Tag, Lock } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useCepAutofill, maskCep } from "@/lib/cep";
import { maskCpf } from "@/lib/cpf";
import MercadoPagoPayment from "@/components/checkout/MercadoPagoPayment";

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
  const [couponFreeShip, setCouponFreeShip] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [done, setDone] = useState(null);
  // Endereço cadastrado / alternativo
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [useOther, setUseOther] = useState(false);
  const [saveToAccount, setSaveToAccount] = useState(false);
  // Mercado Pago (pagamento real)
  const [mp, setMp] = useState({ loaded: false, enabled: false, publicKey: null });
  const [payStep, setPayStep] = useState(null); // pedido aguardando pagamento real
  // Melhor Envio
  const [recipientDoc, setRecipientDoc] = useState(user?.cpf ? maskCpf(user.cpf) : "");
  const [recipientPhone, setRecipientPhone] = useState(user?.phone || "");
  const [shipOptions, setShipOptions] = useState(null);
  const [quoteId, setQuoteId] = useState(null);
  const [selectedShip, setSelectedShip] = useState(null);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    api.get("/mercado-pago/public-key")
      .then(({ data }) => setMp({ loaded: true, enabled: !!data.enabled, publicKey: data.public_key }))
      .catch(() => setMp({ loaded: true, enabled: false, publicKey: null }));
  }, []);

  // Usa o CPF já cadastrado do cliente (evita pedir de novo); a edição de endereço NÃO altera o CPF do cadastro.
  useEffect(() => {
    if (user?.cpf) setRecipientDoc(maskCpf(user.cpf));
    if (user?.phone) setRecipientPhone(user.phone);
  }, [user]);

  // Carrega o endereço já cadastrado do cliente (default > mais recente).
  useEffect(() => {
    api.get("/account/addresses").then(({ data }) => {
      const list = data || [];
      setSavedAddresses(list);
      if (list.length > 0) {
        const chosen = list.find((a) => a.is_default) || list[list.length - 1];
        setAddress({
          label: chosen.label || "Casa", recipient: chosen.recipient || user?.name || "",
          street: chosen.street || "", number: chosen.number || "", complement: chosen.complement || "",
          district: chosen.district || "", city: chosen.city || "", state: chosen.state || "", zip: chosen.zip || "",
        });
        setUseOther(false);
      } else {
        setUseOther(true);
      }
    }).catch(() => setUseOther(true));
  }, [user]);

  useEffect(() => {
    if (mp.enabled && payment === "boleto") setPayment("pix");
  }, [mp.enabled, payment]);

  const fillFromCep = useCepAutofill((d) => setAddress((a) => ({
    ...a,
    street: d.street || a.street,
    district: d.district || a.district,
    city: d.city || a.city,
    state: d.uf || a.state,
  })));

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

  const freeShipping = couponFreeShip || subtotal - discount >= 300 || subtotal === 0;
  const shipping = selectedShip ? (freeShipping ? 0 : selectedShip.price) : (freeShipping ? 0 : 29.9);
  const total = subtotal - discount + shipping;

  const calcShipping = async () => {
    if (!address.zip) return toast.error("Informe o CEP para calcular o frete");
    setCalculating(true);
    setShipOptions(null); setSelectedShip(null); setQuoteId(null);
    try {
      const { data } = await api.post("/shipping/quote", {
        postal_code: address.zip,
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
      });
      setShipOptions(data.options);
      setQuoteId(data.quote_id);
      if (data.options[0]) setSelectedShip(data.options[0]);
      toast.success("Frete calculado");
    } catch (e) {
      const status = e.response?.status;
      if (status === 503) toast.error("Frete temporariamente indisponível. Tente novamente.");
      else toast.error(formatApiError(e.response?.data?.detail));
    } finally { setCalculating(false); }
  };

  const applyCoupon = async () => {
    if (!couponCode) return;
    try {
      const { data } = await api.post("/coupons/preview", {
        code: couponCode,
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
      });
      setCoupon(data);
      setDiscount(data.discount || 0);
      setCouponFreeShip(!!data.free_shipping);
      toast.success(`Cupom ${data.code} aplicado!`);
    } catch (e) {
      setCoupon(null); setDiscount(0); setCouponFreeShip(false);
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const removeCoupon = () => {
    setCoupon(null); setDiscount(0); setCouponFreeShip(false); setCouponCode("");
    toast.message("Cupom removido");
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
        quote_id: quoteId,
        shipping_service_id: selectedShip?.service_id || null,
        recipient_document: recipientDoc || null,
        recipient_phone: recipientPhone || null,
      });
      clearCart();
      if (useOther && saveToAccount) {
        try {
          await api.post("/account/addresses", { ...address, is_default: savedAddresses.length === 0 });
        } catch { /* não bloqueia o pedido */ }
      }
      if (data.payment?.requires_payment) {
        setPayStep(data);
      } else {
        setDone(data);
      }
      window.scrollTo(0, 0);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setPlacing(false);
    }
  };

  const onPaymentApproved = (order) => {
    setPayStep(null);
    setDone({ ...order, _real_payment: true });
    window.scrollTo(0, 0);
  };

  if (payStep) {
    return (
      <div className="max-w-[700px] mx-auto px-4 py-12">
        <h1 className="text-2xl lg:text-3xl font-display font-black uppercase text-white mb-2">Finalize o pagamento</h1>
        <p className="text-gray-400 text-sm mb-6">Pedido <span className="text-[#FFC107] font-bold">#{payStep.order_number}</span> · {formatBRL(payStep.total)}</p>
        <div className="bm-card p-6" data-testid="payment-step">
          <MercadoPagoPayment
            order={payStep}
            method={payStep.payment_method || payment}
            publicKey={mp.publicKey}
            payerEmail={user?.email}
            onApproved={onPaymentApproved}
          />
        </div>
        <button onClick={() => { setPayStep(null); navigate("/conta"); }} data-testid="pay-later-btn" className="mt-4 text-sm text-gray-400 hover:text-white underline">
          Pagar depois (ver em meus pedidos)
        </button>
      </div>
    );
  }

  if (done) {
    return (
      <div className="max-w-[700px] mx-auto px-4 py-20 text-center">
        <CheckCircle2 className="mx-auto text-[#009B3A]" size={72} />
        <h1 className="text-3xl font-display font-black uppercase text-white mt-6">Pedido confirmado!</h1>
        <p className="text-gray-400 mt-3">
          Pedido <span className="text-[#FFC107] font-bold">#{done.order_number}</span> recebido com sucesso.
        </p>
        <div className="bm-card p-6 mt-8 text-left">
          {done._real_payment ? (
            <div className="bg-[#009B3A]/10 border border-[#009B3A]/30 rounded-lg p-3 mb-4 text-xs text-[#009B3A] flex items-center gap-2">
              <CheckCircle2 size={16} /> Pagamento confirmado via Mercado Pago.
            </div>
          ) : (
            <div className="bg-[#FFC107]/10 border border-[#FFC107]/30 rounded-lg p-3 mb-4 text-xs text-[#FFC107]">
              Pagamento SIMULADO (aprovado). Configure o Mercado Pago no painel para cobrar de verdade.
            </div>
          )}
          {done.payment?.pix_qr && !done._real_payment && (
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

  const payments = mp.enabled
    ? [
        { v: "pix", l: "PIX", icon: QrCode, note: "Aprovação imediata" },
        { v: "card", l: "Cartão de Crédito", icon: CreditCard, note: "Em até 12x" },
      ]
    : [
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

            {savedAddresses.length > 0 && !useOther && (
              <div data-testid="saved-address" className="border border-[#2e2e2e] rounded-xl p-4 mb-4">
                <p className="text-white text-sm font-semibold">{address.recipient}</p>
                <p className="text-gray-400 text-sm">{address.street}, {address.number}{address.complement ? ` - ${address.complement}` : ""}</p>
                <p className="text-gray-400 text-sm">{address.district} · {address.city}/{address.state} · CEP {address.zip}</p>
              </div>
            )}

            {savedAddresses.length > 0 && (
              <label className="flex items-center gap-2 text-sm text-gray-300 mb-4 cursor-pointer">
                <input type="checkbox" checked={useOther} onChange={(e) => setUseOther(e.target.checked)} data-testid="use-other-address" className="accent-[#FFC107] h-4 w-4" />
                Entregar em outro endereço
              </label>
            )}

            {useOther && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <Input label="Destinatário" value={address.recipient} onChange={(v) => setAddress({ ...address, recipient: v })} full testid="addr-recipient" />
                  <Input label="CEP" value={address.zip} onChange={(v) => { const mv = maskCep(v); setAddress((a) => ({ ...a, zip: mv })); fillFromCep(mv); }} testid="addr-zip" />
                  <Input label="Estado" value={address.state} onChange={(v) => setAddress({ ...address, state: v })} testid="addr-state" />
                  <Input label="Rua" value={address.street} onChange={(v) => setAddress({ ...address, street: v })} testid="addr-street" />
                  <Input label="Número" value={address.number} onChange={(v) => setAddress({ ...address, number: v })} testid="addr-number" />
                  <Input label="Bairro" value={address.district} onChange={(v) => setAddress({ ...address, district: v })} testid="addr-district" />
                  <Input label="Cidade" value={address.city} onChange={(v) => setAddress({ ...address, city: v })} testid="addr-city" />
                  <Input label="Complemento" value={address.complement} onChange={(v) => setAddress({ ...address, complement: v })} full testid="addr-complement" />
                </div>
                <label className="flex items-center gap-2 text-sm text-gray-300 mt-3 cursor-pointer">
                  <input type="checkbox" checked={saveToAccount} onChange={(e) => setSaveToAccount(e.target.checked)} data-testid="save-address-toggle" className="accent-[#FFC107] h-4 w-4" />
                  Salvar este endereço na minha conta
                </label>
              </>
            )}

            <div className="grid grid-cols-2 gap-3 mt-3">
              <Input label="CPF/CNPJ do destinatário" value={recipientDoc} onChange={setRecipientDoc} testid="addr-document" />
              <Input label="Telefone" value={recipientPhone} onChange={setRecipientPhone} testid="addr-phone" />
            </div>
          </div>

          {/* frete (Melhor Envio) */}
          <div className="bm-card p-6" data-testid="shipping-card">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h3 className="font-display font-bold text-white uppercase">Frete</h3>
              <button onClick={calcShipping} disabled={calculating} data-testid="calc-shipping-btn" className="bg-[#1E3A8A] text-white rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-50">{calculating ? "Calculando..." : "Calcular frete"}</button>
            </div>
            {!shipOptions && <p className="text-sm text-gray-500">Informe o CEP acima e clique em “Calcular frete” para ver as opções.</p>}
            {shipOptions && shipOptions.length === 0 && <p className="text-sm text-gray-500">Nenhuma opção de frete disponível para este CEP.</p>}
            <div className="space-y-2">
              {(shipOptions || []).map((o) => (
                <button key={o.service_id} onClick={() => setSelectedShip(o)} data-testid={`ship-option-${o.service_id}`}
                  className={`w-full flex items-center justify-between gap-3 p-3 rounded-xl border text-left transition-colors ${selectedShip?.service_id === o.service_id ? "border-[#FFC107] bg-[#FFC107]/5" : "border-[#2e2e2e] hover:border-white/30"}`}>
                  <div className="flex items-center gap-3 min-w-0">
                    {o.company_picture && <img src={o.company_picture} alt="" className="h-6 w-6 object-contain" />}
                    <div className="min-w-0">
                      <p className="text-white text-sm font-semibold truncate">{o.company_name} {o.name}</p>
                      <p className="text-gray-500 text-xs">{o.delivery_time ? `${o.delivery_time} dia(s) úteis` : "prazo indisponível"}</p>
                    </div>
                  </div>
                  <span className="text-[#FFC107] font-bold whitespace-nowrap">{freeShipping ? "Grátis" : formatBRL(o.price)}</span>
                </button>
              ))}
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

          <div className="flex gap-2 mb-2">
            <input
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
              placeholder="Cupom de desconto"
              disabled={!!coupon}
              data-testid="coupon-input"
              className="flex-1 bg-[#111111] border border-[#2e2e2e] rounded-full px-4 py-2 text-sm text-white focus:outline-none focus:border-[#FFC107] disabled:opacity-60"
            />
            {coupon ? (
              <button onClick={removeCoupon} data-testid="remove-coupon" className="bg-red-500/20 text-red-400 rounded-full px-4 py-2 text-sm font-semibold">Remover</button>
            ) : (
              <button onClick={applyCoupon} data-testid="apply-coupon" className="bg-[#1E3A8A] text-white rounded-full px-4 py-2 text-sm font-semibold flex items-center gap-1">
                <Tag size={14} /> Aplicar
              </button>
            )}
          </div>
          {coupon && <p className="text-xs text-[#009B3A] mb-4" data-testid="coupon-applied">Cupom {coupon.code} aplicado{couponFreeShip ? " · frete grátis" : ""}.</p>}

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
