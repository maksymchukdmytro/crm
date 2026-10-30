// Вікно «Нова ТТН» (UI-DESIGN §5.6, макет 03): ліворуч відправник, отримувач, спосіб доставки, місто й відділення з пошуком по довіднику НП
// (видно обмеження ваги), хто платить, вантаж, вага й розміри, оголошена вартість, післяплата (з оплати, лише читання), опис.
// Праворуч — вартість доставки, комісія, очікувана дата й дії «Одразу після створення». Головна кнопка — «Створити ТТН» (Ctrl ⏎).
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Building2, Info, MapPin, Package, Search, Truck, User, Warehouse } from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta } from "../lib/app";
import { money } from "../lib/format";
import type { Order, TtnParams, TtnPreview } from "../lib/types";
import { Button, Segmented, Window } from "../components/ui";

const PAYERS = { Recipient: "Отримувач", Sender: "Відправник", ThirdPerson: "Третя особа" } as const;
const CARGO = { Parcel: "Посилка", Cargo: "Вантаж", Documents: "Документи", TiresWheels: "Шини-диски", Pallet: "Палети" } as const;
const COD = { afterpayment: "Контроль оплати", backward: "Грошовий переказ", none: "Без післяплати" } as const;
type Seat = { length: string; width: string; height: string; weight: string };
type Opt = { ref: string; name: string; label: string; max_weight?: number | null; kind?: string };
type Created = Order & { label_url?: string | null; after_errors?: string[] };

const PREF = "crm-ttn-after";
function loadAfter() {
  try { return { print_label: true, add_registry: true, send_sms: true, set_shipped: false, ...JSON.parse(localStorage.getItem(PREF) || "{}") }; }
  catch { return { print_label: true, add_registry: true, send_sms: true, set_shipped: false }; }
}

