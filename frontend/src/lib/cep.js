import { useRef } from "react";
import api from "@/lib/api";

// Autopreenchimento de endereço por CEP (BrasilAPI + ViaCEP no backend).
// Não sobrescreve número/complemento. onFill recebe {street, district, city, uf}.
// opts.onStart / opts.onError permitem exibir loading e erro amigável (opcionais).
export function useCepAutofill(onFill, opts = {}) {
  const lastCep = useRef("");
  const timer = useRef(null);
  const { onStart, onError } = opts;

  return (rawCep) => {
    const digits = String(rawCep || "").replace(/\D/g, "").slice(0, 8);
    if (digits.length !== 8 || digits === lastCep.current) return;
    lastCep.current = digits;
    if (timer.current) clearTimeout(timer.current);
    if (onStart) onStart();
    timer.current = setTimeout(async () => {
      try {
        const { data } = await api.get(`/cep/${digits}`);
        onFill(data);
      } catch (e) {
        // CEP inválido/serviço fora: permite preenchimento manual
        if (onError) onError(e);
      }
    }, 500);
  };
}

export function maskCep(value) {
  const d = String(value || "").replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}
