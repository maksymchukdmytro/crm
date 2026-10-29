import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Bell, Building2, CreditCard, ExternalLink, Globe, Hand, MessageCircle, Package, Phone, Plus, Printer, Receipt, RefreshCw, Send, Sparkles, Stamp, Tag, Trash2, Truck, User, UserRound } from "lucide-react";
import { api, ApiError, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { date, dt, money, num, phone as fmtPhone } from "../lib/format";
import type { Order, OrderItem, Product, Variant } from "../lib/types";
import { Badge, deliveryKind, Modal, NpAutocomplete, PayCheck, Pill, Spinner } from "../components/ui";
import { flag, PayIcon } from "../components/payicons";
import TtnDialog from "./TtnDialog";

type Form = {
  customer_name: string; phone: string; email: string; comment: string; status_id: number; manager_id: number | "";
  payment_type: string; payment_method_id: number | ""; source_id: number | ""; office_id: number | ""; np_account_id: number | ""; reason_id: number | "";
  legal_entity_id: number | "";
  mark_id: number | ""; remind_at: string; country: string; extra1: string; extra2: string; extra3: string; extra4: string;
  prepayment: string; discount: string; delivery_method: string; delivery_cost: string;
  city_name: string; city_ref: string; warehouse_name: string; warehouse_ref: string; address: string; postcode: string;
  ttn: string; site: string; utm_source: string; utm_medium: string; utm_campaign: string; utm_content: string; utm_term: string;
  items: OrderItem[];
};

const UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"] as const;
const EXTRA = ["extra1", "extra2", "extra3", "extra4"] as const;
let keySeq = 0;
const k = () => `i${++keySeq}`;

function toForm(o: Partial<Order> | undefined, defaultStatus: number): Form {
  const s = (v: unknown) => (v === null || v === undefined ? "" : String(v));
  const m = (v: number | undefined) => (v ? String(v) : "");
  return {
    customer_name: s(o?.customer_name), phone: fmtPhone(o?.phone ?? ""), email: s(o?.email), comment: s(o?.comment),
    legal_entity_id: o?.legal_entity_id ?? "",
    status_id: o?.status_id ?? defaultStatus, manager_id: o?.manager_id ?? "",
    payment_type: o?.payment_type || "cod", payment_method_id: o?.payment_method_id ?? "", source_id: o?.source_id ?? "",
    office_id: o?.office_id ?? "", np_account_id: o?.np_account_id ?? "", reason_id: o?.reason_id ?? "", mark_id: o?.mark_id ?? "", remind_at: toLocalInput(o?.remind_at),
    country: o?.country || "UA", extra1: s(o?.extra1), extra2: s(o?.extra2), extra3: s(o?.extra3), extra4: s(o?.extra4),
    prepayment: m(o?.prepayment), discount: m(o?.discount),
    delivery_method: o?.delivery_method || "novaposhta", delivery_cost: m(o?.delivery_cost),
    city_name: s(o?.city_name), city_ref: s(o?.city_ref), warehouse_name: s(o?.warehouse_name), warehouse_ref: s(o?.warehouse_ref),
    address: s(o?.address), postcode: s(o?.postcode), ttn: s(o?.ttn), site: s(o?.site),
    utm_source: s(o?.utm_source), utm_medium: s(o?.utm_medium), utm_campaign: s(o?.utm_campaign),
    utm_content: s(o?.utm_content), utm_term: s(o?.utm_term),
    items: (o?.items ?? []).map((i) => ({ ...i, price: String(i.price), key: k() })),
  };
}

// datetime-local працює в місцевому часі без поясу; сервер зберігає UTC
function toLocalInput(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function payload(f: Form, version?: string) {
  const { items, manager_id, payment_method_id, source_id, office_id, np_account_id, reason_id, mark_id, remind_at, legal_entity_id, ...rest } = f;
  return {
    ...rest, version, manager_id: manager_id || null, legal_entity_id: legal_entity_id || null,
    payment_method_id: payment_method_id || null, source_id: source_id || null, office_id: office_id || null,
    np_account_id: np_account_id || null,
    reason_id: reason_id || null, mark_id: mark_id || null, remind_at: remind_at ? new Date(remind_at).toISOString() : "",
    items: items.filter((i) => i.name.trim()).map((i) => ({ product_id: i.product_id, variant_id: i.variant_id ?? null, name: i.name, qty: i.qty, price: i.price, upsell: i.upsell, upsell_for: i.upsell ? i.upsell_for ?? null : null })),
  };
}

export default function OrderModal({ id, onClose, onOpen }: { id: string; onClose: () => void; onOpen: (id: number) => void }) {
  const dirtyRef = useRef(false);
  const close = useCallback(() => {
    if (dirtyRef.current && !window.confirm("Є незбережені зміни. Закрити без збереження?")) return;
    onClose();
  }, [onClose]);
  return (
    <Modal onClose={close} wide>
      <OrderCard key={id} id={id} onOpen={onOpen} dirtyRef={dirtyRef} />
    </Modal>
  );
}

function OrderCard({ id, onOpen, dirtyRef }: { id: string; onOpen: (id: number) => void; dirtyRef: React.MutableRefObject<boolean> }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const isNew = id === "new";
  const oid = isNew ? 0 : Number(id);
  const fromId = isNew ? Number(sp.get("from") || 0) : 0;
  const newStatus = meta.statuses.find((s) => s.code === "new")?.id ?? meta.statuses[0]?.id;

  const { data: order, error, isLoading } = useQuery({
    queryKey: ["order", oid],
    queryFn: () => api.get<Order>(`/orders/${oid}`),
    enabled: !isNew,
  });
  const { data: source } = useQuery({ queryKey: ["order", fromId], queryFn: () => api.get<Order>(`/orders/${fromId}`), enabled: !!fromId });

  const [form, setForm] = useState<Form>(() => toForm(undefined, newStatus));
  const [baseline, setBaseline] = useState("");
  const [loadedVersion, setLoadedVersion] = useState<string>("");
  const [ttnOpen, setTtnOpen] = useState(false);
  const wantTtn = useRef(false);
  // замовлення щойно створили кнопкою «Створити ТТН» — відкриваємо вікно ТТН одразу
  useEffect(() => {
    if (!order) return;
    let pending = "";
    try { pending = sessionStorage.getItem("crm-open-ttn") || ""; } catch { /* */ }
    if (pending === String(order.id)) {
      try { sessionStorage.removeItem("crm-open-ttn"); } catch { /* */ }
      if (order.delivery_method === "novaposhta") setTtnOpen(true); else action.mutate({ path: "/ttn" });
    }
  }, [order?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // заповнити форму даними замовлення (і оновлювати, якщо його змінили інші, а ми нічого не редагували)
  useEffect(() => {
    if (isNew) {
      if (source) {
        const f = toForm({ country: source.country, office_id: source.office_id, source_id: source.source_id, legal_entity_id: source.legal_entity_id, customer_name: source.customer_name, phone: source.phone, email: source.email,
          delivery_method: source.delivery_method, city_name: source.city_name, city_ref: source.city_ref,
          warehouse_name: source.warehouse_name, warehouse_ref: source.warehouse_ref, address: source.address,
          postcode: source.postcode }, newStatus);
        setForm(f); setBaseline(JSON.stringify(f));
      } else if (!fromId) { const f = toForm(undefined, newStatus); setBaseline(JSON.stringify(f)); }
      return;
    }
    if (!order) return;
    if (order.version === loadedVersion) return;
    const f = toForm(order, newStatus);
    if (!dirtyRef.current || !loadedVersion) { setForm(f); setBaseline(JSON.stringify(f)); setLoadedVersion(order.version); }
    else toast("Замовлення змінив інший користувач. Збережіть або закрийте картку, щоб побачити зміни.", "warn");
  }, [order, source]); // eslint-disable-line react-hooks/exhaustive-deps

  const dirty = baseline !== "" && JSON.stringify(form) !== baseline;
  dirtyRef.current = dirty;
  const set = (patch: Partial<Form>) => setForm((f) => ({ ...f, ...patch }));

  // ---------------- підсумки
  const subtotal = form.items.reduce((s, i) => s + num(i.price) * (i.qty || 0), 0);
  const total = Math.max(subtotal - num(form.discount), 0);
  const cod = form.payment_type === "prepaid" ? 0 : Math.max(total - num(form.prepayment), 0);

  // ---------------- збереження
  const save = useMutation({
    mutationFn: async (): Promise<Order> => {
      if (isNew) return api.post<Order>("/orders", payload(form));
      return api.patch<Order>(`/orders/${oid}`, payload(form, order?.version));
    },
    onSuccess: (o) => {
      qc.setQueryData(["order", o.id], o);
      qc.invalidateQueries({ queryKey: ["orders"] });
      const f = toForm(o, newStatus);
      setForm(f); setBaseline(JSON.stringify(f)); setLoadedVersion(o.version);
      dirtyRef.current = false;
      toast(isNew ? `Замовлення №${o.id} створено` : "Збережено");
      if (isNew) {
        if (wantTtn.current) { try { sessionStorage.setItem("crm-open-ttn", String(o.id)); } catch { /* */ } }
        onOpen(o.id);
      }
    },
    onError: (e) => {
      toast(errText(e), "error");
      if (e instanceof ApiError && e.status === 409) qc.invalidateQueries({ queryKey: ["order", oid] });
    },
  });

  const action = useMutation({
    mutationFn: async ({ path, method = "post", body }: { path: string; method?: "post" | "del"; body?: Record<string, unknown> }) => {
      if (dirty && !isNew) await save.mutateAsync();
      return method === "del" ? api.del<Order>(`/orders/${oid}${path}`) : api.post<Order>(`/orders/${oid}${path}`, body);
    },
    onSuccess: (o, vars) => {
      qc.setQueryData(["order", o.id], o);
      qc.invalidateQueries({ queryKey: ["orders"] });
      const f = toForm(o, newStatus);
      setForm(f); setBaseline(JSON.stringify(f)); setLoadedVersion(o.version);
      const msg: Record<string, string> = { "/ttn": `ТТН ${o.ttn} створено`, "/track": "Статус доставки оновлено", "/take": "Замовлення ваше",
        "/comments": "Коментар додано", "/sms": "Повідомлення поставлено в чергу", "/payments": "Передоплату додано", "/receipts": "Чек створено",
        "/fiscalize": "Замовлення фіскалізовано — чек продажу створено" };
      toast(vars.method === "del" ? "ТТН видалено" : msg[vars.path] ?? "Готово");
    },
    onError: (e) => toast(errText(e), "error"),
  });

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (!save.isPending) save.mutate(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [save]);

  if (!isNew && isLoading) return <div className="empty big"><Spinner /></div>;
  if (!isNew && error) return <div className="empty big"><h1>Не вдалося відкрити</h1><p>{errText(error)}</p></div>;

  const status = meta.statuses.find((s) => s.id === form.status_id);
  const carrier = meta.carriers[form.delivery_method];
  const dm = form.delivery_method;
  const canTake = !isNew && order && meta.user.role !== "warehouse" && order.manager_id !== meta.user.id && (!order.manager_id || meta.user.role === "admin");

  const reasons = meta.reasons.filter((r) => r.status_ids.includes(form.status_id));
  const method = meta.payment_methods.find((m) => m.id === form.payment_method_id);
  const managerName = order?.manager?.name ?? (isNew && meta.user.role === "manager" ? "ви" : "");
  const units = form.items.reduce((n, i) => n + (i.qty || 0), 0);
  const srcOffice = meta.order_sources.find((x) => x.id === form.source_id)?.office_id;
  const officeName = meta.offices.find((o) => o.id === (srcOffice ?? form.office_id))?.name ?? "";

  return (
    <div className="order-card">
      {/* ============ Шапка: номер, статус, менеджер, дії ============ */}
      <div className="oc-head">
        <div className="oc-title">
          <h1>{isNew ? "Нове замовлення" : `Замовлення № ${oid}`}</h1>
          {order && <span className="meta">від {dt(order.created_at)}</span>}
          {order?.shop_id && <span className="badge info" title={order.external_status ? `Статус на маркетплейсі: ${order.external_status}` : undefined}>{meta.shops[String(order.shop_id)] ?? "Маркетплейс"} №{order.external_id}</span>}
          {order?.duplicate_of_id && <a className="badge warn" onClick={() => onOpen(order.duplicate_of_id!)}>дубль №{order.duplicate_of_id}</a>}
          {order && (order.stock_shipped ? <Badge kind="ok">списано зі складу</Badge> : order.stock_reserved ? <Badge kind="info">зарезервовано</Badge> : null)}
        </div>
        <div className="oc-controls">
          <label className="ctl"><span>Статус</span>
            <select className="status-sel" style={{ ["--c" as string]: status?.color ?? "#8f8e8a" }} value={form.status_id}
              onChange={(e) => { const sid = Number(e.target.value); set({ status_id: sid, reason_id: meta.reasons.some((r) => r.id === form.reason_id && r.status_ids.includes(sid)) ? form.reason_id : "" }); }}>
              {meta.statuses.filter((x) => x.active || x.id === form.status_id).map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>
          </label>
          {reasons.length > 0 && <label className="ctl"><span>Причина</span>
            <select value={form.reason_id} onChange={(e) => set({ reason_id: e.target.value ? Number(e.target.value) : "" })}>
              <option value="">не вказано</option>
              {reasons.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select></label>}
          {meta.legal_entities.length > 0 && <label className="ctl" title="Від чийого імені продаж: за юрособою обирається каса Checkbox і ключ Нової Пошти"><span><Building2 size={13} /> Юрособа</span>
            <select value={form.legal_entity_id} onChange={(e) => set({ legal_entity_id: e.target.value ? Number(e.target.value) : "" })}>
              <option value="">{meta.legal_entities.find((x) => x.is_default)?.name ?? "за замовчуванням"} (за замовч.)</option>
              {meta.legal_entities.map((x) => <option key={x.id} value={x.id}>{x.name}{x.has_cashier ? "" : " · без каси"}</option>)}
            </select></label>}
          <label className="ctl"><span>Менеджер</span>
            {meta.user.role === "admin" ? (
              <select value={form.manager_id} onChange={(e) => set({ manager_id: e.target.value ? Number(e.target.value) : "" })}>
                <option value="">не призначений</option>
                {meta.managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            ) : <b className={managerName ? "" : "muted"}>{managerName || "не призначений"}</b>}
          </label>
          {order && <div className="oc-actions">
            {order.checkbox_ready && !(order.receipts ?? []).some((r) => r.kind === "sell" && r.status === "done") &&
              <button type="button" className="btn sm accent" disabled={action.isPending} title="Чек продажу на суму замовлення через касу юрособи"
                onClick={() => action.mutate({ path: "/fiscalize" })}><Stamp size={14} /> Фіскалізувати</button>}
            {order.checkbox_ready && (order.receipts ?? []).some((r) => r.kind === "sell" && r.status === "done") &&
              <span className="badge ok" title="Чек продажу вже створено"><Receipt size={12} /> фіскалізовано</span>}
            {canTake && <button type="button" className="btn sm" onClick={() => action.mutate({ path: "/take" })}><Hand size={14} /> Взяти собі</button>}
            <button type="button" className="btn sm" onClick={() => navigate(`/orders/new?from=${oid}`)} title="Нове замовлення цьому клієнту"><Plus size={14} /> Ще замовлення</button>
            <a className="btn sm icon" href={`${ROOT}/classic/orders/${oid}/print`} target="_blank" rel="noreferrer" title="Друк"><Printer size={15} /></a>
          </div>}
        </div>
      </div>

      {order?.customer?.blacklisted && (
        <div className="oc-alert bad"><Ban size={16} /><span><b>Покупець у чорному списку.</b> {order.customer.blacklist_reason || "Причину не вказано"}</span>
          <a href={`${ROOT}/customers/${order.customer.id}`} onClick={(e) => { e.preventDefault(); navigate(`/customers/${order.customer!.id}`); }}>Картка покупця</a></div>
      )}
      <form id="oc-form" className="oc" onSubmit={(e) => { e.preventDefault(); save.mutate(); }} autoComplete="off">
        {/* ============ Ліва колонка: клієнт, доставка, оплата, джерело ============ */}
        <div className="oc-side">
          <section className="ocs">
            <h3 className="ocs-h"><User size={15} /> Клієнт</h3>
            <div className="fl"><span>Країна</span>
              <select value={form.country} onChange={(e) => set({ country: e.target.value })}>
                {Object.entries(meta.countries).map(([c, n]) => <option key={c} value={c}>{flag(c)} {n}</option>)}
              </select></div>
            <div className="fl"><span>Телефон</span>
              <div className="fl-in"><input value={form.phone} onChange={(e) => set({ phone: e.target.value })} placeholder="+380…" inputMode="tel" required autoFocus={isNew && !fromId} />
                {order?.phone && <span className="acts"><a href={`tel:+${order.phone}`} title="Подзвонити"><Phone size={14} /></a><a href={`viber://chat?number=%2B${order.phone}`} title="Viber"><MessageCircle size={14} /></a></span>}
              </div></div>
            <NameField value={form.customer_name} onChange={(v) => set({ customer_name: v })} saved={order?.customer_name ?? ""} />
            <div className="fl"><span>Email</span><input type="email" value={form.email} onChange={(e) => set({ email: e.target.value })} placeholder="—" /></div>
            {order?.customer && (
              <a className="cust-line" href={`${ROOT}/customers/${order.customer.id}`} onClick={(e) => { e.preventDefault(); navigate(`/customers/${order.customer!.id}`); }}>
                <UserRound size={14} />
                {order.customer.group && <span className="pill" style={{ ["--c" as string]: order.customer.group_color || "#64748b" }}>{order.customer.group}</span>}
                <span>{order.customer.orders} {plural(order.customer.orders, "замовлення", "замовлення", "замовлень")}</span>
                {order.customer.buyout_rate != null && <span className={order.customer.buyout_rate < 50 ? "lowstock" : ""}>викуп {order.customer.buyout_rate}%</span>}
                {order.customer.refused > 0 && <span className="lowstock">відмов {order.customer.refused}</span>}
              </a>
            )}
          </section>

          <section className="ocs">
            <h3 className="ocs-h"><Truck size={15} /> Доставка</h3>
            <div className="fl"><span>Служба</span>
              <select value={dm} onChange={(e) => set({ delivery_method: e.target.value, city_ref: "", warehouse_ref: "", warehouse_name: "" })}>
                {Object.entries(meta.delivery_methods).map(([k2, n]) => <option key={k2} value={k2}>{n}{meta.carriers[k2]?.beta ? " (бета)" : ""}</option>)}
              </select></div>
            {dm === "novaposhta" && <>
              <div className="fl"><span>Місто</span>
                <NpAutocomplete kind="cities" value={form.city_name} refValue={form.city_ref} placeholder="Почніть вводити"
                  onType={(t) => set({ city_name: t, city_ref: "" })} onPick={(o) => set({ city_name: o.name, city_ref: o.ref, warehouse_name: "", warehouse_ref: "" })} /></div>
              <div className="fl"><span>Відділення</span>
                <NpAutocomplete kind="warehouses" cityRef={form.city_ref} value={form.warehouse_name} refValue={form.warehouse_ref} placeholder="Номер або адреса"
                  onType={(t) => set({ warehouse_name: t, warehouse_ref: "" })} onPick={(o) => set({ warehouse_name: o.name, warehouse_ref: o.ref })} /></div>
              {meta.np_accounts.length > 1 && <div className="fl"><span>Відправник</span>
                <select value={form.np_account_id} onChange={(e) => set({ np_account_id: e.target.value ? Number(e.target.value) : "" })} disabled={!!order?.ttn}>
                  <option value="">за відділом / основний</option>
                  {meta.np_accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select></div>}
              {!meta.carriers.novaposhta?.configured && <p className="hint fl-note">Підказки міст з'являться після введення API-ключа НП у налаштуваннях.</p>}
            </>}
            {dm === "ukrposhta" && <>
              <div className="fl"><span>Місто</span><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="—" /></div>
              <div className="fl"><span>Індекс</span><input value={form.postcode} onChange={(e) => set({ postcode: e.target.value })} placeholder="5 цифр" maxLength={5} inputMode="numeric" /></div>
            </>}
            {dm === "meest" && <>
              <div className="fl"><span>Місто</span><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="—" /></div>
              <div className="fl"><span>Відділення</span><input value={form.warehouse_name} onChange={(e) => set({ warehouse_name: e.target.value })} placeholder="Назва або номер" /></div>
              <div className="fl"><span>ID відділення</span><input className="mono" value={form.warehouse_ref} onChange={(e) => set({ warehouse_ref: e.target.value })} placeholder="для ТТН" /></div>
            </>}
            {dm === "courier" && <>
              <div className="fl"><span>Місто</span><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="—" /></div>
              <div className="fl"><span>Адреса</span><input value={form.address} onChange={(e) => set({ address: e.target.value })} placeholder="Вулиця, будинок, квартира" /></div>
            </>}
            {dm === "pickup" && <p className="hint fl-note">Клієнт забирає сам.</p>}
            {dm !== "pickup" && <>
              <div className="fl"><span>ТТН</span>
                <div className="fl-in"><input className="mono" value={form.ttn} onChange={(e) => set({ ttn: e.target.value })} readOnly={!!order?.carrier_ref} placeholder="створіть або вставте" />
                  {order?.ttn && <span className="acts">
                    {carrier && <button type="button" title="Оновити статус доставки" onClick={() => action.mutate({ path: "/track" })}><RefreshCw size={14} /></button>}
                    {carrier && <a href={`${ROOT}/classic/orders/${oid}/label`} target="_blank" rel="noreferrer" title="Наклейка PDF"><Printer size={14} /></a>}
                    {order.carrier_ref && <button type="button" title="Видалити ТТН" onClick={() => { if (window.confirm(`Видалити ТТН ${order.ttn} у перевізника?`)) action.mutate({ path: "/ttn", method: "del" }); }}><Trash2 size={14} /></button>}
                  </span>}
                </div></div>
              {order?.pay_check && <div className={`pc-line pc-${order.pay_check.state}`}><PayCheck check={order.pay_check} text /></div>}
              <div className="fl"><span>Вартість</span><div className="fl-in"><input value={form.delivery_cost} onChange={(e) => set({ delivery_cost: e.target.value })} placeholder="0" inputMode="decimal" /><span className="unit">грн</span></div></div>
              {order?.ttn && order.delivery_status && (
                <div className="ship-card"><Badge kind={deliveryKind(order.delivery_state)}>{meta.delivery_states[order.delivery_state] ?? order.delivery_state}</Badge>
                  <span className="hint">{order.delivery_status}{order.delivery_checked_at && ` · ${dt(order.delivery_checked_at, true)}`}</span></div>
              )}
              {!order?.ttn && carrier && (
                <div className="ship-card">
                  {carrier.configured ? <>
                    <button type="button" className="btn dark block" disabled={action.isPending || save.isPending}
                      title={isNew ? "Замовлення збережеться автоматично" : undefined}
                      onClick={async () => {
                        if (isNew) { wantTtn.current = true; save.mutate(); return; }
                        if (dm === "novaposhta") { if (dirty) await save.mutateAsync(); setTtnOpen(true); } else action.mutate({ path: "/ttn" });
                      }}>
                      <Send size={14} /> Створити ТТН {carrier.name}</button>
                    <span className="hint">Накладений платіж: {money(cod)} грн{carrier.beta ? " · бета: перше відправлення зробіть тестовим" : ""}</span>
                  </> : <span className="hint">Щоб створювати ТТН, заповніть доступи в налаштуваннях доставки.</span>}
                </div>
              )}
            </>}
          </section>

          <section className="ocs">
            <h3 className="ocs-h"><CreditCard size={15} /> Оплата {method && <span className="muted">{method.name}</span>}</h3>
            <div className="pay-grid" role="radiogroup" aria-label="Вид оплати">
              {meta.payment_methods.map((m) => (
                <button type="button" key={m.id} role="radio" aria-checked={form.payment_method_id === m.id} title={m.name}
                  className={`pay-tile ${form.payment_method_id === m.id ? "on" : ""}`}
                  onClick={() => set({ payment_method_id: m.id, payment_type: m.kind })}>
                  <PayIcon icon={m.icon} size={26} /><span>{m.name}</span>
                </button>
              ))}
            </div>
            {method && <p className="hint pay-note">{method.kind === "prepaid" ? "Оплачено повністю — ТТН без післяплати" : method.kind === "partial" ? "Передоплата, решта — післяплатою" : "Уся сума — при отриманні"}</p>}
            {form.payment_type === "partial" && <div className="fl"><span>Передоплата</span><div className="fl-in"><input value={form.prepayment} onChange={(e) => set({ prepayment: e.target.value })} placeholder="0" inputMode="decimal" /><span className="unit">грн</span></div></div>}
          </section>

          {order?.checkbox_ready && (
            <section className="ocs">
              <h3 className="ocs-h"><Receipt size={15} /> ПРРО · Checkbox</h3>
              {(order.receipts ?? []).length === 0 ? <p className="hint fl-note">Чеків ще немає.</p> : (
                <div className="rc-list">{(order.receipts ?? []).map((r) => (
                  <div className={`rc ${r.status}`} key={r.id} title={r.error || undefined}>
                    <span>{r.kind_name}{r.test && <span className="badge">тест</span>}</span>
                    <b>{money(r.total)} ₴</b>
                    {r.url ? <a href={r.url} target="_blank" rel="noreferrer">чек <ExternalLink size={12} /></a> : <span className={r.status === "error" ? "lowstock" : "muted"}>{r.status === "error" ? "помилка" : r.fiscal_code || "в обробці"}</span>}
                  </div>
                ))}</div>
              )}
              <div className="rc-actions">
                {!(order.receipts ?? []).some((r) => r.kind === "sell" && r.status === "done") && <button type="button" className="btn sm" disabled={action.isPending} onClick={() => action.mutate({ path: "/receipts", body: { kind: "sell" } })}>Чек продажу</button>}
                <button type="button" className="btn sm" disabled={action.isPending} onClick={() => { if (window.confirm("Створити чек повернення?")) action.mutate({ path: "/receipts", body: { kind: "return" } }); }}>Чек повернення</button>
                {num(form.prepayment) > 0 && <button type="button" className="btn sm" disabled={action.isPending} onClick={() => action.mutate({ path: "/receipts", body: { kind: "prepay" } })}>Чек передоплати</button>}
              </div>
            </section>
          )}

          <section className="ocs">
            <h3 className="ocs-h"><Tag size={15} /> Джерело й додаткові поля</h3>
            <div className="fl"><span>Джерело</span>
              <select value={form.source_id} onChange={(e) => set({ source_id: e.target.value ? Number(e.target.value) : "" })}>
                <option value="">не вказано</option>
                {meta.order_sources.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
              </select></div>
            {meta.offices.length > 0 && <div className="fl"><span>Відділ</span><span className="val">{officeName || <span className="muted">визначається джерелом</span>}</span></div>}
            {EXTRA.map((f, i) => (
              <div className="fl" key={f}><span>{meta.extra_fields[i] || `Поле ${i + 1}`}</span>
                <div className="fl-in"><input value={form[f]} onChange={(e) => set({ [f]: e.target.value } as Partial<Form>)} placeholder="—" />
                  {/^https?:\/\//.test(form[f]) && <span className="acts"><a href={form[f]} target="_blank" rel="noreferrer" title="Перейти за посиланням"><ExternalLink size={14} /></a></span>}
                </div></div>
            ))}
          </section>

          <details className="ocs" open={!!(form.site || UTM.some((u) => form[u]))}>
            <summary className="ocs-h"><Globe size={15} /> Сайт і UTM-мітки <span className="muted">{form.site || (form.utm_source ? `utm: ${form.utm_source}` : "")}</span></summary>
            <div className="fl"><span>Сайт</span><input value={form.site} onChange={(e) => set({ site: e.target.value })} placeholder="—" /></div>
            {UTM.map((u) => <div className="fl" key={u}><span className="mono">{u}</span><input value={form[u]} onChange={(e) => set({ [u]: e.target.value } as Partial<Form>)} placeholder="—" /></div>)}
            {order?.ip && <div className="fl"><span>IP</span><span className="val mono">{order.ip}</span></div>}
          </details>
        </div>

        {/* ============ Права колонка: товари з підсумком, коментар ============ */}
        <div className="oc-main">
          <section className="ocs">
            <h3 className="ocs-h"><Package size={15} /> Товари {units > 0 && <span className="muted">{units} шт</span>}</h3>
            <Goods items={form.items} products={meta.products} onChange={(items) => set({ items })} />
            <div className="oc-sum">
              <div><span>Товари</span><b>{money(subtotal)} ₴</b></div>
              <div className="disc"><span>Знижка</span><div className="fl-in"><input value={form.discount} onChange={(e) => set({ discount: e.target.value })} placeholder="0" inputMode="decimal" /><span className="unit">грн</span></div></div>
              {num(form.prepayment) > 0 && form.payment_type !== "cod" && <div><span>Передоплата</span><b>−{money(form.prepayment)} ₴</b></div>}
              <div className="total"><span>Разом</span><b>{money(total)} ₴</b></div>
              <div className="cod"><span>{form.payment_type === "prepaid" ? "Повністю оплачено" : "До сплати при отриманні"}</span><b>{money(cod)} ₴</b></div>
            </div>
          </section>
          <section className="ocs">
            <h3 className="ocs-h"><MessageCircle size={15} /> Позначка й коментар</h3>
            <div className="mark-row">
              <select value={form.mark_id} onChange={(e) => set({ mark_id: e.target.value ? Number(e.target.value) : "" })} aria-label="Позначка">
                <option value="">Без позначки</option>
                {meta.marks.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
              <label className={`remind ${form.remind_at ? "on" : ""}`} title="Нагадати про замовлення"><Bell size={15} />
                <input type="datetime-local" value={form.remind_at} onChange={(e) => set({ remind_at: e.target.value })} aria-label="Нагадати" />
                {form.remind_at && <button type="button" className="x" title="Прибрати нагадування" onClick={() => set({ remind_at: "" })}>×</button>}
              </label>
            </div>
            <textarea className="oc-note" rows={3} value={form.comment} onChange={(e) => set({ comment: e.target.value })} placeholder="Від клієнта з лендингу або для складу" />
          </section>
        </div>
      </form>

      {ttnOpen && order && <TtnDialog orderId={order.id} accountId={form.np_account_id} busy={action.isPending} onClose={() => setTtnOpen(false)}
        onCreate={(body) => action.mutate({ path: "/ttn", body }, { onSuccess: () => setTtnOpen(false) })} />}
      {order && <OrderTabs order={order} onAction={(path, body) => action.mutate({ path, body })} busy={action.isPending} onOpen={onOpen} />}

      <div className="oc-bar">
        <span className={`oc-dirty ${dirty ? "on" : ""}`}>{dirty ? "Є незбережені зміни · Ctrl+S" : isNew ? "" : "Усі зміни збережено"}</span>
        <button type="submit" form="oc-form" className="btn primary" disabled={save.isPending}>{save.isPending ? "Збереження…" : isNew ? "Створити замовлення" : "Зберегти"}</button>
      </div>
    </div>
  );
}

function plural(n: number, one: string, few: string, many: string) {
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
}

// ---------------------------------------------------------------- ПІБ одним рядком з розпізнаванням
function NameField({ value, onChange, saved }: { value: string; onChange: (v: string) => void; saved: string }) {
  const dv = useDebounced(value.trim(), 250);
  const { data } = useQuery({
    queryKey: ["name-split", dv], enabled: dv.length > 1 && dv !== saved,
    queryFn: () => api.get<{ last_name: string; first_name: string; middle_name: string; full: string }>(`/names/split${qs({ q: dv })}`),
    staleTime: Infinity,
  });
  const show = data && dv.length > 1 && dv !== saved;
  return (
    <>
      <div className="fl"><span>ПІБ</span><input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Прізвище Ім'я По батькові — у будь-якому порядку" /></div>
      {show && (
        <div className="name-parts" title="Як CRM розпізнала ПІБ. Порядок слів можна вводити будь-який">
          <span><small>Прізвище</small>{data.last_name || "—"}</span><span><small>Ім'я</small>{data.first_name || "—"}</span>
          <span><small>По батькові</small>{data.middle_name || "—"}</span>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------- товари в замовленні
function Goods({ items, products, onChange }: { items: OrderItem[]; products: Product[]; onChange: (i: OrderItem[]) => void }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    // товар із варіантами — окремий рядок на кожен варіант («Лампа — Чорний»)
    const rows: { p: Product; v?: Variant }[] = [];
    for (const p of products) {
      const vs = (p.variants ?? []).filter((v) => v.active);
      if (vs.length) {
        for (const v of vs) if (!t || `${p.name} ${v.name} ${p.sku} ${v.sku}`.toLowerCase().includes(t)) rows.push({ p, v });
      } else if (!t || p.name.toLowerCase().includes(t) || p.sku.toLowerCase().includes(t)) rows.push({ p });
      if (rows.length >= 40) break;
    }
    return rows;
  }, [q, products]);
  const byId = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);
  // основні товари замовлення — до них можна привʼязати допродаж
  const mains = items.filter((i) => !i.upsell && i.product_id);
  const inOrder = new Set(items.map((i) => i.product_id).filter(Boolean));
  // що запропонувати: товари-допродажі, привʼязані до товарів у замовленні (або до будь-якого замовлення)
  const offers = mains.length ? products.filter((p) => p.upsell && !inOrder.has(p.id) && (!p.upsell_for?.length || mains.some((m) => p.upsell_for!.includes(m.product_id!)))).slice(0, 6) : [];

  const add = (p?: Product, asUpsell = false, v?: Variant) => {
    if (p) {
      const ex = items.find((i) => i.product_id === p.id && (i.variant_id ?? null) === (v?.id ?? null));
      if (ex) onChange(items.map((i) => (i === ex ? { ...i, qty: i.qty + 1 } : i)));
      else {
        const upsell = asUpsell || (p.upsell && mains.length > 0);
        const main = upsell ? (mains.find((m) => p.upsell_for?.includes(m.product_id!)) ?? mains[0]) : undefined;
        const price = v?.price ?? p.sale_price ?? p.price;
        onChange([...items, { product_id: p.id, variant_id: v?.id ?? null, variant_name: v?.name ?? "", name: v ? `${p.name} (${v.name})` : p.name,
          price: String(price), qty: 1, upsell, upsell_for: main?.product_id ?? null, base_price: price, photo: p.photo, key: k() }]);
      }
    } else onChange([...items, { product_id: null, name: q.trim(), price: "", qty: 1, upsell: false, upsell_for: null, key: k() }]);
    setQ(""); setHl(0); setOpen(false);
  };
  const upd = (key: string | undefined, patch: Partial<OrderItem>) => onChange(items.map((i) => (i.key === key ? { ...i, ...patch } : i)));

  return (
    <>
      {items.length > 0 ? (
        <table className="t items">
          <thead><tr><th>Товар</th><th className="num">Кількість</th><th className="num">Ціна, ₴</th><th className="num">Сума</th><th /></tr></thead>
          <tbody>
            {items.map((i) => {
              const p = i.product_id ? byId[i.product_id] : undefined;
              const base = i.base_price ?? p?.price;
              const changed = base != null && num(i.price) !== Number(base);
              const others = items.filter((x) => x.key !== i.key && !x.upsell && x.product_id);
              return (
                <tr key={i.key} className={i.upsell ? "is-upsell" : ""}>
                  <td className="item-cell">
                    {(i.photo ?? p?.photo) ? <img className="item-ph" src={`${ROOT}${i.photo ?? p?.photo}`} alt="" /> : <span className="item-ph empty"><Package size={14} /></span>}
                    <div className="item-main">
                    <input className="name" value={i.name} onChange={(e) => upd(i.key, { name: e.target.value })} placeholder="Назва позиції" />
                    <div className="meta-line">
                      {p && (p.variants ?? []).some((x) => x.active) && (
                        <select className="mini-sel" value={i.variant_id ?? ""} title="Варіант"
                          onChange={(e) => { const nv = (p.variants ?? []).find((x) => x.id === Number(e.target.value)); upd(i.key, { variant_id: nv?.id ?? null, variant_name: nv?.name ?? "", name: nv ? `${p.name} (${nv.name})` : p.name, price: String(nv?.price ?? p.sale_price ?? p.price) }); }}>
                          <option value="">варіант…</option>
                          {(p.variants ?? []).filter((x) => x.active || x.id === i.variant_id).map((x) => <option key={x.id} value={x.id}>{x.name} · {x.available} шт</option>)}
                        </select>
                      )}
                      {p && <span>{p.sku && `${p.sku} · `}залишок {i.variant_id ? (p.variants ?? []).find((x) => x.id === i.variant_id)?.available ?? "—" : p.available}</span>}
                      <label className="mini-check"><input type="checkbox" checked={i.upsell} onChange={(e) => upd(i.key, { upsell: e.target.checked, upsell_for: e.target.checked ? others[0]?.product_id ?? null : null })} /> допродаж</label>
                      {i.upsell && others.length > 0 && (
                        <select className="mini-sel" value={i.upsell_for ?? ""} onChange={(e) => upd(i.key, { upsell_for: e.target.value ? Number(e.target.value) : null })}>
                          <option value="">до замовлення</option>
                          {others.map((o) => <option key={o.key} value={o.product_id!}>до «{o.name}»</option>)}
                        </select>
                      )}
                    </div>
                    </div>
                  </td>
                  <td className="qty num"><input type="number" min={1} value={i.qty} onChange={(e) => upd(i.key, { qty: Math.max(1, Number(e.target.value) || 1) })} /></td>
                  <td className="price num">
                    <input value={i.price} inputMode="decimal" onChange={(e) => upd(i.key, { price: e.target.value })} title="Ціну можна змінити лише для цього замовлення" />
                    {changed && <span className="was" title="Ціна в каталозі">{money(base!)}</span>}
                  </td>
                  <td className="num sum">{money(num(i.price) * i.qty)}</td>
                  <td><button type="button" className="x" title="Прибрати" onClick={() => onChange(items.filter((x) => x.key !== i.key))}>×</button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : null}
      <div className={`goods-add ac ${items.length ? "" : "first"}`}>
        <input value={q} placeholder="Додати товар: назва або артикул…" onChange={(e) => { setQ(e.target.value); setHl(0); setOpen(true); }}
          onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            const n = list.length + 1;
            if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % n); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + n) % n); }
            else if (e.key === "Enter") { e.preventDefault(); if (hl < list.length) add(list[hl].p, false, list[hl].v); else add(); }
            else if (e.key === "Escape") { e.preventDefault(); setOpen(false); }
          }} />
        {open && (
          <div className="ac-list on">
            {list.map(({ p, v }, i) => (
              <div key={`${p.id}-${v?.id ?? 0}`} className={`goods-opt ${i === hl ? "hl" : ""}`} onMouseDown={(e) => { e.preventDefault(); add(p, false, v); }}>
                {p.photo ? <img src={`${ROOT}${p.photo}`} alt="" /> : <span className="ph"><Package size={14} /></span>}
                <span className="nm">{p.name}{v && <b> · {v.name}</b>}{p.upsell && <span className="badge info">допродаж</span>}{p.discount_percent > 0 && <span className="badge warn">−{p.discount_percent}%</span>}</span>
                <small>{money(v?.price ?? p.sale_price ?? p.price)} ₴ · {(v ?? p).available} шт</small>
              </div>
            ))}
            <div className={hl === list.length ? "hl" : ""} onMouseDown={(e) => { e.preventDefault(); add(); }}>
              <span>{q.trim() ? `Довільна позиція «${q.trim()}»` : "Довільна позиція (без товару зі складу)"}</span><small>Enter</small>
            </div>
          </div>
        )}
      </div>
      {offers.length > 0 && (
        <div className="offers"><span className="offers-l"><Sparkles size={14} /> Запропонуйте допродаж</span>
          {offers.map((p) => <button type="button" key={p.id} className="offer" onClick={() => add(p, true)}><Plus size={13} /> {p.name} <b>{money(p.price)} ₴</b></button>)}
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------- вкладки під карткою
function OrderTabs({ order, onAction, busy, onOpen }: { order: Order; onAction: (path: string, body: Record<string, unknown>) => void; busy: boolean; onOpen: (id: number) => void }) {
  const meta = useMeta();
  const [tab, setTab] = useState(() => sessionStorage.getItem("crm-tab") || "comments");
  const [comment, setComment] = useState("");
  const [smsText, setSmsText] = useState("");
  const [channel, setChannel] = useState("sms");
  const [pay, setPay] = useState({ amount: "", method: "card", reference: "" });
  const statuses = Object.fromEntries(meta.statuses.map((s) => [s.id, s]));
  const choose = (t: string) => { setTab(t); try { sessionStorage.setItem("crm-tab", t); } catch { /* */ } };
  const tabs: [string, string, number][] = [
    ["comments", "Коментарі", order.comments.length], ["history", "Історія", 0], ["payments", "Оплати", order.payments.length],
    ["sms", "SMS / Viber", order.sms.length], ...(order.others.length ? [["others", "Інші замовлення клієнта", order.others.length] as [string, string, number]] : []),
  ];
  const cur = tabs.some((t) => t[0] === tab) ? tab : "comments";

  return (
    <div className="oc-tabs">
      <nav className="subnav">{tabs.map(([key, label, n]) => <a key={key} className={cur === key ? "on" : ""} onClick={() => choose(key)}>{label} {n > 0 && <span className="n">{n}</span>}</a>)}</nav>
      {cur === "comments" && (
        <div className="grid half">
          <form className="form" onSubmit={(e) => { e.preventDefault(); if (comment.trim()) { onAction("/comments", { text: comment }); setComment(""); } }}>
            <textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Коментар для колег — клієнт його не бачить" />
            <button className="btn sm" disabled={busy || !comment.trim()}>Додати коментар</button>
          </form>
          <div className="stack">
            {order.comments.length ? order.comments.map((c) => (
              <div className="comment" key={c.id}><div className="hint"><strong>{c.user}</strong> · {dt(c.created_at)}</div>{c.text}</div>
            )) : <p className="hint">Коментарів ще немає</p>}
          </div>
        </div>
      )}
      {cur === "history" && (
        <ul className="timeline">
          {order.history.map((h) => (
            <li key={h.id}><span className="who">{h.user} · {h.action}</span><span className="when">{dt(h.created_at)}</span>{h.details && <span className="what">{h.details}</span>}</li>
          ))}
        </ul>
      )}
      {cur === "payments" && (
        <div className="grid half">
          <div>{order.payments.length ? (
            <table className="t"><tbody>{order.payments.map((p) => (
              <tr key={p.id}><td>{p.kind_name}<span className="sub">{date(p.created_at)}{p.reference && ` · ${p.reference}`}</span></td>
                <td className="num">{money(p.amount)} ₴</td>
                <td><Badge kind={p.status === "received" ? "ok" : p.status === "cancelled" ? "bad" : p.status === "collected" ? "info" : "warn"}>{p.status_name}</Badge></td></tr>
            ))}</tbody></table>
          ) : <p className="hint">Оплат ще немає. Очікуваний накладений платіж з'явиться після відправки.</p>}</div>
          <form className="form" onSubmit={(e) => { e.preventDefault(); onAction("/payments", pay); setPay({ amount: "", method: "card", reference: "" }); }}>
            <div className="cols">
              <label><span className="lbl">Передоплата, грн</span><input value={pay.amount} onChange={(e) => setPay({ ...pay, amount: e.target.value })} inputMode="decimal" required /></label>
              <label><span className="lbl">Спосіб</span><select value={pay.method} onChange={(e) => setPay({ ...pay, method: e.target.value })}>
                <option value="card">Карта</option><option value="iban">Рахунок (IBAN)</option><option value="cash">Готівка</option><option value="other">Інше</option></select></label>
            </div>
            <label><span className="lbl">Примітка / № квитанції</span><input value={pay.reference} onChange={(e) => setPay({ ...pay, reference: e.target.value })} /></label>
            <button className="btn sm" disabled={busy}>Додати передоплату</button>
          </form>
        </div>
      )}
      {cur === "sms" && (
        <div className="grid half">
          {meta.sms_ready ? (
            <form className="form" onSubmit={(e) => { e.preventDefault(); if (smsText.trim()) { onAction("/sms", { text: smsText, channel }); setSmsText(""); } }}>
              <textarea rows={3} value={smsText} onChange={(e) => setSmsText(e.target.value)} placeholder="Текст. Можна {ttn}, {total}, {cod}, {first_name}…" />
              <div className="form-actions"><select style={{ width: "auto" }} value={channel} onChange={(e) => setChannel(e.target.value)}>
                <option value="sms">SMS</option><option value="viber">Viber</option><option value="hybrid">Viber → SMS</option></select>
                <button className="btn sm" disabled={busy || !smsText.trim()}><Send size={14} /> Відправити</button></div>
            </form>
          ) : <p className="hint">Підключіть TurboSMS у налаштуваннях.</p>}
          <div className="stack">
            {order.sms.length ? order.sms.map((m) => (
              <div key={m.id}><Badge kind={m.status === "sent" ? "ok" : m.status === "failed" ? "bad" : "warn"}>{({ sent: "відправлено", failed: "помилка", queued: "в черзі" } as Record<string, string>)[m.status]}</Badge>
                <small> {m.channel} · {dt(m.created_at)}</small><div>{m.text}</div>{m.error && <small className="lowstock">{m.error}</small>}</div>
            )) : <p className="hint">Повідомлень ще не було</p>}
          </div>
        </div>
      )}
      {cur === "others" && (
        <table className="t dense"><tbody>{order.others.map((o) => (
          <tr key={o.id} className="clickable" onClick={() => onOpen(o.id)}>
            <td><b>№{o.id}</b></td><td>{date(o.created_at)}</td><td className="ell">{o.items.map((i) => i.name).join(", ")}</td>
            <td className="num">{money(o.total)} ₴</td><td><Pill status={statuses[o.status_id]} /></td><td><ExternalLink size={14} className="muted" /></td>
          </tr>
        ))}</tbody></table>
      )}
    </div>
  );
}