export default function TtnDialog({ order, accountId, onClose, onCreated }: {
  order: Order; accountId: number | ""; onClose: () => void; onCreated: (o: Order, labelUrl?: string | null) => void;
}) {
  const meta = useMeta();
  const [acc, setAcc] = useState<number | "">(accountId);
  const [way, setWay] = useState<"branch" | "postomat" | "courier">(/поштомат/i.test(order.warehouse_name) ? "postomat" : "branch");
  const [city, setCity] = useState({ name: order.city_name, ref: order.city_ref });
  const [wh, setWh] = useState({ name: order.warehouse_name, ref: order.warehouse_ref, max: null as number | null });
  const [p, setP] = useState<(Omit<TtnParams, "seats"> & { seats: Seat[] }) | null>(null);
  const [after, setAfter] = useState(loadAfter);
  const [err, setErr] = useState("");
  const { data, error } = useQuery({
    queryKey: ["ttn-preview", order.id, acc, city.ref],
    queryFn: () => api.get<TtnPreview>(`/orders/${order.id}/ttn/preview${qs({ np_account_id: acc || undefined, city_ref: city.ref || undefined })}`),
  });
  useEffect(() => {
    if (!data?.params || p) return;
    const d = data.params;
    setP({ ...d, seats: d.seats.map((x) => ({ length: String(x.length), width: String(x.width), height: String(x.height), weight: String(x.weight) })) });
    if (!acc && data.np_account_id) setAcc(data.np_account_id);
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (patch: Partial<NonNullable<typeof p>>) => setP((x) => (x ? { ...x, ...patch } : x));
  const seat = (patch: Partial<Seat>) => p && set({ seats: p.seats.map((x, j) => (j === 0 ? { ...x, ...patch } : x)) });
  const weight = p ? p.seats.reduce((s, x) => s + Number(x.weight || 0), 0) : 0;
  const tooHeavy = wh.max != null && weight > wh.max;
  const toggle = (k: keyof ReturnType<typeof loadAfter>) => setAfter((a: ReturnType<typeof loadAfter>) => { const n = { ...a, [k]: !a[k] }; try { localStorage.setItem(PREF, JSON.stringify(n)); } catch { /* */ } return n; });

  const create = useMutation({
    mutationFn: () => {
      if (!p) throw new Error("Параметри ще завантажуються");
      if (!city.ref || !wh.ref) throw new Error("Оберіть місто й відділення зі списку довідника НП");
      return api.post<Created>(`/orders/${order.id}/ttn`, {
        np_account_id: acc || undefined, payer: p.payer, cargo_type: p.cargo_type, service_type: p.service_type,
        description: p.description, declared_cost: Number(p.declared_cost) || 1, cod_mode: p.cod_mode,
        cod_amount: p.cod_mode === "none" ? 0 : Number(p.cod_amount) || 0, cod_payer: p.cod_payer, additional_info: p.additional_info,
        seats: p.seats.map((x) => ({ length: Number(x.length), width: Number(x.width), height: Number(x.height), weight: Number(x.weight) })),
        city_name: city.name, city_ref: city.ref, warehouse_name: wh.name, warehouse_ref: wh.ref,
        after: { print_label: after.print_label, add_registry: after.add_registry, send_sms: after.send_sms && meta.sms_ready, set_shipped: after.set_shipped },
      });
    },
    onSuccess: (o) => { (o.after_errors ?? []).forEach((e) => setErr(e)); onCreated(o, o.label_url); },
    onError: (e) => setErr(errText(e)),
  });

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); if (!create.isPending) create.mutate(); } };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [create]);

  const head = (
    <div className="win-head ttn-head">
      <span className="ttn-ic"><Truck size={18} /></span>
      <div><h2>Нова ТТН</h2><small className="muted">Замовлення №{order.id} · Нова Пошта</small></div>
      <div className="acts" />
    </div>
  );
  return (
    <Window size="lg" onClose={onClose} head={head} label="Нова ТТН" className="ttn-win" bodyClass="ttn-body"
      footer={<>
        <span className="hint ttn-foot-hint"><Info size={13} />{city.ref && wh.ref ? "Адреса з довідника НП" : "Місто й відділення — зі списку довідника НП"}</span>
        <span className="spacer" />
        <Button onClick={onClose}>Скасувати</Button>
        <Button variant="primary" icon={Truck} kbd="Ctrl ⏎" disabled={create.isPending || !p} onClick={() => create.mutate()}>{create.isPending ? "Створюю…" : "Створити ТТН"}</Button>
      </>}>
      {error ? <p className="flash error">{errText(error)}</p> : !p ? <div className="skel-rows">{[0, 1, 2, 3, 4].map((i) => <div key={i} className="skel-row"><span className="skel" /></div>)}</div> : (
        <div className="ttn-grid">
          <div className="block ttn-form">
            <div className="ttn-2">
              <label className="fbox"><span className="lbl">Відправник · ключ НП</span>
                <span className="sel-ic"><span className="np-badge">НП</span>
                  <select value={acc} onChange={(e) => setAcc(e.target.value ? Number(e.target.value) : "")} aria-label="Відправник">
                    {(data?.accounts ?? []).map((a) => <option key={a.id} value={a.id}>{a.name}{a.is_default ? " · основний" : ""}</option>)}
                  </select></span>
                {data?.sender && <small className="hint">{data.sender}</small>}
              </label>
              <div className="fbox"><span className="lbl">Отримувач</span><div className="ro-field"><User size={14} />{data?.recipient || order.customer_name}</div></div>
            </div>
            <div className="fbox"><span className="lbl">Спосіб доставки</span>
              <Segmented label="Спосіб доставки" value={way} onChange={(k) => { if (k === "courier") return; setWay(k); setWh({ name: "", ref: "", max: null }); }}
                items={[{ key: "branch", label: "Відділення", icon: <Warehouse size={14} /> }, { key: "postomat", label: "Поштомат", icon: <Package size={14} /> },
                  { key: "courier", label: "Кур'єр на адресу", icon: <MapPin size={14} />, title: "Адресна доставка — поки в кабінеті НП" }]} />
            </div>
            <div className="ttn-2">
              <NpSearch kind="cities" label="Місто" value={city.name} refValue={city.ref} placeholder="Почніть вводити місто"
                onPick={(o) => { setCity({ name: o.name, ref: o.ref }); setWh({ name: "", ref: "", max: null }); }} onType={(t) => setCity({ name: t, ref: "" })} />
              <NpSearch kind="warehouses" label={way === "postomat" ? "Поштомат" : "Відділення"} cityRef={city.ref} filter={way} value={wh.name} refValue={wh.ref}
                placeholder="Номер або вулиця" onPick={(o) => setWh({ name: o.name, ref: o.ref, max: o.max_weight ?? null })} onType={(t) => setWh({ name: t, ref: "", max: null })} />
            </div>
            <div className="fbox"><span className="lbl">Хто платить за доставку</span>
              <Segmented label="Платник" value={p.payer} onChange={(k) => set({ payer: k as TtnParams["payer"] })}
                items={Object.entries(PAYERS).map(([k, n]) => ({ key: k, label: n }))} />
            </div>
            <div className="ttn-4">
              <label className="fbox"><span className="lbl">Тип вантажу</span>
                <select value={p.cargo_type} onChange={(e) => set({ cargo_type: e.target.value as TtnParams["cargo_type"] })}>{Object.entries(CARGO).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></label>
              <label className={`fbox${tooHeavy ? " has-err" : ""}`}><span className="lbl">Вага, кг</span>
                <input value={p.seats[0]?.weight ?? ""} inputMode="decimal" onChange={(e) => seat({ weight: e.target.value.replace(",", ".") })} />
                {tooHeavy && <span className="err-hint">Ліміт відділення — {wh.max} кг</span>}</label>
              <div className="fbox"><span className="lbl">Д × Ш × В, см</span>
                <div className="dims">{(["length", "width", "height"] as const).map((k) => (
                  <input key={k} value={p.seats[0]?.[k] ?? ""} inputMode="numeric" aria-label={{ length: "Довжина", width: "Ширина", height: "Висота" }[k]} onChange={(e) => seat({ [k]: e.target.value.replace(/\D/g, "") })} />))}</div></div>
              <label className="fbox"><span className="lbl">Місць</span>
                <input value={p.seats.length} inputMode="numeric" onChange={(e) => {
                  const n = Math.max(1, Math.min(20, Number(e.target.value.replace(/\D/g, "")) || 1));
                  set({ seats: Array.from({ length: n }, (_, i) => p.seats[i] ?? { ...p.seats[0] }) });
                }} /></label>
            </div>
            <div className="ttn-2">
              <label className="fbox"><span className="lbl">Оголошена вартість</span>
                <span className="money-in"><input value={p.declared_cost} inputMode="numeric" onChange={(e) => set({ declared_cost: Number(e.target.value.replace(/\D/g, "")) || 0 })} /><span className="unit">₴</span></span></label>
              <div className="fbox"><span className="lbl">Післяплата · з оплати замовлення</span>
                <div className="ro-field">{data?.prepaid ? "Оплачено — без післяплати" : `${COD[p.cod_mode as keyof typeof COD] ?? p.cod_mode}${p.cod_mode !== "none" ? ` · ${money(p.cod_amount)} ₴` : ""}`}</div></div>
            </div>
            <label className="fbox"><span className="lbl">Опис</span><input value={p.description} maxLength={100} onChange={(e) => set({ description: e.target.value })} /></label>
            {err && <p className="flash error" role="alert">{err}</p>}
          </div>
          <div className="ttn-side">
            <section className="summary-block">
              <div className="lbl">Вартість доставки</div>
              <div className="big">{data?.price ? `≈ ${money(data.price)}` : "—"} <span className="cur">₴</span></div>
              <div className="hint">платить {PAYERS[p.payer as keyof typeof PAYERS]?.toLowerCase() ?? "отримувач"} · за тарифом НП</div>
              <div className="sum-rows">
                {data?.cod_commission != null && <div><span>Комісія за {p.cod_mode === "afterpayment" ? "контроль оплати" : "переказ"}</span><b>≈ {money(data.cod_commission)} ₴</b></div>}
                <div><span>Очікувана доставка</span><b>{data?.eta ? new Date(`${data.eta}T12:00:00`).toLocaleDateString("uk-UA", { weekday: "short", day: "2-digit", month: "2-digit" }) : "—"}</b></div>
                <div><span>Вага</span><b>{weight.toLocaleString("uk-UA")} кг{wh.max ? ` · ліміт ${wh.max}` : ""}</b></div>
              </div>
            </section>
            <section className="block ttn-after">
              <h2>Одразу після створення</h2>
              <label className="check"><input type="checkbox" checked={after.print_label} onChange={() => toggle("print_label")} />Друкувати наклейку</label>
              <label className="check"><input type="checkbox" checked={after.add_registry} onChange={() => toggle("add_registry")} />Додати в реєстр на сьогодні</label>
              <label className="check" title={meta.sms_ready ? undefined : "SMS не підключено"}><input type="checkbox" disabled={!meta.sms_ready} checked={after.send_sms && meta.sms_ready} onChange={() => toggle("send_sms")} />SMS покупцю з номером ТТН</label>
              <label className="check"><input type="checkbox" checked={after.set_shipped} onChange={() => toggle("set_shipped")} />Статус «Відправлений» одразу</label>
              <p className="hint"><Building2 size={12} /> Типові значення беруться з ключа НП</p>
            </section>
          </div>
        </div>
      )}
    </Window>
  );
}

