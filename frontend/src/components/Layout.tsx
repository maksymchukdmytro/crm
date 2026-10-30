// Каркас нового інтерфейсу (UI-DESIGN §3): бокова панель 236 px (згортається до 64 px), верхня смуга 48 px, робоча область,
// кнопка «+» з меню швидких дій, глобальні клавіші N / L / P / C / T, Ctrl K.
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity, BarChart3, Bell, Boxes, Building2, ChartColumnStacked, Check, ChevronDown, Contact, ExternalLink, FileText, History, Inbox,
  KanbanSquare, LogOut, Menu, MessageSquare, Package, PanelLeftClose, PanelLeftOpen, ReceiptText, ScanBarcode, Search, Settings,
  ShoppingCart, UserPlus, UserRound, Wallet, House, PackagePlus, PhoneIncoming, AlarmClock,
} from "lucide-react";
import { api, ROOT } from "../lib/api";
import { useLive, useMeta } from "../lib/app";
import { dt as dateTime } from "../lib/format";
import type { Counters, Notifications, SavedFilter } from "../lib/types";
import CommandPalette from "./CommandPalette";
import { ErrorBoundary } from "../lib/monitoring";
import { Fab, IconButton, MenuButton, inField, type QuickAction } from "./ui";

type Item = { to: string; label: string; icon: typeof Inbox };
const NAV: Record<string, Item> = {
  home: { to: "/home", label: "Головна", icon: House },
  leads: { to: "/leads", label: "Ліди", icon: Inbox },
  orders: { to: "/orders", label: "Замовлення", icon: ReceiptText },
  invoices: { to: "/invoices", label: "Видаткові накладні", icon: FileText },
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
const GROUPS: [string, string[]][] = [
  ["Продажі", ["home", "leads", "orders", "invoices", "board", "customers"]],
  ["Склад", ["products", "warehouse", "purchases"]],
  ["Гроші й аналітика", ["payments", "stats", "reports"]],
  ["Керування", ["audit", "settings", "system"]],
];

const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";

export function useCounters(): Counters {
  const meta = useMeta();
  const { data } = useQuery({
    queryKey: ["counters"], queryFn: () => api.get<Counters>("/counters"), refetchInterval: 60_000,
    initialData: meta.counters ?? undefined, staleTime: 20_000,
  });
  return data ?? { leads_new: 0, orders_unsorted: 0, reminders_due: 0, saved: {} };
}

export default function Layout() {
  const meta = useMeta();
  const { live } = useLive();
  const nav = useNavigate();
  const loc = useLocation();
  const qc = useQueryClient();
  const counters = useCounters();
  const [drawer, setDrawer] = useState(false);
  const [palette, setPalette] = useState<null | { initial?: string; hint?: string }>(null);
  const [narrow, setNarrow] = useState(() => window.matchMedia("(max-width: 1279px)").matches);
  const prefCollapsed = meta.prefs?.["sidebar.collapsed"] === true;
  const collapsed = narrow || prefCollapsed;
  const canProducts = meta.user.role === "admin" || meta.user.role === "warehouse";
  const leadsOn = meta.leads_enabled && meta.nav.includes("leads");
  const routes = meta.nav.filter((k) => k !== "leads" || leadsOn);

  const saved = useQuery({ queryKey: ["saved-filters"], queryFn: () => api.get<SavedFilter[]>("/saved-filters"), staleTime: 60_000 });

  const setOffice = useMutation({
    mutationFn: (office_id: number | null) => api.put("/me/office", { office_id }),
    onSuccess: () => qc.invalidateQueries(),
  });
  const toggleSidebar = useMutation({
    mutationFn: (v: boolean) => api.put("/me/prefs/sidebar.collapsed", { value: v || null }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["meta"] }),
  });

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1279px)");
    const h = () => setNarrow(mq.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  const quick: QuickAction[] = [
    { key: "order", label: "Нове замовлення", icon: ReceiptText, kbd: "N", onClick: () => nav("/orders/new") },
    ...(leadsOn ? [{ key: "lead", label: "Новий лід", icon: PhoneIncoming, kbd: "L", onClick: () => nav("/leads/new") }] : []),
    ...(canProducts ? [{ key: "product", label: "Товар", icon: PackagePlus, kbd: "P", onClick: () => nav("/products?new=1") }] : []),
    ...(meta.nav.includes("customers") ? [{ key: "customer", label: "Покупець", icon: UserPlus, kbd: "C", onClick: () => nav("/customers?new=1") }] : []),
    { key: "ttn", label: "Знайти за ТТН", icon: ScanBarcode, kbd: "T", onClick: () => setPalette({ hint: "Номер ТТН…" }) },
  ];

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((p) => (p ? null : {})); return; }
      if (e.ctrlKey || e.metaKey || e.altKey || inField(e) || document.querySelector(".win-backdrop, .modal, .side-panel")) return;
      const a = quick.find((q) => q.kbd?.toLowerCase() === e.key.toLowerCase());
      if (a) { e.preventDefault(); a.onClick(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  useEffect(() => { document.title = meta.company; }, [meta.company]);
  useEffect(() => setDrawer(false), [loc.pathname]);

  const logout = async () => {
    await api.post("/auth/logout");
    qc.clear();
    window.location.href = `${ROOT}/`;
  };

  const officeName = meta.offices.find((o) => o.id === meta.office)?.name;
  const counterFor = (k: string) => {
    if (k === "leads" && counters.leads_new) return <span className="count hot" title={`${counters.leads_new} нових лідів`}>{counters.leads_new}</span>;
    if (k === "orders" && counters.orders_unsorted) return <span className="count hot" title={`${counters.orders_unsorted} несортованих`}>{counters.orders_unsorted}</span>;
    if (k === "products") return <span className="count">{meta.products.length}</span>;
    return null;
  };
  const savedItems = (saved.data ?? []).filter((f) => f.section === "orders" || f.section === "leads");

  return (
    <div className={`app${collapsed ? " collapsed" : ""}`}>
      <aside className={`sb${drawer ? " open" : ""}`} aria-label="Меню">
        <div className="sb-top">
          <NavLink to="/" className="sb-logo" aria-label="mdmy — на головну"><span className="sb-mark">m</span><span className="sb-word">mdmy</span></NavLink>
          <span className={`live-dot${live ? " on" : ""}`} title={live ? "Оновлення в реальному часі" : "Оновлення кожні 30 с"} />
        </div>
        {meta.offices.length > 0 && (
          <MenuButton align="left" className="sb-office" button={({ open, toggle }) => (
            <button className="sb-office-btn" aria-haspopup="menu" aria-expanded={open} onClick={toggle} title={`Відділ: ${officeName ?? "усі"}`}>
              <Building2 size={15} /><span className="sb-txt ell">Відділ: {officeName ?? "усі"}</span><ChevronDown size={14} className="sb-txt" />
            </button>
          )}>
            {(close) => (<>
              <button className="pop-item" role="menuitemradio" aria-checked={meta.office == null} onClick={() => { setOffice.mutate(null); close(); }}>
                <span style={{ flex: 1 }}>Усі відділи</span>{meta.office == null && <Check size={15} />}
              </button>
              {meta.offices.filter((o) => meta.user.role === "admin" || !meta.user.offices?.length || meta.user.offices.includes(o.id)).map((o) => (
                <button key={o.id} className="pop-item" role="menuitemradio" aria-checked={meta.office === o.id} onClick={() => { setOffice.mutate(o.id); close(); }}>
                  <span style={{ flex: 1 }} className="ell">{o.name}</span>{meta.office === o.id && <Check size={15} />}
                </button>
              ))}
            </>)}
          </MenuButton>
        )}
        <nav className="sb-nav">
          {GROUPS.map(([title, keys]) => {
            const items = keys.filter((k) => routes.includes(k) && NAV[k]);
            if (!items.length) return null;
            return (
              <div className="sb-group" key={title}>
                <div className="sb-title">{title}</div>
                {items.map((k) => {
                  const n = NAV[k];
                  return (
                    <NavLink key={k} to={n.to} title={collapsed ? n.label : undefined} className={({ isActive }) => `sb-item${isActive ? " on" : ""}`}
                      state={k === "settings" && !loc.pathname.startsWith("/settings") ? { bg: loc } : undefined}>
                      <n.icon size={17} strokeWidth={1.8} /><span className="sb-txt ell">{n.label}</span>{counterFor(k)}
                    </NavLink>
                  );
                })}
              </div>
            );
          })}
          {savedItems.length > 0 && (
            <div className="sb-group">
              <div className="sb-title">Збережені фільтри</div>
              {savedItems.map((f) => (
                <NavLink key={f.id} to={`/${f.section}?${f.query}`} title={f.name}
                  className={() => `sb-item sb-saved${loc.pathname === `/${f.section}` && loc.search === `?${f.query}` ? " on" : ""}`}>
                  <span className="sb-dot" style={{ background: f.color }} /><span className="sb-txt ell">{f.name}</span>
                  <span className="count">{counters.saved?.[String(f.id)] ?? ""}</span>
                </NavLink>
              ))}
            </div>
          )}
        </nav>
        <div className="sb-foot">
          <MenuButton align="left" className="sb-me-wrap" button={({ open, toggle }) => (
            <button className="sb-me" aria-haspopup="menu" aria-expanded={open} onClick={toggle} title={meta.user.name}>
              <span className="av">{initials(meta.user.name)}</span>
              <span className="sb-txt sb-me-txt"><b className="ell">{meta.user.name}</b><small className="ell">{meta.user.role_name}</small></span>
            </button>
          )}>
            {(close) => (<>
              <button className="pop-item" onClick={() => { nav("/profile"); close(); }}><UserRound size={16} />Мій профіль</button>
              {!narrow && (
                <button className="pop-item" onClick={() => { toggleSidebar.mutate(!prefCollapsed); close(); }}>
                  {prefCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}{prefCollapsed ? "Розгорнути меню" : "Згорнути меню"}
                </button>
              )}
              <a className="pop-item" href={`${ROOT}/classic/orders`}><ExternalLink size={16} />Класичний інтерфейс</a>
              <button className="pop-item" onClick={logout}><LogOut size={16} />Вийти</button>
            </>)}
          </MenuButton>
        </div>
      </aside>
      {drawer && <div className="sb-backdrop" onClick={() => setDrawer(false)} />}

      <div className="app-main">
        <header className="topbar">
          <IconButton className="burger-btn" icon={Menu} label="Меню" quiet onClick={() => setDrawer(true)} />
          <button className="top-search" onClick={() => setPalette({})}>
            <Search size={16} /><span className="ell">Шукати замовлення, телефон, ТТН або товар…</span><kbd>Ctrl K</kbd>
          </button>
          <div className="top-acts">
            <TopComments />
            <TopBell due={counters.reminders_due} />
          </div>
        </header>
        <main className="work" id="main">
          <ErrorBoundary area="page"><Outlet /></ErrorBoundary>
        </main>
      </div>
      <Fab onClick={() => nav("/orders/new")} actions={quick} />
      {palette && <CommandPalette onClose={() => setPalette(null)} placeholder={palette.hint} />}
    </div>
  );
}

function useNotifications(enabled: boolean) {
  return useQuery({ queryKey: ["notifications"], queryFn: () => api.get<Notifications>("/notifications"), enabled, staleTime: 15_000 });
}

function TopBell({ due }: { due: number }) {
  const nav = useNavigate();
  const [on, setOn] = useState(false);
  const q = useNotifications(on);
  return (
    <MenuButton className="top-pop" button={({ open, toggle }) => (
      <IconButton icon={Bell} label={due ? `Нагадування: ${due}` : "Сповіщення"} count={due} aria-expanded={open} onClick={() => { setOn(true); toggle(); }} />
    )}>
      {(close) => (
        <div className="note-list">
          <div className="note-head">Нагадування</div>
          {q.isLoading && <div className="note-empty">Завантаження…</div>}
          {q.data && !q.data.reminders?.length && <div className="note-empty">Нагадувань на зараз немає</div>}
          {q.data?.reminders?.map((r) => (
            <button key={r.order_id} className="pop-item note" onClick={() => { nav(`/orders/${r.order_id}`); close(); }}>
              <AlarmClock size={16} className={r.due ? "due" : ""} />
              <span className="note-txt"><b className="ell">№{r.order_id} · {r.customer || "без імені"}</b><small>{r.due ? "час настав" : "незабаром"} · {dateTime(r.at)}</small></span>
            </button>
          ))}
        </div>
      )}
    </MenuButton>
  );
}

function TopComments() {
  const nav = useNavigate();
  const [on, setOn] = useState(false);
  const q = useNotifications(on);
  return (
    <MenuButton className="top-pop" button={({ open, toggle }) => (
      <IconButton icon={MessageSquare} label="Коментарі колег" aria-expanded={open} onClick={() => { setOn(true); toggle(); }} />
    )}>
      {(close) => (
        <div className="note-list">
          <div className="note-head">Коментарі колег · 7 днів</div>
          {q.isLoading && <div className="note-empty">Завантаження…</div>}
          {q.data && !q.data.comments?.length && <div className="note-empty">Нових коментарів немає</div>}
          {q.data?.comments?.map((c) => (
            <button key={c.id} className="pop-item note" onClick={() => { nav(`/orders/${c.order_id}`); close(); }}>
              <MessageSquare size={16} />
              <span className="note-txt"><b className="ell">{c.user} · №{c.order_id}</b><span className="note-body">{c.text}</span><small>{dateTime(c.at)}</small></span>
            </button>
          ))}
        </div>
      )}
    </MenuButton>
  );
}
