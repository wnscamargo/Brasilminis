import { useEffect, useRef, useState, useCallback } from "react";
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

export default function Lightbox({ images = [], index = 0, onClose, onIndex }) {
  const [i, setI] = useState(index);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef(null);
  const touch = useRef(null);
  const dialogRef = useRef(null);
  const prevFocus = useRef(null);
  const many = images.length > 1;

  const reset = useCallback(() => { setZoom(1); setPan({ x: 0, y: 0 }); }, []);
  const go = useCallback((d) => { if (!many) return; setI((p) => (p + d + images.length) % images.length); }, [images.length, many]);
  const zoomBy = useCallback((f) => setZoom((z) => Math.min(5, Math.max(1, +(z + f).toFixed(2)))), []);

  useEffect(() => { setI(index); }, [index]);
  // Sincroniza índice com o pai e reseta zoom quando a imagem muda (fora do render).
  useEffect(() => { onIndex && onIndex(i); reset(); /* eslint-disable-next-line */ }, [i]);

  useEffect(() => {
    prevFocus.current = document.activeElement;
    dialogRef.current?.focus();
    const onKey = (e) => {
      const t = e.target;
      if (t && (/(input|textarea|select)/i.test(t.tagName) || t.isContentEditable)) return;
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
      else if (e.key === "+" || e.key === "=") { e.preventDefault(); zoomBy(0.5); }
      else if (e.key === "-") { e.preventDefault(); zoomBy(-0.5); }
      else if (e.key === "0") reset();
    };
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); prevFocus.current?.focus?.(); };
  }, [go, onClose, reset, zoomBy]);

  const onWheel = (e) => { e.preventDefault(); zoomBy(e.deltaY < 0 ? 0.3 : -0.3); };
  const onDown = (e) => { if (zoom <= 1) return; drag.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }; };
  const onMove = (e) => { if (!drag.current) return; setPan({ x: e.clientX - drag.current.x, y: e.clientY - drag.current.y }); };
  const onUp = () => { drag.current = null; };
  const onTouchStart = (e) => { if (e.touches.length === 1) touch.current = { x: e.touches[0].clientX, t: Date.now() }; };
  const onTouchEnd = (e) => {
    if (!touch.current || zoom > 1) { touch.current = null; return; }
    const dx = (e.changedTouches[0]?.clientX ?? 0) - touch.current.x;
    if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1);
    touch.current = null;
  };

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 flex flex-col" role="dialog" aria-modal="true" aria-label="Galeria de imagens do produto"
      ref={dialogRef} tabIndex={-1} data-testid="lightbox">
      <div className="flex items-center justify-between p-4 text-white">
        {many ? <span className="text-sm text-gray-300" data-testid="lightbox-counter">{`${i + 1} / ${images.length}`}</span> : <span />}
        <div className="hidden md:block text-xs text-gray-500">← → navegar · + − zoom · Esc fechar</div>
        <div className="flex items-center gap-2">
          <button onClick={() => zoomBy(0.5)} aria-label="Aumentar zoom" data-testid="lightbox-zoom-in" className="p-2 rounded-full bg-white/10 hover:bg-white/20"><ZoomIn size={18} /></button>
          <button onClick={() => zoomBy(-0.5)} aria-label="Diminuir zoom" data-testid="lightbox-zoom-out" className="p-2 rounded-full bg-white/10 hover:bg-white/20"><ZoomOut size={18} /></button>
          <button onClick={reset} aria-label="Restaurar zoom" data-testid="lightbox-zoom-reset" className="p-2 rounded-full bg-white/10 hover:bg-white/20"><RotateCcw size={18} /></button>
          <button onClick={onClose} aria-label="Fechar" data-testid="lightbox-close" className="p-2 rounded-full bg-white/10 hover:bg-white/20"><X size={18} /></button>
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden flex items-center justify-center select-none"
        onWheel={onWheel} onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} onMouseLeave={onUp}
        onTouchStart={onTouchStart} onTouchEnd={onTouchEnd} onDoubleClick={() => (zoom > 1 ? reset() : zoomBy(1))}>
        {many && (
          <button onClick={() => go(-1)} aria-label="Imagem anterior" data-testid="lightbox-prev" className="absolute left-3 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"><ChevronLeft size={22} /></button>
        )}
        <img src={images[i]} alt={`Imagem ${i + 1}`} draggable={false} data-testid="lightbox-image"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, cursor: zoom > 1 ? "grab" : "zoom-in" }}
          onClick={() => zoom === 1 && zoomBy(1)}
          className="max-h-[75vh] max-w-[90vw] object-contain transition-transform duration-100" />
        {many && (
          <button onClick={() => go(1)} aria-label="Próxima imagem" data-testid="lightbox-next" className="absolute right-3 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"><ChevronRight size={22} /></button>
        )}
      </div>

      {many && (
        <div className="flex gap-2 justify-center p-4 overflow-x-auto">
          {images.map((img, k) => (
            <button key={k} onClick={() => { setI(k); onIndex && onIndex(k); reset(); }} aria-label={`Ir para imagem ${k + 1}`}
              data-testid={`lightbox-thumb-${k}`}
              className={`h-14 w-14 rounded-lg overflow-hidden border-2 shrink-0 ${i === k ? "border-[#FFC107]" : "border-white/20"}`}>
              <img src={img} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
