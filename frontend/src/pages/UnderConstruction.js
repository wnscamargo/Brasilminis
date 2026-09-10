import { useEffect, useMemo, useState } from "react";
import { MessageCircle, Instagram } from "lucide-react";
import api from "@/lib/api";
import { useSiteConfig } from "@/context/SiteConfigContext";

const BG = "https://images.unsplash.com/photo-1637494873826-795116ba38cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

function useCountdown(launchDate, enabled) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!enabled || !launchDate) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [enabled, launchDate]);

  return useMemo(() => {
    if (!enabled || !launchDate) return null;
    const target = new Date(launchDate).getTime();
    if (isNaN(target)) return null;
    let diff = Math.max(0, Math.floor((target - now) / 1000));
    const d = Math.floor(diff / 86400); diff -= d * 86400;
    const h = Math.floor(diff / 3600); diff -= h * 3600;
    const m = Math.floor(diff / 60); const s = diff - m * 60;
    return { d, h, m, s };
  }, [now, launchDate, enabled]);
}

function Unit({ value, label }) {
  return (
    <div className="flex flex-col items-center" data-testid={`countdown-${label.toLowerCase()}`}>
      <div className="w-16 h-16 md:w-20 md:h-20 grid place-items-center rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
        <span className="font-display font-black text-2xl md:text-3xl text-white tabular-nums">
          {String(value).padStart(2, "0")}
        </span>
      </div>
      <span className="mt-2 text-[10px] md:text-xs uppercase tracking-widest text-gray-400">{label}</span>
    </div>
  );
}

export default function UnderConstruction({ data: propData }) {
  const [data, setData] = useState(propData || null);
  const { logoSrc, logo_width } = useSiteConfig();

  useEffect(() => {
    if (propData) { setData(propData); return; }
    let active = true;
    api.get("/site-status").then((r) => active && setData(r.data)).catch(() => active && setData({}));
    return () => { active = false; };
  }, [propData]);

  const d = data || {};
  const cd = useCountdown(d.launch_date, d.show_countdown);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0a0a0a] text-white" data-testid="under-construction">
      <style>{`
        @keyframes bmFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        @keyframes bmSweep { 0%{transform:translateX(-120%)} 100%{transform:translateX(120%)} }
        @keyframes bmFade { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
      `}</style>

      {/* fundo */}
      <div className="absolute inset-0">
        <img src={BG} alt="" className="w-full h-full object-cover opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0a]/70 via-[#0a0a0a]/85 to-[#0a0a0a]" />
        <div className="absolute -top-40 -left-40 w-[520px] h-[520px] rounded-full blur-3xl"
             style={{ background: "radial-gradient(circle,#1E3A8A55,transparent 70%)" }} />
        <div className="absolute -bottom-40 -right-40 w-[520px] h-[520px] rounded-full blur-3xl"
             style={{ background: "radial-gradient(circle,#FFC10733,transparent 70%)" }} />
        {/* linha de velocidade */}
        <div className="absolute top-1/3 left-0 right-0 h-px overflow-hidden opacity-40">
          <div className="h-px w-1/3 bg-gradient-to-r from-transparent via-[#FFC107] to-transparent"
               style={{ animation: "bmSweep 4s linear infinite" }} />
        </div>
      </div>

      {/* conteúdo */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-5 py-16 text-center">
        <div style={{ animation: "bmFade .6s ease both" }}>
          <img src={logoSrc} alt="Brasil Minis - Miniaturas e Diecast"
               className="w-auto h-auto object-contain mx-auto drop-shadow-[0_10px_30px_rgba(0,0,0,0.6)]"
               style={{ maxWidth: `min(${(logo_width || 200) * 1.4}px, 80vw)`, maxHeight: "220px", animation: "bmFloat 5s ease-in-out infinite" }} />
        </div>

        <p className="mt-8 text-[#FFC107] text-xs md:text-sm font-bold uppercase tracking-[0.3em]"
           style={{ animation: "bmFade .6s ease both .1s" }}>Brasil Minis</p>

        <h1 className="mt-3 font-display font-black uppercase text-4xl sm:text-5xl lg:text-6xl leading-[1.05] max-w-3xl"
            style={{ animation: "bmFade .6s ease both .15s" }}
            data-testid="uc-title">
          {d.title || "Estamos preparando algo incrível"}
        </h1>

        {d.subtitle ? (
          <p className="mt-5 text-base md:text-lg text-gray-300 max-w-2xl" style={{ animation: "bmFade .6s ease both .2s" }}>
            {d.subtitle}
          </p>
        ) : null}
        {d.message ? (
          <p className="mt-3 text-sm md:text-base text-gray-400 max-w-2xl" style={{ animation: "bmFade .6s ease both .25s" }}>
            {d.message}
          </p>
        ) : null}

        {cd ? (
          <div className="mt-10 flex items-center gap-3 md:gap-5" style={{ animation: "bmFade .6s ease both .3s" }}>
            <Unit value={cd.d} label="Dias" />
            <Unit value={cd.h} label="Horas" />
            <Unit value={cd.m} label="Min" />
            <Unit value={cd.s} label="Seg" />
          </div>
        ) : null}

        {(d.show_whatsapp || d.show_instagram) ? (
          <div className="mt-10 flex flex-col sm:flex-row items-center gap-3" style={{ animation: "bmFade .6s ease both .35s" }}>
            {d.show_whatsapp && d.whatsapp_url ? (
              <a href={d.whatsapp_url} target="_blank" rel="noopener noreferrer"
                 data-testid="uc-whatsapp"
                 className="inline-flex items-center gap-2 bg-[#009B3A] hover:bg-[#00832f] transition-colors text-white font-bold rounded-full px-6 py-3">
                <MessageCircle size={18} /> Falar pelo WhatsApp
              </a>
            ) : null}
            {d.show_instagram && d.instagram_url ? (
              <a href={d.instagram_url} target="_blank" rel="noopener noreferrer"
                 data-testid="uc-instagram"
                 className="inline-flex items-center gap-2 rounded-full px-6 py-3 font-bold text-white"
                 style={{ background: "linear-gradient(90deg,#833AB4,#FD1D1D,#FCB045)" }}>
                <Instagram size={18} /> Seguir no Instagram
              </a>
            ) : null}
          </div>
        ) : null}

        <p className="mt-14 text-xs text-gray-600">© {new Date().getFullYear()} Brasil Minis — Miniaturas & Diecast</p>
      </div>
    </div>
  );
}
