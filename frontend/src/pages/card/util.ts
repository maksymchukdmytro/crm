import { ROOT } from "../../lib/api";
import { phone } from "../../lib/format";

export const fmtPhoneSafe = (v: string) => phone(v);

export function plural(n: number, one: string, few: string, many: string) {
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
}

export const digits = (v: string) => (v || "").replace(/\D/g, "");

/** Друк наклейки (маркування Rozetka або НП): вікно відкриваємо одразу — інакше браузер заблокує його після очікування. */
export async function printLabel(orderId: number, toast: (msg: string, kind?: "error") => void, url?: string) {
  const w = window.open("", "_blank");
  try {
    const r = await fetch(`${ROOT}${url ?? `/api/orders/${orderId}/label`}`, { credentials: "same-origin" });
    if (!r.ok) {
      let msg = `Не вдалося отримати наклейку (${r.status})`;
      try { const j = await r.json(); msg = j.error || j.detail || msg; } catch { /* не JSON */ }
      throw new Error(msg);
    }
    const blob = URL.createObjectURL(await r.blob());
    if (w) w.location.href = blob; else window.location.href = blob;
  } catch (e) {
    w?.close();
    toast((e as Error).message, "error");
  }
}

export const shortDate = (iso?: string | null) =>
  iso ? new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString("uk-UA", { day: "2-digit", month: "2-digit" }) : "";
export const dateTime = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleString("uk-UA", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).replace(",", ",") : "";
