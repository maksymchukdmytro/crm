import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Banknote, Barcode, CreditCard, ExternalLink, Globe, Hand, Mail, MapPin, MessageCircle, Monitor, Phone, Plus,
  Printer, RefreshCw, Send, Tag, Trash2, Truck, User, Wallet, Warehouse,
} from "lucide-react";
import { api, ApiError, ROOT } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { date, dt, money, num, phone as fmtPhone } from "../lib/format";
import type { Order, OrderItem, Product } from "../lib/types";
import { Badge, deliveryKind, Modal, NpAutocomplete, Pill, Spinner } from "../components/ui";

type Form = {
  customer_name: string; phone: string; email: string; comment: string; status_id: number; manager_id: number | "";
  payment_type: string; prepayment: string; discount: string; delivery_method: string; delivery_cost: string;
  city_name: string; city_ref: string; warehouse_name: string; warehouse_ref: string; address: string; postcode: string;
  ttn: string; site: string; utm_source: string; utm_medium: string; utm_campaign: string; utm_content: string; utm_term: string;
  items: OrderItem[];
};

const UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"] as const;
let keySeq = 0;
const k = () => `i${++keySeq}`;

function toForm(o: Partial<Order> | undefined, defaultStatus: number): Form {
  const s = (v: unknown) => (v === null || v === undefined ? "" : String(v));
  const m = (v: number | undefined) => (v ? String(v) : "");
  return {
    customer_name: s(o?.customer_name), phone: fmtPhone(o?.phone ?? ""), email: s(o?.email), comment: s(o?.comment),
    status_id: o?.status_id ?? defaultStatus, manager_id: o?.manager_id ?? "",
    payment_type: o?.payment_type || "cod", prepayment: m(o?.prepayment), discount: m(o?.discount),
    delivery_method: o?.delivery_method || "novaposhta", delivery_cost: m(o?.delivery_cost),
    city_name: s(o?.city_name), city_ref: s(o?.city_ref), warehouse_name: s(o?.warehouse_name), warehouse_ref: s(o?.warehouse_ref),
    address: s(o?.address), postcode: s(o?.postcode), ttn: s(o?.ttn), site: s(o?.site),
    utm_source: s(o?.utm_source), utm_medium: s(o?.utm_medium), utm_campaign: s(o?.utm_campaign),
    utm_content: s(o?.utm_content), utm_term: s(o?.utm_term),
    items: (o?.items ?? []).map((i) => ({ ...i, price: String(i.price), key: k() })),
  };
}

