// Стан форми картки замовлення: перетворення замовлення ↔ форма, тіло запиту, порядок позицій (товар → його допродажі).
import { fmtPhoneSafe } from "./util";
import type { Order, OrderItem } from "../../lib/types";

export type Form = {
  customer_name: string; phone: string; email: string; comment: string; status_id: number; manager_id: number | "";
  payment_type: string; payment_method_id: number | ""; source_id: number | ""; office_id: number | ""; np_account_id: number | ""; reason_id: number | "";
  legal_entity_id: number | "";
  mark_id: number | ""; remind_at: string; country: string; extra1: string; extra2: string; extra3: string; extra4: string;
  prepayment: string; discount: string; delivery_method: string;
  city_name: string; city_ref: string; warehouse_name: string; warehouse_ref: string; address: string; postcode: string;
  ttn: string; site: string; utm_source: string; utm_medium: string; utm_campaign: string; utm_content: string; utm_term: string;
  items: OrderItem[];
};

export const UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"] as const;
export const EXTRA = ["extra1", "extra2", "extra3", "extra4"] as const;

let keySeq = 0;
export const newKey = () => `i${++keySeq}`;

export function toForm(o: Partial<Order> | undefined, defaultStatus: number): Form {
  const s = (v: unknown) => (v === null || v === undefined ? "" : String(v));
  const m = (v: number | undefined | null) => (v ? String(v) : "");
  return {
    customer_name: s(o?.customer_name), phone: fmtPhoneSafe(o?.phone ?? ""), email: s(o?.email), comment: s(o?.comment),
    legal_entity_id: o?.legal_entity_id ?? "",
    status_id: o?.status_id ?? defaultStatus, manager_id: o?.manager_id ?? "",
    payment_type: o?.payment_type || "cod", payment_method_id: o?.payment_method_id ?? "", source_id: o?.source_id ?? "",
    office_id: o?.office_id ?? "", np_account_id: o?.np_account_id ?? "", reason_id: o?.reason_id ?? "", mark_id: o?.mark_id ?? "",
    remind_at: toLocalInput(o?.remind_at),
    country: o?.country || "UA", extra1: s(o?.extra1), extra2: s(o?.extra2), extra3: s(o?.extra3), extra4: s(o?.extra4),
    prepayment: m(o?.prepayment), discount: m(o?.discount),
    delivery_method: o?.delivery_method || "novaposhta",
    city_name: s(o?.city_name), city_ref: s(o?.city_ref), warehouse_name: s(o?.warehouse_name), warehouse_ref: s(o?.warehouse_ref),
    address: s(o?.address), postcode: s(o?.postcode), ttn: s(o?.ttn), site: s(o?.site),
    utm_source: s(o?.utm_source), utm_medium: s(o?.utm_medium), utm_campaign: s(o?.utm_campaign),
    utm_content: s(o?.utm_content), utm_term: s(o?.utm_term),
    items: arrange((o?.items ?? []).map((i) => ({ ...i, price: String(i.price), key: newKey() }))),
  };
}

/** datetime-local працює в місцевому часі без поясу; сервер зберігає UTC. */
export function toLocalInput(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function payload(f: Form, version?: string) {
  const { items, manager_id, payment_method_id, source_id, office_id, np_account_id, reason_id, mark_id, remind_at, legal_entity_id, ...rest } = f;
  return {
    ...rest, version, manager_id: manager_id || null, legal_entity_id: legal_entity_id || null,
    payment_method_id: payment_method_id || null, source_id: source_id || null, office_id: office_id || null,
    np_account_id: np_account_id || null,
    reason_id: reason_id || null, mark_id: mark_id || null, remind_at: remind_at ? new Date(remind_at).toISOString() : "",
    items: items.filter((i) => i.name.trim()).map((i) => ({
      product_id: i.product_id, variant_id: i.variant_id ?? null, name: i.name, qty: i.qty, price: i.price, upsell: i.upsell,
      upsell_for: i.upsell ? i.upsell_for ?? null : null,
    })),
  };
}

/** Порядок позицій: основний товар → його допродажі; допродажі без свого товару — у кінці. Так і зберігається (друк, ТТН, чеки). */
export function arrange(items: OrderItem[]): OrderItem[] {
  const ups = items.filter((i) => i.upsell);
  const used = new Set<string | undefined>();
  const out: OrderItem[] = [];
  for (const m of items.filter((i) => !i.upsell)) {
    out.push(m);
    for (const u of ups) if (!used.has(u.key) && m.product_id && u.upsell_for === m.product_id) { out.push(u); used.add(u.key); }
  }
  return [...out, ...ups.filter((u) => !used.has(u.key))];
}
