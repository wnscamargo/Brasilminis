// Máscara e normalização de CPF no frontend (validação matemática é feita no backend).
export function maskCpf(value) {
  const d = String(value || "").replace(/\D/g, "").slice(0, 11);
  return d
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

export function normalizeCpf(value) {
  return String(value || "").replace(/\D/g, "");
}
