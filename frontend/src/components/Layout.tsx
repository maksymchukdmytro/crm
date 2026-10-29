import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  BarChart3, Boxes, History, KanbanSquare, ListOrdered, LogOut, Menu, Package, Plus, Search, Settings,
  ShoppingCart, Wallet,
} from "lucide-react";
import { api, ROOT } from "../lib/api";
import { useLive, useMeta } from "../lib/app";
import CommandPalette from "./CommandPalette";

const NAV: Record<string, { to: string; label: string; icon: typeof ListOrdered }> = {
  orders: { to: "/orders", label: "Замовлення", icon: ListOrdered },
  board: { to: "/board", label: "Дошка", icon: KanbanSquare },
  products: { to: "/products", label: "Товари", icon: Package },
  warehouse: { to: "/warehouse", label: "Склад", icon: Boxes },
  purchases: { to: "/purchases", label: "Закупівлі", icon: ShoppingCart },
  payments: { to: "/payments", label: "Оплати", icon: Wallet },
  reports: { to: "/reports", label: "Звіти", icon: BarChart3 },
  audit: { to: "/audit", label: "Журнал дій", icon: History },
  settings: { to: "/settings", label: "Налаштування", icon: Settings },
};

export default function Layout() {
  const meta = useMeta();
  const { live } = useLive();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [palette, setPalette] = useState(false);

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
        <button className="new" onClick={() => nav("/orders/new")}><Plus size={16} /> Нове замовлення</button>
        <button className="search-btn" onClick={() => setPalette(true)}><Search size={15} /> Пошук <kbd>Ctrl K</kbd></button>
        <nav>
          {meta.nav.map((k) => {
            const n = NAV[k];
            if (!n) return null;
            const Icon = n.icon;
            return <NavLink key={k} to={n.to} className={({ isActive }) => (isActive ? "on" : "")}><Icon size={16} />{n.label}</NavLink>;
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
        <Outlet />
      </main>
      {palette && <CommandPalette onClose={() => setPalette(false)} />}
    </div>
  );
}
