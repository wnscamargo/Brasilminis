import { useCallback, useEffect, useRef, useState } from "react";
import { initMercadoPago, CardPayment } from "@mercadopago/sdk-react";
import { QrCode, Copy, Check, Loader2, ShieldCheck, Clock } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

let mpInitialized = false;

// Renderiza o pagamento REAL do Mercado Pago (PIX QR + copia-e-cola, ou Cartão via Brick).
export default function MercadoPagoPayment({ order, method, publicKey, payerEmail, onApproved }) {
  useEffect(() => {
    if (publicKey && !mpInitialized) {
      initMercadoPago(publicKey, { locale: "pt-BR" });
      mpInitialized = true;
    }
  }, [publicKey]);

  if (method === "pix") return <PixPayment order={order} onApproved={onApproved} />;
  return <CardBrickPayment order={order} payerEmail={payerEmail} onApproved={onApproved} />;
}

// ---------------- PIX ----------------
function PixPayment({ order, onApproved }) {
  const [pix, setPix] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState("pending");
  const pollRef = useRef(null);
  const created = useRef(false);

  const createPix = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await api.post("/payments/pix", { order_id: order.id });
      setPix(data);
      setStatus(data.status || "pending");
      if (data.status === "approved") onApproved(order);
    } catch (e) {
      setError(formatApiError(e.response?.data?.detail));
    } finally { setLoading(false); }
  }, [order, onApproved]);

  useEffect(() => {
    if (created.current) return;
    created.current = true;
    createPix();
  }, [createPix]);

  // Polling de status (fonte de verdade = backend, não o cliente).
  useEffect(() => {
    if (!pix || status === "approved") return;
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/payments/${order.id}/status`);
        if (data.status && data.status !== status) setStatus(data.status);
        if (data.status === "approved") {
          clearInterval(pollRef.current);
          onApproved(order);
        }
      } catch (_) { /* silencioso */ }
    }, 5000);
    return () => clearInterval(pollRef.current);
  }, [pix, status, order, onApproved]);

  const copyCode = () => {
    if (!pix?.copy_paste) return;
    navigator.clipboard.writeText(pix.copy_paste);
    setCopied(true);
    toast.success("Código PIX copiado");
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) return <Centered><Loader2 className="animate-spin text-[#FFC107]" size={36} /><p className="text-gray-400 mt-3">Gerando PIX...</p></Centered>;
  if (error) return (
    <Centered>
      <p className="text-red-400 text-sm">{error}</p>
      <button onClick={createPix} data-testid="pix-retry-btn" className="mt-4 bg-[#1E3A8A] text-white rounded-full px-5 py-2 text-sm font-semibold">Tentar novamente</button>
    </Centered>
  );

  const qrSrc = pix?.qr_code_base64
    ? (pix.qr_code_base64.startsWith("data:") ? pix.qr_code_base64 : `data:image/png;base64,${pix.qr_code_base64}`)
    : null;

  return (
    <div data-testid="pix-payment" className="text-center">
      <div className="inline-flex items-center gap-2 text-[#FFC107] text-sm font-semibold mb-4"><QrCode size={18} /> Pague com PIX</div>
      {qrSrc && <img src={qrSrc} alt="QR Code PIX" data-testid="pix-qr-image" className="mx-auto h-56 w-56 rounded-xl bg-white p-2" />}
      <p className="text-gray-400 text-sm mt-4">Escaneie o QR Code no app do seu banco ou use o copia-e-cola:</p>
      <div className="mt-3 flex items-stretch gap-2 max-w-md mx-auto">
        <textarea readOnly value={pix?.copy_paste || ""} data-testid="pix-copy-paste" rows={3}
          className="flex-1 bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-xs text-gray-300 resize-none" />
        <button onClick={copyCode} data-testid="pix-copy-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-lg px-4 flex items-center gap-1 shrink-0">
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </button>
      </div>
      <div className="mt-6 inline-flex items-center gap-2 text-xs text-gray-400 bg-[#111] border border-[#2e2e2e] rounded-full px-4 py-2" data-testid="pix-status">
        {status === "approved"
          ? <><Check size={14} className="text-[#009B3A]" /> Pagamento aprovado!</>
          : <><Clock size={14} className="text-[#FFC107] animate-pulse" /> Aguardando pagamento... (atualiza automaticamente)</>}
      </div>
      <p className="text-gray-600 text-xs mt-3">Valor: {formatBRL(order.total)} · expira em 30 minutos</p>
    </div>
  );
}

// ---------------- Cartão (Brick) ----------------
function CardBrickPayment({ order, payerEmail, onApproved }) {
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const onSubmit = async (formData) => {
    setProcessing(true);
    try {
      const { data } = await api.post("/payments/card", {
        order_id: order.id,
        token: formData.token,
        payment_method_id: formData.payment_method_id,
        installments: Number(formData.installments) || 1,
        issuer_id: formData.issuer_id ? Number(formData.issuer_id) : null,
        payer_email: formData.payer?.email || payerEmail,
      });
      setResult(data);
      if (data.status === "approved") {
        toast.success("Pagamento aprovado!");
        onApproved(order);
      } else if (data.status === "rejected") {
        toast.error("Pagamento recusado. Tente outro cartão.");
      } else {
        toast.info("Pagamento em processamento.");
      }
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
      throw e;
    } finally { setProcessing(false); }
  };

  return (
    <div data-testid="card-payment">
      <div className="inline-flex items-center gap-2 text-[#FFC107] text-sm font-semibold mb-4"><ShieldCheck size={18} /> Pagamento seguro com cartão</div>
      {processing && <p className="text-gray-400 text-sm mb-3 flex items-center gap-2"><Loader2 className="animate-spin" size={16} /> Processando pagamento...</p>}
      {result && result.status && (
        <div data-testid="card-status" className={`mb-4 text-sm rounded-lg p-3 border ${result.status === "approved" ? "text-[#009B3A] border-[#009B3A]/40 bg-[#009B3A]/10" : "text-[#FFC107] border-[#FFC107]/40 bg-[#FFC107]/10"}`}>
          Status: {result.status}{result.status_detail ? ` (${result.status_detail})` : ""}
        </div>
      )}
      <div className="bg-white rounded-xl p-3">
        <CardPayment
          initialization={{ amount: Number(order.total), payer: { email: payerEmail } }}
          customization={{ visual: { style: { theme: "default" } }, paymentMethods: { maxInstallments: 12 } }}
          onSubmit={onSubmit}
          onError={() => toast.error("Verifique os dados do cartão.")}
        />
      </div>
    </div>
  );
}

function Centered({ children }) {
  return <div className="flex flex-col items-center justify-center py-10 text-center">{children}</div>;
}
