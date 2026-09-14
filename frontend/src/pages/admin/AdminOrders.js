import { useEffect, useState, Fragment } from "react";
import { toast } from "sonner";
import { Truck, ChevronDown, ChevronUp, Printer, MapPin, RefreshCw, Trash2, AlertTriangle, X, ExternalLink, Copy, PackagePlus } from "lucide-react";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const STATUSES = ["confirmado", "em_separacao", "enviado", "entregue", "cancelado"];
const SCOPES = [["active", "Ativos"], ["deleted", "Excluídos"], ["all", "Todos"]];

const ACTION_LABELS = {
  prepare: "Preparar envio",
  cart: "Inserir no carrinho",
  checkout: "Comprar etiqueta",
  generate: "Gerar etiqueta",
  print: "Imprimir etiqueta",
  tracking: "Rastrear",
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [scope, setScope] = useState("active");
  const [deleting, setDeleting] = useState(null);
  const load = () => api.get(`/admin/orders?scope=${scope}`).then((r) => setOrders(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [scope]);

  const changeStatus = async (id, status) => {
    await api.put(`/admin/orders/${id}/status`, { status });
    toast.success("Status atualizado");
    load();
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Pedidos</h1>
        <div className="inline-flex bg-[#1f1f1f] border border-[#2e2e2e] rounded-full p-1" data-testid="orders-scope">
          {SCOPES.map(([v, l]) => (
            <button key={v} onClick={() => setScope(v)} data-testid={`orders-scope-${v}`}
              className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide ${scope === v ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white"}`}>{l}</button>
          ))}
        </div>
      </div>
      {orders.length === 0 ? (
        <div className="bm-card p-12 text-center text-gray-400">Nenhum pedido nesta visão.</div>
      ) : (
        <div className="bm-card overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111111] text-gray-500 uppercase text-xs">
              <tr>
                <th className="text-left p-4">Pedido</th>
                <th className="text-left p-4">Cliente</th>
                <th className="text-left p-4">Data</th>
                <th className="text-left p-4">Total</th>
                <th className="text-left p-4">Status</th>
                <th className="text-left p-4">Logística</th>
                <th className="text-left p-4">Ações</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <Fragment key={o.id}>
                  <tr className={`border-t border-[#2e2e2e] ${o.deleted_at ? "opacity-50" : ""}`} data-testid={`admin-order-${o.order_number}`}>
                    <td className="p-4 text-white font-semibold">#{o.order_number}
                      {o.deleted_at && <span className="ml-2 text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full uppercase" data-testid={`order-deleted-badge-${o.order_number}`}>Excluído</span>}
                    </td>
                    <td className="p-4 text-gray-300">{o.user_name}<br /><span className="text-gray-600 text-xs">{o.user_email}</span></td>
                    <td className="p-4 text-gray-400">{new Date(o.created_at).toLocaleDateString("pt-BR")}</td>
                    <td className="p-4 text-white">{formatBRL(o.total)}</td>
                    <td className="p-4">
                      <select value={o.status} disabled={!!o.deleted_at} onChange={(e) => changeStatus(o.id, e.target.value)} data-testid={`order-status-${o.order_number}`} className="bg-[#111111] border border-[#2e2e2e] rounded-lg px-2 py-1.5 text-xs text-white disabled:opacity-50">
                        {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="p-4">
                      <button onClick={() => setExpanded(expanded === o.id ? null : o.id)} data-testid={`toggle-shipment-${o.order_number}`} className="flex items-center gap-1.5 text-xs text-[#FFC107] font-semibold">
                        <Truck size={14} /> {o.shipping_provider === "melhor_envio" ? "Melhor Envio" : "Ver"}
                        {expanded === o.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </td>
                    <td className="p-4">
                      {!o.deleted_at && (
                        <button onClick={() => setDeleting(o)} data-testid={`delete-order-${o.order_number}`} className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 font-semibold">
                          <Trash2 size={14} /> Excluir
                        </button>
                      )}
                    </td>
                  </tr>
                  {expanded === o.id && (
                    <tr className="bg-[#0d0d0d]">
                      <td colSpan={7} className="p-4 space-y-4">
                        <SuperFretePanel order={o} />
                        <ShipmentPanel order={o} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {deleting && <DeleteOrderModal order={deleting} onClose={() => setDeleting(null)} onDeleted={() => { setDeleting(null); load(); }} />}
    </div>
  );
}

function DeleteOrderModal({ order, onClose, onDeleted }) {
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const canDelete = reason.trim().length > 0 && confirm === "EXCLUIR";

  const doDelete = async () => {
    if (!canDelete) return;
    setBusy(true);
    try {
      await api.delete(`/admin/orders/${order.id}`, { data: { reason: reason.trim(), confirm } });
      toast.success("Pedido excluído");
      onDeleted();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="delete-order-modal">
      <div className="bm-card p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white flex items-center gap-2"><AlertTriangle className="text-red-400" size={20} /> Excluir pedido</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <div className="text-sm text-gray-300 space-y-1 bg-[#111] border border-[#2e2e2e] rounded-lg p-3 mb-4">
          <div className="flex justify-between"><span className="text-gray-500">Pedido</span><span className="text-white font-semibold">#{order.order_number}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Cliente</span><span>{order.user_name}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Valor</span><span>{formatBRL(order.total)}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Status</span><span>{order.status}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Pagamento</span><span>{order.payment_status}{order.payment_provider ? ` (${order.payment_provider})` : ""}</span></div>
        </div>
        <label className="text-xs text-gray-500 block mb-1">Motivo da exclusão</label>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="delete-reason" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-3" />
        <label className="text-xs text-gray-500 block mb-1">Para confirmar a exclusão, digite <b className="text-red-400">EXCLUIR</b></label>
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="delete-confirm-input" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white mb-4" />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-300 hover:text-white">Cancelar</button>
          <button onClick={doDelete} disabled={!canDelete || busy} data-testid="delete-confirm-btn" className="bg-red-500 text-white font-bold rounded-full px-5 py-2 text-sm disabled:opacity-40">
            {busy ? "Excluindo..." : "EXCLUIR DEFINITIVAMENTE"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ShipmentPanel({ order }) {
  const [sh, setSh] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get(`/admin/orders/${order.id}/shipment`).then((r) => setSh(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [order.id]);

  const act = async (action) => {
    setBusy(true);
    try {
      if (action === "print") {
        const { data } = await api.get(`/admin/orders/${order.id}/shipment/print`);
        if (data.url) window.open(data.url, "_blank");
        else toast.error("Etiqueta ainda não disponível");
      } else if (action === "tracking") {
        const { data } = await api.post(`/admin/orders/${order.id}/shipment/tracking`);
        setSh(data);
        toast.success("Rastreamento atualizado");
      } else {
        const { data } = await api.post(`/admin/orders/${order.id}/shipment/${action}`);
        setSh(data);
        toast.success(ACTION_LABELS[action] + " ✓");
      }
      if (action !== "print") load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setBusy(false); }
  };

  if (!sh) return <p className="text-gray-500 text-sm">Carregando...</p>;
  const rec = order.recipient_snapshot || {};
  const allowed = sh.allowed_actions || [];

  return (
    <div className="grid lg:grid-cols-3 gap-4" data-testid={`shipment-panel-${order.order_number}`}>
      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3 flex items-center gap-2"><Truck size={14} /> Envio</h4>
        <Row l="Transportadora" v={order.shipping_company_name || sh.company_name || "—"} />
        <Row l="Serviço" v={order.shipping_service_name || sh.service_name || "—"} />
        <Row l="Valor cliente" v={order.shipping_price_customer != null ? formatBRL(order.shipping_price_customer) : "—"} />
        <Row l="Custo real (negócio)" v={order.shipping_price_quoted != null ? formatBRL(order.shipping_price_quoted) : (sh.price != null ? formatBRL(sh.price) : "—")} />
        <Row l="Prazo" v={order.shipping_delivery_max ? `${order.shipping_delivery_min || order.shipping_delivery_max}–${order.shipping_delivery_max} dias` : "—"} />
        <Row l="CEP destino" v={order.shipping_destination_postal_code || rec.zip || "—"} />
        <Row l="Status" v={<span className="text-[#FFC107] uppercase text-xs font-bold" data-testid={`shipment-status-${order.order_number}`}>{sh.internal_status}</span>} />
        {sh.external_status && <Row l="Status ME" v={sh.external_status} />}
        {sh.tracking_code && <Row l="Rastreio" v={sh.tracking_code} />}
        {sh.cart_order_id && <Row l="Shipment ID" v={<span className="text-[10px] break-all">{sh.cart_order_id}</span>} />}
      </div>

      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3 flex items-center gap-2"><MapPin size={14} /> Destinatário</h4>
        <Row l="Nome" v={rec.name || order.user_name} />
        <Row l="Documento" v={rec.document || "—"} />
        <Row l="Endereço" v={rec.street ? `${rec.street}, ${rec.number} - ${rec.district}` : "—"} />
        <Row l="Cidade/UF" v={rec.city ? `${rec.city}/${rec.uf || rec.state || ""}` : "—"} />
        <Row l="CEP" v={rec.zip || "—"} />
      </div>

      <div className="bm-card p-4">
        <h4 className="text-xs uppercase text-gray-500 font-bold mb-3">Ações / Timeline</h4>
        {order.shipping_provider !== "melhor_envio" ? (
          <p className="text-xs text-gray-500">Pedido sem cotação Melhor Envio (frete padrão).</p>
        ) : (
          <div className="flex flex-wrap gap-2 mb-4">
            {["prepare", "cart", "checkout", "generate", "print", "tracking"].map((a) => (
              <button key={a} onClick={() => act(a)} disabled={busy || !allowed.includes(a)}
                data-testid={`ship-action-${a}-${order.order_number}`}
                className={`text-xs font-semibold rounded-full px-3 py-1.5 flex items-center gap-1 border ${allowed.includes(a) ? "border-[#FFC107] text-[#FFC107] hover:bg-[#FFC107]/10" : "border-[#2e2e2e] text-gray-600 cursor-not-allowed"}`}>
                {a === "print" && <Printer size={12} />}{a === "tracking" && <RefreshCw size={12} />}{ACTION_LABELS[a]}
              </button>
            ))}
          </div>
        )}
        <div className="space-y-1.5">
          {(sh.timeline || []).map((t, i) => (
            <div key={i} className="text-xs text-gray-400 flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#009B3A]" /> {t.label}</div>
          ))}
          {(sh.timeline || []).length === 0 && <p className="text-xs text-gray-600">Nenhum evento ainda.</p>}
        </div>
      </div>
    </div>
  );
}

function Row({ l, v }) {  return (
    <div className="flex justify-between gap-3 py-1 text-xs border-b border-[#1a1a1a] last:border-0">
      <span className="text-gray-500">{l}</span>
      <span className="text-gray-200 text-right">{v}</span>
    </div>
  );
}


const SF_BADGE = {
  PENDING_LABEL: ["Pronto p/ etiqueta", "bg-[#FFC107]/15 text-[#FFC107]"],
  LABEL_READY: ["Etiqueta pronta", "bg-[#1E3A8A]/20 text-[#8fb0ff]"],
  POSTED: ["Postado", "bg-[#1E3A8A]/20 text-[#8fb0ff]"],
  IN_TRANSIT: ["Em trânsito", "bg-[#1E3A8A]/20 text-[#8fb0ff]"],
  OUT_FOR_DELIVERY: ["Saiu para entrega", "bg-[#1E3A8A]/20 text-[#8fb0ff]"],
  DELIVERED: ["Entregue", "bg-[#009B3A]/15 text-[#009B3A]"],
  DELIVERY_FAILED: ["Falha na entrega", "bg-red-500/15 text-red-400"],
  CANCELED: ["Cancelado", "bg-gray-500/15 text-gray-400"],
  RETURNED: ["Devolvido", "bg-gray-500/15 text-gray-400"],
  ERROR: ["Erro", "bg-red-500/15 text-red-400"],
};

function SuperFretePanel({ order }) {
  const [d, setD] = useState(null);
  const [busy, setBusy] = useState(false);
  const [track, setTrack] = useState("");
  const load = () => api.get(`/admin/orders/${order.id}/logistics`).then((r) => setD(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [order.id]);
  if (!d) return <div className="text-xs text-gray-500">Carregando logística…</div>;
  if (!d.superfrete_enabled && !d.shipment)
    return <div className="text-xs text-gray-500 border border-[#2e2e2e] rounded-lg p-3" data-testid={`sf-panel-${order.id}`}>SuperFrete não habilitada. Configure em Admin → SuperFrete.</div>;

  const sh = d.shipment;
  const [label, cls] = sh ? (SF_BADGE[sh.shipment_status] || [sh.shipment_status, "bg-gray-500/15 text-gray-400"]) : ["—", ""];
  const act = async (fn) => { setBusy(true); try { await fn(); await load(); } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(false); } };
  const create = () => { if (!window.confirm("Preparar envio na SuperFrete para este pedido?")) return; act(async () => { const { data } = await api.post(`/admin/orders/${order.id}/logistics/create`); toast.success(data.hybrid_note || "Envio preparado"); }); };
  const sync = () => act(async () => { await api.post(`/admin/orders/${order.id}/logistics/sync`); toast.success("Sincronizado"); });
  const retry = () => act(async () => { await api.post(`/admin/orders/${order.id}/logistics/retry`); toast.success("Reprocessando"); });
  const saveTrack = () => act(async () => { await api.post(`/admin/orders/${order.id}/logistics/tracking`, { tracking_code: track.trim() }); setTrack(""); toast.success("Rastreio registrado"); });
  const openPanel = () => window.open(d.panel_url, "_blank", "noopener,noreferrer");

  return (
    <div className="border border-[#1E3A8A]/40 rounded-lg p-4 bg-[#0b1020]/40" data-testid={`sf-panel-${order.id}`}>
      <div className="flex items-center gap-2 mb-3">
        <Truck size={16} className="text-[#8fb0ff]" />
        <span className="text-sm font-bold text-white uppercase tracking-wide">Logística · SuperFrete</span>
        {sh && <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${cls}`} data-testid={`sf-status-${order.id}`}>{label}</span>}
      </div>
      {sh ? (
        <div className="grid md:grid-cols-2 gap-x-8">
          <Row l="Provider" v={sh.provider} />
          <Row l="Serviço / Transportadora" v={`${sh.service_name || "—"} · ${sh.carrier_name || "—"}`} />
          <Row l="Frete cobrado" v={sh.charged_price != null ? `R$ ${sh.charged_price.toFixed(2)}` : "—"} />
          <Row l="Custo (cotado)" v={sh.quoted_price != null ? `R$ ${sh.quoted_price.toFixed(2)}` : "—"} />
          <Row l="Prazo estimado" v={sh.estimated_days ? `${sh.estimated_days} dia(s)` : "—"} />
          <Row l="Identificador externo" v={sh.external_id || "—"} />
          <Row l="Rastreio" v={sh.tracking_code || "—"} />
          <Row l="Última sincronização" v={sh.last_sync_at ? new Date(sh.last_sync_at).toLocaleString("pt-BR") : "—"} />
          {sh.next_sync_at && !["DELIVERED", "RETURNED", "CANCELED"].includes(sh.shipment_status) && (
            <Row l="Próxima tentativa" v={new Date(sh.next_sync_at).toLocaleString("pt-BR")} />
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-400 mb-2">{d.can_create ? "Pedido pronto para preparar o envio." : (d.blocked_reason || "Envio ainda não preparado.")}</p>
      )}
      {sh?.last_error && <p className="text-xs text-red-400 mt-2" data-testid={`sf-error-${order.id}`}>Erro: {sh.last_error}</p>}
      {d.sync_suspended && (
        <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/30 rounded-lg p-2.5 mt-2" data-testid={`sf-suspended-${order.id}`}>
          <AlertTriangle className="text-red-400 shrink-0" size={15} />
          <p className="text-[11px] text-red-300">Sincronização automática suspensa ({d.sync_suspended_reason || "autenticação inválida"}). Atualize o token em Admin → SuperFrete e teste a conexão.</p>
        </div>
      )}

      <div className="flex flex-wrap gap-2 mt-3">
        {!sh && d.can_create && <button onClick={create} disabled={busy} data-testid={`sf-create-${order.id}`} className="text-xs font-bold rounded-full px-4 py-2 bg-[#FFC107] text-[#111] flex items-center gap-1.5"><PackagePlus size={14} /> Preparar envio</button>}
        <button onClick={openPanel} data-testid={`sf-open-panel-${order.id}`} className="text-xs font-semibold rounded-full px-4 py-2 border border-[#1E3A8A] text-[#8fb0ff] flex items-center gap-1.5"><ExternalLink size={14} /> Abrir na SuperFrete</button>
        {sh && !d.sync_suspended && <button onClick={sync} disabled={busy} data-testid={`sf-sync-${order.id}`} className="text-xs font-semibold rounded-full px-4 py-2 border border-[#2e2e2e] text-gray-300 flex items-center gap-1.5"><RefreshCw size={14} /> Sincronizar</button>}
        {sh?.shipment_status === "ERROR" && <button onClick={retry} disabled={busy} data-testid={`sf-retry-${order.id}`} className="text-xs font-semibold rounded-full px-4 py-2 border border-[#FFC107] text-[#FFC107]">Tentar novamente</button>}
        {sh?.tracking_code && <button onClick={() => { navigator.clipboard?.writeText(sh.tracking_code); toast.success("Rastreio copiado"); }} className="text-xs font-semibold rounded-full px-4 py-2 border border-[#2e2e2e] text-gray-300 flex items-center gap-1.5"><Copy size={13} /> Copiar rastreio</button>}
        {sh?.tracking_url && <a href={sh.tracking_url} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold rounded-full px-4 py-2 border border-[#2e2e2e] text-gray-300">Abrir rastreamento</a>}
      </div>

      {sh && (
        <div className="flex flex-wrap items-end gap-2 mt-3 pt-3 border-t border-[#1a1a1a]">
          <div className="flex-1 min-w-[180px]">
            <label className="text-[11px] text-gray-500 block mb-1">Informar rastreio (emitido no painel)</label>
            <input value={track} onChange={(e) => setTrack(e.target.value)} data-testid={`sf-track-input-${order.id}`} placeholder="Código de rastreio" className="w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <button onClick={saveTrack} disabled={busy || !track.trim()} data-testid={`sf-track-save-${order.id}`} className="text-xs font-bold rounded-full px-4 py-2 bg-[#1E3A8A] text-white disabled:opacity-40">Salvar rastreio</button>
        </div>
      )}
      {sh && (d.timeline || []).length > 0 && (
        <div className="mt-3 pt-3 border-t border-[#1a1a1a]" data-testid={`sf-timeline-${order.id}`}>
          <p className="text-[11px] font-bold text-gray-400 uppercase mb-2">Linha do tempo</p>
          <ul className="space-y-2">
            {(d.timeline || []).map((t) => (
              <li key={t.id} className="flex items-start gap-2 text-xs">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[#8fb0ff] shrink-0" />
                <div>
                  <p className="text-gray-200">{t.description || t.status || t.raw_status}</p>
                  <p className="text-[10px] text-gray-500">
                    {new Date(t.provider_event_at || t.created_at).toLocaleString("pt-BR")} · origem: {t.source}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-[11px] text-gray-600 mt-2">A compra/emissão e o cancelamento da etiqueta são finalizados no painel SuperFrete. Depois, sincronize ou informe o rastreio aqui.</p>
    </div>
  );
}
