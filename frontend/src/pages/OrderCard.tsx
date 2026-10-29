import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CreditCard, ExternalLink, Globe, Tag, Hand, MessageCircle, Package, Phone, Plus, Printer, RefreshCw, Send, Sparkles, Trash2, Truck, User } from "lucide-react";
import { api, ApiError, ROOT } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { date, dt, money, num, phone as fmtPhone } from "../lib/format";
import type { Order, OrderItem, Product } from "../lib/types";
import { Badge, deliveryKind, Modal, NpAutocomplete, Pill, Spinner } from "../components/ui";
import { flag, PayIcon } from "../components/payicons";
import TtnDialog from "./TtnDialog";

type Form = {
  last_name: string; first_name: string; middle_name: string; phone: string; email: string; comment: string; status_id: number; manager_id: number | "";
  payment_type: string; payment_method_id: number | ""; source_id: number | ""; office_id: number | ""; np_account_id: number | ""; reason_id: number | "";
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
    last_name: s(o?.last_name), first_name: s(o?.first_name), middle_name: s(o?.middle_name), phone: fmtPhone(o?.phone ?? ""), email: s(o?.email), comment: s(o?.comment),
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
  const { items, manager_id, payment_method_id, source_id, office_id, np_account_id, reason_id, mark_id, remind_at, ...rest } = f;
  return {
    ...rest, version, manager_id: manager_id || null,
    payment_method_id: payment_method_id || null, source_id: source_id || null, office_id: office_id || null,
    np_account_id: np_account_id || null,
    reason_id: reason_id || null, mark_id: mark_id || null, remind_at: remind_at ? new Date(remind_at).toISOString() : "",
    items: items.filter((i) => i.name.trim()).map((i) => ({ product_id: i.product_id, name: i.name, qty: i.qty, price: i.price, upsell: i.upsell, upsell_for: i.upsell ? i.upsell_for ?? null : null })),
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

  // заповнити форму даними замовлення (і оновлювати, якщо його змінили інші, а ми нічого не редагували)
  useEffect(() => {
    if (isNew) {
      if (source) {
        const f = toForm({ country: source.country, office_id: source.office_id, last_name: source.last_name, first_name: source.first_name, middle_name: source.middle_name, phone: source.phone, email: source.email,
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
      if (isNew) onOpen(o.id);
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
        "/comments": "Коментар додано", "/sms": "Повідомлення поставлено в чергу", "/payments": "Передоплату додано" };
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

  return (
    <div className="order-card">
      {/* ============ Шапка: номер, статус, менеджер, дії ============ */}
      <div className="oc-head">
        <div className="oc-title">
          <h1>{isNew ? "Нове замовлення" : `Замовлення № ${oid}`}</h1>
          {order && <span className="meta">від {dt(order.created_at)}</span>}
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
          {meta.offices.length > 0 && <label className="ctl"><span>Відділ</span>
            <select value={form.office_id} onChange={(e) => set({ office_id: e.target.value ? Number(e.target.value) : "" })}>
              <option value="">не вказано</option>
              {meta.offices.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
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
            {canTake && <button type="button" className="btn sm" onClick={() => action.mutate({ path: "/take" })}><Hand size={14} /> Взяти собі</button>}
            <button type="button" className="btn sm" onClick={() => navigate(`/orders/new?from=${oid}`)} title="Нове замовлення цьому клієнту"><Plus size={14} /> Ще замовлення</button>
            <a className="btn sm icon" href={`${ROOT}/classic/orders/${oid}/print`} target="_blank" rel="noreferrer" title="Друк"><Printer size={15} /></a>
          </div>}
        </div>
      </div>

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
            <div className="fl"><span>Прізвище</span><input value={form.last_name} onChange={(e) => set({ last_name: e.target.value })} placeholder="Петренко" /></div>
            <div className="fl"><span>Ім'я</span><input value={form.first_name} onChange={(e) => set({ first_name: e.target.value })} placeholder="Іван" /></div>
            <div className="fl"><span>По батькові</span><input value={form.middle_name} onChange={(e) => set({ middle_name: e.target.value })} placeholder="необов'язково" /></div>
            <div className="fl"><span>Email</span><input type="email" value={form.email} onChange={(e) => set({ email: e.target.value })} placeholder="—" /></div>
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
              <div className="fl"><span>Вартість</span><div className="fl-in"><input value={form.delivery_cost} onChange={(e) => set({ delivery_cost: e.target.value })} placeholder="0" inputMode="decimal" /><span className="unit">грн</span></div></div>
              {order?.ttn && order.delivery_status && (
                <div className="ship-card"><Badge kind={deliveryKind(order.delivery_state)}>{meta.delivery_states[order.delivery_state] ?? order.delivery_state}</Badge>
                  <span className="hint">{order.delivery_status}{order.delivery_checked_at && ` · ${dt(order.delivery_checked_at, true)}`}</span></div>
              )}
              {!isNew && !order?.ttn && carrier && (
                <div className="ship-card">
                  {carrier.configured ? <>
                    <button type="button" className="btn dark block" disabled={action.isPending}
                      onClick={async () => { if (dm === "novaposhta") { if (dirty) await save.mutateAsync(); setTtnOpen(true); } else action.mutate({ path: "/ttn" }); }}>
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

          <section className="ocs">
            <h3 className="ocs-h"><Tag size={15} /> Джерело й додаткові поля</h3>
            <div className="fl"><span>Джерело</span>
              <select value={form.source_id} onChange={(e) => set({ source_id: e.target.value ? Number(e.target.value) : "" })}>
                <option value="">не вказано</option>
                {meta.order_sources.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
              </select></div>
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

// ---------------------------------------------------------------- товари в замовленні
function Goods({ items, products, onChange }: { items: OrderItem[]; products: Product[]; onChange: (i: OrderItem[]) => void }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    return products.filter((p) => !t || p.name.toLowerCase().includes(t) || p.sku.toLowerCase().includes(t)).slice(0, 30);
  }, [q, products]);
  const byId = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);
  // основні товари замовлення — до них можна привʼязати допродаж
  const mains = items.filter((i) => !i.upsell && i.product_id);
  const inOrder = new Set(items.map((i) => i.product_id).filter(Boolean));
  // що запропонувати: товари-допродажі, привʼязані до товарів у замовленні (або до будь-якого замовлення)
  const offers = mains.length ? products.filter((p) => p.upsell && !inOrder.has(p.id) && (!p.upsell_for?.length || mains.some((m) => p.upsell_for!.includes(m.product_id!)))).slice(0, 6) : [];

  const add = (p?: Product, asUpsell = false) => {
    if (p) {
      const ex = items.find((i) => i.product_id === p.id);
      if (ex) onChange(items.map((i) => (i === ex ? { ...i, qty: i.qty + 1 } : i)));
      else {
        const upsell = asUpsell || (p.upsell && mains.length > 0);
        const main = upsell ? (mains.find((m) => p.upsell_for?.includes(m.product_id!)) ?? mains[0]) : undefined;
        onChange([...items, { product_id: p.id, name: p.name, price: String(p.price), qty: 1, upsell, upsell_for: main?.product_id ?? null, base_price: p.price, key: k() }]);
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
                  <td>
                    <input className="name" value={i.name} onChange={(e) => upd(i.key, { name: e.target.value })} placeholder="Назва позиції" />
                    <div className="meta-line">
                      {p && <span>{p.sku && `${p.sku} · `}залишок {p.available}</span>}
                      <label className="mini-check"><input type="checkbox" checked={i.upsell} onChange={(e) => upd(i.key, { upsell: e.target.checked, upsell_for: e.target.checked ? others[0]?.product_id ?? null : null })} /> допродаж</label>
                      {i.upsell && others.length > 0 && (
                        <select className="mini-sel" value={i.upsell_for ?? ""} onChange={(e) => upd(i.key, { upsell_for: e.target.value ? Number(e.target.value) : null })}>
                          <option value="">до замовлення</option>
                          {others.map((o) => <option key={o.key} value={o.product_id!}>до «{o.name}»</option>)}
                        </select>
                      )}
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
      ) : <div className="goods-empty">Додайте товар — почніть вводити назву або артикул</div>}
      <div className="goods-add ac">
        <input value={q} placeholder="Додати товар: назва або артикул…" onChange={(e) => { setQ(e.target.value); setHl(0); setOpen(true); }}
          onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            const n = list.length + 1;
            if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % n); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + n) % n); }
            else if (e.key === "Enter") { e.preventDefault(); add(hl < list.length ? list[hl] : undefined); }
            else if (e.key === "Escape") { e.preventDefault(); setOpen(false); }
          }} />
        {open && (
          <div className="ac-list on">
            {list.map((p, i) => (
              <div key={p.id} className={i === hl ? "hl" : ""} onMouseDown={(e) => { e.preventDefault(); add(p); }}>
                <span>{p.name}{p.upsell && <span className="badge info">допродаж</span>}</span><small>{money(p.price)} ₴ · {p.available} шт</small>
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
