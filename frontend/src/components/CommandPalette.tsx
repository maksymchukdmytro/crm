import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CornerDownLeft, Search } from "lucide-react";
import { createPortal } from "react-dom";
import { api, qs } from "../lib/api";
import { useDebounced, useMeta } from "../lib/app";
import { money, phone } from "../lib/format";
import type { OrderList } from "../lib/types";

// Ctrl+K: пошук замовлень (№, телефон, ПІБ, ТТН) і швидкий перехід по розділах.
export default function CommandPalette({ onClose }: { onClose: () => void }) {
  const meta = useMeta();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const [hl, setHl] = useState(0);
  const dq = useDebounced(q.trim(), 200);
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);

  const { data } = useQuery({
    queryKey: ["palette", dq],
    queryFn: () => api.get<OrderList>(`/orders${qs({ q: dq, limit: 8, counts: 0 })}`),
    enabled: dq.length >= 2,
  });

  const pages = [
    { label: "Нове замовлення", to: "/orders/new" },
    { label: "Замовлення", to: "/orders" }, { label: "Дошка", to: "/board" }, { label: "Товари", to: "/products" },
    { label: "Склад", to: "/warehouse" }, { label: "Закупівлі", to: "/purchases" }, { label: "Оплати", to: "/payments" },
    { label: "Звіти", to: "/reports" }, { label: "Журнал дій", to: "/audit" }, { label: "Налаштування", to: "/settings" },
    { label: "Мій профіль", to: "/profile" },
  ].filter((p) => !dq || p.label.toLowerCase().includes(dq.toLowerCase()));

  const results = [
    ...(data?.items ?? []).map((o) => ({ key: `o${o.id}`, to: `/orders/${o.id}`, main: `№${o.id} · ${o.customer_name || "без імені"}`,
      sub: `${phone(o.phone)} · ${money(o.total)} ₴ · ${statuses[o.status_id]?.name ?? ""}` })),
    ...pages.map((p) => ({ key: p.to, to: p.to, main: p.label, sub: "Перейти" })),
  ];

  useEffect(() => setHl(0), [dq, data]);

  const go = (i: number) => { const r = results[i]; if (r) { nav(r.to); onClose(); } };

  return createPortal(
    <div className="modal palette-wrap" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="palette">
        <div className="palette-in"><Search size={17} />
          <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Пошук замовлення: №, телефон, ПІБ, ТТН… або розділ"
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose();
              else if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => Math.min(h + 1, results.length - 1)); }
              else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => Math.max(h - 1, 0)); }
              else if (e.key === "Enter") { e.preventDefault(); go(hl); }
            }} />
        </div>
        <div className="palette-list">
          {results.map((r, i) => (
            <div key={r.key} className={`palette-item ${i === hl ? "hl" : ""}`} onMouseEnter={() => setHl(i)} onMouseDown={() => go(i)}>
              <span>{r.main}</span><small>{r.sub}</small>{i === hl && <CornerDownLeft size={14} />}
            </div>
          ))}
          {dq.length >= 2 && data && !data.items.length && <div className="palette-empty">Замовлень не знайдено</div>}
        </div>
      </div>
    </div>,
    document.body,
  );
}
