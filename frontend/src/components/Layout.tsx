import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity, BarChart3, Boxes, ChartColumnStacked, Contact, History, Inbox, KanbanSquare, LogOut, Menu, Package, PackagePlus,
  Plus, ReceiptText, Search, Settings, ShoppingCart, Wallet, House,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { useLive, useMeta } from "../lib/app";
import type { OrderList } from "../lib/types";
import CommandPalette from "./CommandPalette";
import { ErrorBoundary } from "../lib/monitoring";

type Item = { to: string; label: string; icon: typeof Inbox };
const NAV: Record<string, Item> = {
  home: { to: "/home", label: "Головна", icon: House },
  leads: { to: "/leads", label: "Ліди", icon: Inbox },
  orders: { to: "/orders", label: "Замовлення", icon: ReceiptText },
  board: { to: "/board", label: "Дошка", icon: KanbanSquare },
  customers: { to: "/customers", label: "Покупці", icon: Contact },
  products: { to: "/products", label: "Товари", icon: Package },
  warehouse: { to: "/warehouse", label: "Склад", icon: Boxes },
  purchases: { to: "/purchases", label: "Закупівлі", icon: ShoppingCart },
  payments: { to: "/payments", label: "Оплати", icon: Wallet },
  stats: { to: "/stats", label: "Статистика", icon: ChartColumnStacked },
  reports: { to: "/reports", label: "Звіти", icon: BarChart3 },
  audit: { to: "/audit", label: "Журнал дій", icon: History },
  settings: { to: "/settings", label: "Налаштування", icon: Settings },
  system: { to: "/system", label: "Система", icon: Activity },
};
// групи меню — за видом роботи
const GROUPS: [string, string[]][] = [
  ["", ["home"]],
  ["Продажі", ["leads", "orders", "board", "customers"]],
  ["Склад", ["products", "warehouse", "purchases"]],
  ["Гроші й аналітика", ["payments", "stats", "reports"]],
  ["Керування", ["audit", "settings", "system"]],
];

export default function Layout() {
  const meta = useMeta();
  const { live } = useLive();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [palette, setPalette] = useState(false);
  const canProducts = meta.user.role === "admin" || meta.user.role === "warehouse";
  // скільки нових лідів чекає на обробку
  const leads = useQuery({
    queryKey: ["nav-leads"], enabled: meta.nav.includes("leads"), refetchInterval: 60_000,
    queryFn: () => api.get<OrderList>(`/orders${qs({ stage: "lead", limit: 1 })}`),
  });
  const newStatus = meta.statuses.find((s) => s.code === "new")?.id;
  const fresh = newStatus ? leads.data?.counts?.[String(newStatus)] ?? 0 : 0;
  const leadTotal = leads.data?.total ?? 0;

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((p) => !p); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  useEffect(() => { document.title = meta.company; }, [meta.company]);

  const logout = async () => {
    await api.post("/auth/logout");
    qc.clear();
    window.location.href = `${ROOT}/`;
  };

  return (
    <div className="shell">
      <aside className={`side ${open ? "open" : ""}`} onClick={(e) => { if ((e.target as HTMLElement).closest("a")) setOpen(false); }}>
        <div className="brand"><span className="brand-mark" /><span>{meta.company}</span>
          <span className={`live-dot ${live ? "on" : ""}`} title={live ? "Оновлення в реальному часі" : "Оновлення кожні 30 с"} />
        </div>
        <div className="side-actions" style={canProducts ? undefined : { gridTemplateColumns: "1fr" }}>
          <button className="new" onClick={() => { nav("/orders/new"); setOpen(false); }}><Plus size={16} /> Замовлення</button>
          {canProducts && <button className="new-product" title="Додати товар" onClick={() => { nav("/products?new=1"); setOpen(false); }}><PackagePlus size={16} /> Товар</button>}
        </div>
        <button className="search-btn" onClick={() => setPalette(true)}><Search size={15} /> Пошук <kbd>Ctrl K</kbd></button>
        <nav>
          {GROUPS.map(([title, keys]) => {
            const items = keys.filter((k) => meta.nav.includes(k) && NAV[k]);
            if (!items.length) return null;
            return (
              <div className="nav-group" key={title}>
                {title && <div className="nav-title">{title}</div>}
                {items.map((k) => {
                  const n = NAV[k];
                  const Icon = n.icon;
                  return (
                    <NavLink key={k} to={n.to} className={({ isActive }) => (isActive ? "on" : "")}>
                      <Icon size={17} />{n.label}
                      {k === "leads" && leadTotal > 0 && <span className={`count ${fresh ? "hot" : ""}`} title={fresh ? `${fresh} нових` : `${leadTotal} у роботі`}>{fresh || leadTotal}</span>}
                    </NavLink>
                  );
                })}
              </div>
            );
          })}
        </nav>
        <div className="side-foot">
          <NavLink to="/profile" className="me"><span className="av">{meta.user.name.slice(0, 1).toUpperCase()}</span>
            <span><b>{meta.user.name}</b><small>{meta.user.role_name}</small></span></NavLink>
          <button className="link" onClick={logout} title="Вийти"><LogOut size={16} /></button>
        </div>
        <a className="classic-link" href={`${ROOT}/classic/orders`}>Класичний інтерфейс</a>
      </aside>
      {open && <div className="side-backdrop" onClick={() => setOpen(false)} />}
      <main className="main">
        <button className="burger" onClick={() => setOpen(true)} aria-label="Меню"><Menu size={18} /></button>
        <ErrorBoundary area="page"><Outlet /></ErrorBoundary>
      </main>
      {palette && <CommandPalette onClose={() => setPalette(false)} />}
    </div>
  );
}
