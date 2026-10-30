import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CornerDownLeft, Search } from "lucide-react";
import { createPortal } from "react-dom";
import { api, qs } from "../lib/api";
import { useDebounced, useMeta } from "../lib/app";
import { money, phone } from "../lib/format";
import type { OrderList } from "../lib/types";

type Row = { key: string; to: string; main: string; sub: string; group: string };
type CustomerList = { rows: { id: number; name: string; phone: string; orders?: number }[] };

// Ctrl K: пошук по CRM — групи Замовлення, Покупці, Товари, Дії (UI-DESIGN §3).
export default function CommandPalette({ onClose, placeholder }: { onClose: () => void; placeholder?: string }) {
  const meta = useMeta();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const [hl, setHl] = useState(0);
  const dq = useDebounced(q.trim(), 200);
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);
  const canCustomers = meta.nav.includes("customers");

  const orders = useQuery({
    queryKey: ["palette", dq],
    queryFn: () => api.get<OrderList>(`/orders${qs({ q: dq, limit: 6, counts: 0 })}`),
    enabled: dq.length >= 2,
  });
  const customers = useQuery({
    queryKey: ["palette-c", dq],
    queryFn: () => api.get<CustomerList>(`/customers${qs({ q: dq, limit: 4 })}`),
    enabled: canCustomers && dq.length >= 2,
  });

  const low = dq.toLowerCase();
  const actions = [
    { label: "Нове замовлення", to: "/orders/new" },
    ...(meta.leads_enabled && meta.nav.includes("leads") ? [{ label: "Новий лід", to: "/leads/new" }] : []),
    { label: "Головна", to: "/home" }, { label: "Замовлення", to: "/orders" }, { label: "Дошка", to: "/board" },
    { label: "Товари", to: "/products" }, { label: "Склад", to: "/warehouse" }, { label: "Закупівлі", to: "/purchases" },
    { label: "Оплати", to: "/payments" }, { label: "Статистика", to: "/stats" }, { label: "Звіти", to: "/reports" },
    { label: "Журнал дій", to: "/audit" }, { label: "Налаштування", to: "/settings" }, { label: "Мій профіль", to: "/profile" },
  ].filter((p) => (!dq || p.label.toLowerCase().includes(low)) && (p.to === "/orders/new" || p.to === "/profile" || meta.nav.includes(p.to.slice(1).split("/")[0])));

  const products = dq.length >= 2
    ? meta.products.filter((p) => p.name.toLowerCase().includes(low) || (p.sku || "").toLowerCase().includes(low)).slice(0, 4)
    : [];

  const results: Row[] = [
    ...(orders.data?.items ?? []).map((o) => ({ group: "Замовлення", key: `o${o.id}`, to: `/orders/${o.id}`, main: `№${o.id} · ${o.customer_name || "без імені"}`,
      sub: `${phone(o.phone)} · ${money(o.total)} ₴ · ${statuses[o.status_id]?.name ?? ""}` })),
    ...(customers.data?.rows ?? []).map((c) => ({ group: "Покупці", key: `c${c.id}`, to: `/customers/${c.id}`, main: c.name || "без імені", sub: phone(c.phone) })),
    ...products.map((p) => ({ group: "Товари", key: `p${p.id}`, to: `/products?open=${p.id}`, main: p.name, sub: `${p.sku || ""} · ${money(p.price)} ₴` })),
    ...actions.map((p) => ({ group: "Дії", key: p.to, to: p.to, main: p.label, sub: "Перейти" })),
  ];

  useEffect(() => setHl(0), [dq, orders.data, customers.data]);
  const go = (i: number) => { const r = results[i]; if (r) { nav(r.to); onClose(); } };

  return createPortal(
    <div className="modal palette-wrap" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="palette" role="dialog" aria-label="Пошук">
        <div className="palette-in"><Search size={17} />
          <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} aria-label="Пошук"
            placeholder={placeholder ?? "Шукати замовлення, телефон, ТТН або товар…"}
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose();
              else if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => Math.min(h + 1, results.length - 1)); }
              else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => Math.max(h - 1, 0)); }
              else if (e.key === "Enter") { e.preventDefault(); go(hl); }
            }} />
          <kbd>Esc</kbd>
        </div>
        <div className="palette-list" role="listbox">
          {results.map((r, i) => (
            <div key={r.key}>
              {(i === 0 || results[i - 1].group !== r.group) && <div className="palette-group">{r.group}</div>}
              <div role="option" aria-selected={i === hl} className={`palette-item ${i === hl ? "hl" : ""}`} onMouseEnter={() => setHl(i)} onMouseDown={() => go(i)}>
                <span>{r.main}</span><small>{r.sub}</small>{i === hl && <CornerDownLeft size={14} />}
              </div>
            </div>
          ))}
          {dq.length >= 2 && orders.data && !orders.data.items.length && !customers.data?.rows.length && !products.length && <div className="palette-empty">Нічого не знайдено</div>}
        </div>
      </div>
    </div>,
    document.body,
  );
}