/** Пошук міста або відділення по довіднику НП; у відділень — обмеження ваги, фільтр «поштомат / відділення». */
function NpSearch({ kind, label, cityRef, filter, value, refValue, placeholder, onPick, onType }: {
  kind: "cities" | "warehouses"; label: string; cityRef?: string; filter?: string; value: string; refValue: string; placeholder: string;
  onPick: (o: Opt) => void; onType: (t: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const dq = useDebounced(value, 250);
  const box = useRef<HTMLDivElement>(null);
  const enabled = open && (kind === "warehouses" ? !!cityRef : dq.trim().length >= 2);
  const q = useQuery({
    queryKey: ["np", kind, cityRef, dq], enabled,
    queryFn: () => api.get<{ ok: boolean; items?: Opt[]; error?: string }>(`/np/${kind}${qs({ q: refValue ? "" : dq, city_ref: cityRef })}`),
  });
  const items = (q.data?.items ?? []).filter((o) => kind !== "warehouses" || !filter || filter === "courier" || (filter === "postomat" ? o.kind === "postomat" : o.kind !== "postomat"));
  const pick = (o?: Opt) => { if (o) { onPick(o); setOpen(false); } };
  return (
    <div className="fbox np-search" ref={box}>
      <span className="lbl">{label}</span>
      <span className={`np-in${refValue ? " ok" : ""}`}>
        {kind === "cities" ? <MapPin size={15} /> : <Search size={15} />}
        <input value={value} placeholder={kind === "warehouses" && !cityRef ? "Спершу оберіть місто" : placeholder} disabled={kind === "warehouses" && !cityRef}
          onChange={(e) => { onType(e.target.value); setOpen(true); setHl(0); }} onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (!open || !items.length) return;
            if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % items.length); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + items.length) % items.length); }
            else if (e.key === "Enter") { e.preventDefault(); pick(items[hl]); }
            else if (e.key === "Escape") { e.stopPropagation(); setOpen(false); }
          }} aria-label={label} />
      </span>
      {open && enabled && (
        <div className="pop np-pop" role="listbox">
          {q.isFetching && !items.length && <div className="note-empty">Пошук…</div>}
          {q.data && !q.data.ok && <div className="note-empty">{q.data.error}</div>}
          {q.data?.ok && !items.length && !q.isFetching && <div className="note-empty">Нічого не знайдено</div>}
          {items.slice(0, 30).map((o, i) => (
            <button key={o.ref} type="button" role="option" aria-selected={o.ref === refValue} className={`pop-item np-opt${i === hl ? " hl" : ""}`}
              onMouseDown={(e) => { e.preventDefault(); pick(o); }} onMouseEnter={() => setHl(i)}>
              {kind === "warehouses" ? (o.kind === "postomat" ? <Package size={15} /> : <Warehouse size={15} />) : <MapPin size={15} />}
              <span className="ell" style={{ flex: 1 }}>{o.label || o.name}</span>
              {o.max_weight ? <small className="muted">до {o.max_weight} кг</small> : null}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
