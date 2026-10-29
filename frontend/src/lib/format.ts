const NBSP = " ";

export function money(v: number | string | null | undefined, decimals = false): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? "0").replace(",", "."));
  if (!isFinite(n)) return "0";
  const r = Math.round(n * 100) / 100;
  const s = !decimals && r % 1 === 0 ? r.toFixed(0) : r.toFixed(2);
  return s.replace(/\B(?=(\d{3})+(?!\d))/g, NBSP);
}

export function num(v: unknown): number {
  const n = parseFloat(String(v ?? "").replace(/\s/g, "").replace(",", "."));
  return isFinite(n) ? n : 0;
}

export function phone(v: string | null | undefined): string {
  if (v && v.length === 12 && v.startsWith("380")) {
    return `+38 ${v.slice(2, 5)} ${v.slice(5, 8)} ${v.slice(8, 10)} ${v.slice(10)}`;
  }
  return v ?? "";
}

const dtf = new Intl.DateTimeFormat("uk-UA", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
const dshort = new Intl.DateTimeFormat("uk-UA", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
const donly = new Intl.DateTimeFormat("uk-UA", { day: "2-digit", month: "2-digit", year: "numeric" });

export function dt(iso: string | null | undefined, short = false): string {
  if (!iso) return "";
  const d = new Date(iso);
  return (short ? dshort : dtf).format(d).replace(",", "");
}

export function date(iso: string | null | undefined): string {
  return iso ? donly.format(new Date(iso)) : "";
}

export function ago(iso: string | null | undefined): string {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "щойно";
  if (s < 3600) return `${Math.floor(s / 60)} хв тому`;
  if (s < 86400) return `${Math.floor(s / 3600)} год тому`;
  return dt(iso, true);
}

export function isoDay(d: Date): string {
  const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return z.toISOString().slice(0, 10);
}

export function itemsLabel(items: { name: string; qty: number }[]): string {
  return items.map((i) => (i.qty > 1 ? `${i.name} ×${i.qty}` : i.name)).join(", ");
}
