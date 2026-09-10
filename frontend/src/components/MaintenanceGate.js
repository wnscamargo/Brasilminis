import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import UnderConstruction from "@/pages/UnderConstruction";
import { LOGO_HEADER } from "@/lib/brand";

// Rotas sempre liberadas (auth/admin/conta e a própria página de preview).
const ALLOW_EXACT = ["/login", "/cadastro", "/recuperar-senha", "/reset-password", "/em-construcao"];
const ALLOW_PREFIX = ["/conta", "/admin"];

function BootSplash() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] grid place-items-center" data-testid="boot-splash">
      <div className="flex flex-col items-center gap-6">
        <img src={LOGO_HEADER} alt="Brasil Minis" className="h-24 w-auto object-contain animate-pulse" />
        <div className="h-8 w-8 rounded-full border-2 border-[#2e2e2e] border-t-[#FFC107] animate-spin" />
      </div>
    </div>
  );
}

export default function MaintenanceGate({ children }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  const [status, setStatus] = useState(undefined); // undefined = carregando

  useEffect(() => {
    let active = true;
    api
      .get("/site-status")
      .then((r) => active && setStatus(r.data))
      .catch(() => active && setStatus({ maintenance_enabled: false })); // resiliência: falha => site normal
    return () => { active = false; };
  }, []);

  // Evita flash do site real: espera status + auth resolverem.
  if (status === undefined || !ready) return <BootSplash />;

  const isAdmin = !!user && user.role === "admin";
  const path = location.pathname;
  const allowed =
    ALLOW_EXACT.includes(path) ||
    ALLOW_PREFIX.some((p) => path === p || path.startsWith(p + "/"));

  if (status.maintenance_enabled && !isAdmin && !allowed) {
    return <UnderConstruction data={status} />;
  }
  return children;
}
