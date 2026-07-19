export const BIN_RE = /^\d{9}-\d{4}$|^\d{9,13}$/;
export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const WHATSAPP_RE = /^\+?\d{10,15}$/;

export function money(n?: number | null): string {
  if (n == null) return "";
  return Math.abs(n - Math.round(n)) < 0.005
    ? Math.round(n).toLocaleString()
    : n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
export function bdt(n?: number | null): string { return "BDT " + Number(n || 0).toLocaleString(); }
