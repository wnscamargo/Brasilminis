import { createContext, useContext, useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import { LOGO_HEADER } from "@/lib/brand";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const DEFAULT_LOGO = LOGO_HEADER; // fallback institucional (servido pelo frontend)

export function resolveLogo(url) {
  if (!url) return DEFAULT_LOGO;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/api")) return `${BACKEND_URL}${url}`;
  return url;
}

const SiteConfigContext = createContext(null);

export function SiteConfigProvider({ children }) {
  const [config, setConfig] = useState({ logo_url: null, logo_width: 200 });

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/site-config");
      setConfig(data);
    } catch {
      setConfig({ logo_url: null, logo_width: 200 }); // fallback resiliente
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const value = {
    ...config,
    logoSrc: resolveLogo(config.logo_url),
    isDefaultLogo: !config.logo_url,
    refresh,
  };
  return <SiteConfigContext.Provider value={value}>{children}</SiteConfigContext.Provider>;
}

export const useSiteConfig = () => useContext(SiteConfigContext) || { logoSrc: DEFAULT_LOGO, logo_width: 200, isDefaultLogo: true, refresh: () => {} };