function payload(f: Form, version?: string) {
  const { items, manager_id, ...rest } = f;
  return {
    ...rest, version, manager_id: manager_id || null,
    items: items.filter((i) => i.name.trim()).map((i) => ({ product_id: i.product_id, name: i.name, qty: i.qty, price: i.price, upsell: i.upsell })),
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

  // заповнити форму даними замовлення (і оновлювати, якщо його змінили інші, а ми нічого не редагували)
  useEffect(() => {
    if (isNew) {
      if (source) {
        const f = toForm({ customer_name: source.customer_name, phone: source.phone, email: source.email,
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

  return (
    <div className="order-card">
      <div className="oc-top">
        <h1>{isNew ? "Нове замовлення" : `№ ${oid}`}</h1>
        {order && <>
          <span className="meta">{dt(order.created_at)}{order.manager && ` · ${order.manager.name}`}</span>
          {order.duplicate_of_id && <a className="badge warn" onClick={() => onOpen(order.duplicate_of_id!)}>дубль №{order.duplicate_of_id}</a>}
          {order.stock_shipped ? <Badge kind="ok">списано зі складу</Badge> : order.stock_reserved ? <Badge kind="info">зарезервовано</Badge> : null}
          <div className="actions">
            {canTake && <button className="btn sm" onClick={() => action.mutate({ path: "/take" })}><Hand size={14} /> Взяти собі</button>}
            <button className="btn sm ghost" onClick={() => navigate(`/orders/new?from=${oid}`)} title="Нове замовлення цьому клієнту"><Plus size={14} /> Ще замовлення</button>
            <a className="btn sm ghost" href={`${ROOT}/classic/orders/${oid}/print`} target="_blank" rel="noreferrer" title="Друк"><Printer size={14} /></a>
          </div>
        </>}
      </div>

      <form className="oc" onSubmit={(e) => { e.preventDefault(); save.mutate(); }} autoComplete="off">
        {/* ============ Контакт ============ */}
        <div className="oc-col">
          <div className="sec">Контакт</div>
          <div className="prop"><Phone size={16} /><input value={form.phone} onChange={(e) => set({ phone: e.target.value })} placeholder="Телефон" inputMode="tel" required autoFocus={isNew && !fromId} />
            {order?.phone && <span className="acts"><a href={`tel:+${order.phone}`} title="Подзвонити"><Phone size={14} /></a><a href={`viber://chat?number=%2B${order.phone}`} title="Viber"><MessageCircle size={14} /></a></span>}
          </div>
          <div className="prop"><User size={16} /><input value={form.customer_name} onChange={(e) => set({ customer_name: e.target.value })} placeholder="Прізвище Ім'я По батькові" /></div>
          <div className="prop"><Mail size={16} /><input type="email" value={form.email} onChange={(e) => set({ email: e.target.value })} placeholder="Email" /></div>
          <div className="prop"><Tag size={16} />
            <select className="status-sel" style={{ ["--c" as string]: status?.color ?? "#8f8e8a" }} value={form.status_id} onChange={(e) => set({ status_id: Number(e.target.value) })}>
              {meta.statuses.filter((s) => s.active || s.id === form.status_id).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="prop"><Hand size={16} />
            {meta.user.role === "admin" ? (
              <select value={form.manager_id} onChange={(e) => set({ manager_id: e.target.value ? Number(e.target.value) : "" })}>
                <option value="">Менеджер не призначений</option>
                {meta.managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            ) : <span className={`val ${order?.manager ? "" : "muted"}`}>{order?.manager?.name ?? (isNew && meta.user.role === "manager" ? "Менеджер: ви" : "Менеджер не призначений")}</span>}
          </div>
          <div className="prop"><CreditCard size={16} />
            <select value={form.payment_type} onChange={(e) => set({ payment_type: e.target.value })}>
              {Object.entries(meta.payment_types).map(([k2, n]) => <option key={k2} value={k2}>{n}</option>)}
            </select>
          </div>
          <div className="prop"><Banknote size={16} /><input value={form.prepayment} onChange={(e) => set({ prepayment: e.target.value })} placeholder="Передоплата" inputMode="decimal" /><span className="unit">грн</span></div>
          <div className="note-box"><textarea rows={3} value={form.comment} onChange={(e) => set({ comment: e.target.value })} placeholder="Коментар до замовлення (від клієнта або для складу)" /></div>
        </div>

        {/* ============ Доставка ============ */}
        <div className="oc-col">
          <div className="sec">Доставка</div>
          <div className="prop"><Truck size={16} />
            <select value={dm} onChange={(e) => set({ delivery_method: e.target.value, city_ref: "", warehouse_ref: "", warehouse_name: "" })}>
              {Object.entries(meta.delivery_methods).map(([k2, n]) => <option key={k2} value={k2}>{n}{meta.carriers[k2]?.beta ? " (бета)" : ""}</option>)}
            </select>
          </div>
          {dm === "novaposhta" && <>
            <div className="prop"><MapPin size={16} />
              <NpAutocomplete kind="cities" value={form.city_name} refValue={form.city_ref} placeholder="Місто"
                onType={(t) => set({ city_name: t, city_ref: "" })} onPick={(o) => set({ city_name: o.name, city_ref: o.ref, warehouse_name: "", warehouse_ref: "" })} />
            </div>
            <div className="prop"><Warehouse size={16} />
              <NpAutocomplete kind="warehouses" cityRef={form.city_ref} value={form.warehouse_name} refValue={form.warehouse_ref} placeholder="Відділення або поштомат"
                onType={(t) => set({ warehouse_name: t, warehouse_ref: "" })} onPick={(o) => set({ warehouse_name: o.name, warehouse_ref: o.ref })} />
            </div>
            {!meta.carriers.novaposhta?.configured && <p className="hint indent">Підказки міст з'являться після введення API-ключа НП у налаштуваннях.</p>}
          </>}
          {dm === "ukrposhta" && <>
            <div className="prop"><MapPin size={16} /><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="Місто" /></div>
            <div className="prop"><Mail size={16} /><input value={form.postcode} onChange={(e) => set({ postcode: e.target.value })} placeholder="Індекс відділення (5 цифр)" maxLength={5} inputMode="numeric" /></div>
          </>}
          {dm === "meest" && <>
            <div className="prop"><MapPin size={16} /><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="Місто" /></div>
            <div className="prop"><Warehouse size={16} /><input value={form.warehouse_name} onChange={(e) => set({ warehouse_name: e.target.value })} placeholder="Відділення (назва / номер)" /></div>
            <div className="prop"><Tag size={16} /><input className="mono" value={form.warehouse_ref} onChange={(e) => set({ warehouse_ref: e.target.value })} placeholder="ID відділення Meest (для ТТН)" /></div>
          </>}
          {dm === "courier" && <>
            <div className="prop"><MapPin size={16} /><input value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} placeholder="Місто" /></div>
            <div className="prop"><Warehouse size={16} /><input value={form.address} onChange={(e) => set({ address: e.target.value })} placeholder="Вулиця, будинок, квартира" /></div>
          </>}
          {dm === "pickup" && <div className="prop"><MapPin size={16} /><span className="val muted">Клієнт забирає сам</span></div>}
          {dm !== "pickup" && <>
            <div className="prop"><Barcode size={16} />
              <input className="mono" value={form.ttn} onChange={(e) => set({ ttn: e.target.value })} readOnly={!!order?.carrier_ref} placeholder="ТТН (створіть або вставте номер)" />
              {order?.ttn && <span className="acts">
                {carrier && <button type="button" title="Оновити статус доставки" onClick={() => action.mutate({ path: "/track" })}><RefreshCw size={14} /></button>}
                {carrier && <a href={`${ROOT}/classic/orders/${oid}/label`} target="_blank" rel="noreferrer" title="Наклейка PDF"><Printer size={14} /></a>}
                {order.carrier_ref && <button type="button" title="Видалити ТТН" onClick={() => { if (window.confirm(`Видалити ТТН ${order.ttn} у перевізника?`)) action.mutate({ path: "/ttn", method: "del" }); }}><Trash2 size={14} /></button>}
              </span>}
            </div>
            {order?.ttn && order.delivery_status && (
              <div className="ship-card"><Badge kind={deliveryKind(order.delivery_state)}>{meta.delivery_states[order.delivery_state] ?? order.delivery_state}</Badge>
                <span className="hint">{order.delivery_status}{order.delivery_checked_at && ` · ${dt(order.delivery_checked_at, true)}`}</span></div>
            )}
            {!isNew && !order?.ttn && carrier && (
              <div className="ship-card">
                {carrier.configured ? (
                  <div className="row"><button type="button" className="btn sm dark" disabled={action.isPending} onClick={() => action.mutate({ path: "/ttn" })}><Send size={14} /> Створити ТТН {carrier.name}</button>
                    <span className="hint">накладений {money(cod)} грн</span></div>
                ) : <span className="hint">Щоб створювати ТТН, заповніть доступи в налаштуваннях доставки.</span>}
                {carrier.configured && carrier.beta && <p className="hint" style={{ margin: "6px 0 0" }}>Бета: перше відправлення зробіть тестовим.</p>}
              </div>
            )}
          </>}
          <div className="prop"><Wallet size={16} /><input value={form.delivery_cost} onChange={(e) => set({ delivery_cost: e.target.value })} placeholder="Вартість доставки" inputMode="decimal" /><span className="unit">грн</span></div>

          <div className="sec mt">Інформація</div>
          <div className="prop"><Globe size={16} /><input value={form.site} onChange={(e) => set({ site: e.target.value })} placeholder="Сайт / лендинг" /></div>
          {order?.ip && <div className="prop"><Monitor size={16} /><span className="val muted mono">{order.ip}</span></div>}
          <div className="sec mt">UTM-мітки</div>
          {UTM.map((u) => (
            <div className="prop" key={u}><span className="utm-k">{u.slice(4)}</span><input value={form[u]} onChange={(e) => set({ [u]: e.target.value } as Partial<Form>)} placeholder="—" /></div>
          ))}
        </div>

        {/* ============ Товари ============ */}
        <div className="oc-col oc-goods-col">
          <div className="oc-goods">
            <div className="sec">Товари</div>
            <Goods items={form.items} products={meta.products} onChange={(items) => set({ items })} />
            <div className="goods-foot">
              <label className="disc">Знижка, грн<input value={form.discount} onChange={(e) => set({ discount: e.target.value })} placeholder="0" inputMode="decimal" /></label>
              <div className="totals">
                <span>Товари</span><span className="num">{money(subtotal)}</span>
                <span>Знижка</span><span className="num">{num(form.discount) ? `−${money(form.discount)}` : "0"}</span>
                <span>Передоплата</span><span className="num">{money(form.prepayment)}</span>
                <span className="big">Разом</span><span className="num big">{money(total)} ₴</span>
                <span><strong>До сплати при отриманні</strong></span><span className="num"><strong>{money(cod)} ₴</strong></span>
              </div>
            </div>
          </div>
        </div>

        <div className="oc-bar">
          <button className="btn primary" disabled={save.isPending}>{save.isPending ? "Збереження…" : isNew ? "Створити замовлення" : "Зберегти"}</button>
          {dirty && <span className="hint">є незбережені зміни · Ctrl+S</span>}
        </div>
      </form>

      {order && <OrderTabs order={order} onAction={(path, body) => action.mutate({ path, body })} busy={action.isPending} onOpen={onOpen} />}
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

  const add = (p?: Product) => {
    if (p) {
      const ex = items.find((i) => i.product_id === p.id);
      if (ex) onChange(items.map((i) => (i === ex ? { ...i, qty: i.qty + 1 } : i)));
      else onChange([...items, { product_id: p.id, name: p.name, price: String(p.price), qty: 1, upsell: p.upsell, key: k() }]);
    } else onChange([...items, { product_id: null, name: q.trim(), price: "", qty: 1, upsell: false, key: k() }]);
    setQ(""); setHl(0); setOpen(false);
  };
  const upd = (key: string | undefined, patch: Partial<OrderItem>) => onChange(items.map((i) => (i.key === key ? { ...i, ...patch } : i)));

  return (
    <>
      {items.length > 0 ? (
        <table className="t items">
          <thead><tr><th>Назва</th><th className="num">К-сть</th><th className="num">Ціна</th><th title="Допродаж">Апсел</th><th className="num">Сума</th><th /></tr></thead>
          <tbody>
            {items.map((i) => {
              const p = i.product_id ? byId[i.product_id] : undefined;
              return (
                <tr key={i.key}>
                  <td><input value={i.name} onChange={(e) => upd(i.key, { name: e.target.value })} placeholder="Назва позиції" />
                    {p && <span className="meta-line">{p.sku && `${p.sku} · `}залишок {p.available}</span>}</td>
                  <td className="qty num"><input type="number" min={1} value={i.qty} onChange={(e) => upd(i.key, { qty: Math.max(1, Number(e.target.value) || 1) })} /></td>
                  <td className="price num"><input value={i.price} inputMode="decimal" onChange={(e) => upd(i.key, { price: e.target.value })} /></td>
                  <td><input type="checkbox" checked={i.upsell} onChange={(e) => upd(i.key, { upsell: e.target.checked })} title="Допродаж" /></td>
                  <td className="num sum">{money(num(i.price) * i.qty)}</td>
                  <td><button type="button" className="x" title="Прибрати" onClick={() => onChange(items.filter((x) => x.key !== i.key))}>×</button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : <div className="empty" style={{ padding: 18 }}>Товарів ще немає — знайдіть товар нижче</div>}
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
                <span>{p.name}{p.upsell && <span className="badge info">апсел</span>}</span><small>{money(p.price)} ₴ · {p.available} шт</small>
              </div>
            ))}
            <div className={hl === list.length ? "hl" : ""} onMouseDown={(e) => { e.preventDefault(); add(); }}>
              <span>{q.trim() ? `Довільна позиція «${q.trim()}»` : "Довільна позиція (без товару зі складу)"}</span><small>Enter</small>
            </div>
          </div>
        )}
      </div>
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
            <button className="btn sm mt" disabled={busy || !comment.trim()}>Додати коментар</button>
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
            <div className="row">
              <label>Передоплата, грн<input value={pay.amount} onChange={(e) => setPay({ ...pay, amount: e.target.value })} inputMode="decimal" required /></label>
              <label>Спосіб<select value={pay.method} onChange={(e) => setPay({ ...pay, method: e.target.value })}>
                <option value="card">Карта</option><option value="iban">Рахунок (IBAN)</option><option value="cash">Готівка</option><option value="other">Інше</option></select></label>
            </div>
            <label>Примітка / № квитанції<input value={pay.reference} onChange={(e) => setPay({ ...pay, reference: e.target.value })} /></label>
            <button className="btn sm mt" disabled={busy}>Додати передоплату</button>
          </form>
        </div>
      )}
      {cur === "sms" && (
        <div className="grid half">
          {meta.sms_ready ? (
            <form className="form" onSubmit={(e) => { e.preventDefault(); if (smsText.trim()) { onAction("/sms", { text: smsText, channel }); setSmsText(""); } }}>
              <textarea rows={3} value={smsText} onChange={(e) => setSmsText(e.target.value)} placeholder="Текст. Можна {ttn}, {total}, {cod}, {first_name}…" />
              <div className="row mt"><select style={{ width: "auto" }} value={channel} onChange={(e) => setChannel(e.target.value)}>
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
