// Вікно «Нова ТТН» (макети docs/design/wizard-ttn, рішення власника 31.10) — у стилі покрокового замовлення:
// ліворуч великі плитки «Відділення / Поштомат / Кур'єр», місто, список відділень з пошуком (вага й години), хто платить,
// посилка одним рядком («Змінити» — розміри, вага, опис); праворуч — вартість і дата доставки, післяплата, дії «одразу після
// створення» й одна кнопка «Створити ТТН» (Ctrl ⏎). Після створення — екран «Готово»: номер, що вже зроблено, наступні дії.
// На телефоні — два кроки на весь екран («Куди» → «Посилка й оплата»), ціна над кнопкою.
import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Calendar, Check, ChevronDown, ChevronLeft, ChevronRight, CircleAlert, CircleCheck, Copy, KeyRound, ListChecks, MapPin, MessageSquare, Package,
  Printer, Search, Send, Store, Truck, User, Users, X,
} from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money } from "../lib/format";
import type { Order, TtnParams, TtnPreview } from "../lib/types";
import { StatusPill, Window, useMobile } from "../components/ui";
import { printLabel } from "./card/util";

const PAYERS = { Recipient: "Отримувач", Sender: "Відправник", ThirdPerson: "Третя особа" } as const;
const CARGO = { Parcel: "Посилка", Cargo: "Вантаж", Documents: "Документи", TiresWheels: "Шини-диски", Pallet: "Палети" } as const;
const COD = { afterpayment: "Контроль оплати", backward: "Грошовий переказ", none: "Без післяплати" } as const;
type Way = "branch" | "postomat" | "courier";
type Seat = { length: string; width: string; height: string; weight: string };
type Opt = { ref: string; name: string; label: string; max_weight?: number | null; kind?: string };
type Created = Order & { label_url?: string | null; after_errors?: string[] };
type After = { print_label: boolean; add_registry: boolean; send_sms: boolean; set_shipped: boolean };

const PREF = "crm-ttn-after";
const AFTER0: After = { print_label: true, add_registry: true, send_sms: true, set_shipped: false };
function loadAfter(): After {
  try { return { ...AFTER0, ...JSON.parse(localStorage.getItem(PREF) || "{}") }; } catch { return AFTER0; }
}
const kg = (v: number) => v.toLocaleString("uk-UA", { maximumFractionDigits: 2 });
const ttnFmt = (v: string) => v.replace(/^(\d{2})(\d{4})(\d{4})(\d{4})$/, "$1 $2 $3 $4");
const dayText = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00`);
  const t = new Date(); t.setHours(12, 0, 0, 0);
  const diff = Math.round((d.getTime() - t.getTime()) / 86400_000);
  const date = d.toLocaleDateString("uk-UA", { day: "numeric", month: "long" });
  return diff === 0 ? `сьогодні, ${date}` : diff === 1 ? `завтра, ${date}` : diff === 2 ? `післязавтра, ${date}` : d.toLocaleDateString("uk-UA", { weekday: "long", day: "numeric", month: "long" });
};

export default function TtnDialog({ order, accountId, onClose, onCreated }: {
  order: Order; accountId: number | ""; onClose: () => void; onCreated: (o: Order, labelUrl?: string | null) => void;
}) {
  const meta = useMeta();
  const mobile = useMobile();
  const [acc, setAcc] = useState<number | "">(accountId);
  const [way, setWay] = useState<Way>(order.address && !order.warehouse_ref ? "courier" : /поштомат/i.test(order.warehouse_name) ? "postomat" : "branch");
  const [city, setCity] = useState({ name: order.city_name, ref: order.city_ref });
  const [wh, setWh] = useState({ name: order.warehouse_name, ref: order.warehouse_ref, max: null as number | null });
  const [street, setStreet] = useState({ name: "", ref: "" });
  const [house, setHouse] = useState("");
  const [flat, setFlat] = useState("");
  const [p, setP] = useState<(Omit<TtnParams, "seats"> & { seats: Seat[] }) | null>(null);
  const [after, setAfter] = useState(loadAfter);
  const [parcelOpen, setParcelOpen] = useState(false);
  const [mstep, setMstep] = useState(0);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<Created | null>(null);
  const service = way === "courier" ? "WarehouseDoors" : "WarehouseWarehouse";
  const { data, error } = useQuery({
    queryKey: ["ttn-preview", order.id, acc, city.ref, service],
    queryFn: () => api.get<TtnPreview>(`/orders/${order.id}/ttn/preview${qs({ np_account_id: acc || undefined, city_ref: city.ref || undefined, service_type: service })}`),
    placeholderData: (prev) => prev,
  });
  useEffect(() => {
    if (!data?.params || p) return;
    const d = data.params;
    setP({ ...d, service_type: service, seats: d.seats.map((x) => ({ length: String(x.length), width: String(x.width), height: String(x.height), weight: String(x.weight) })) });
    if (!acc && data.np_account_id) setAcc(data.np_account_id);
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (patch: Partial<NonNullable<typeof p>>) => { setErr(""); setP((x) => (x ? { ...x, ...patch } : x)); };
  const seat = (patch: Partial<Seat>) => p && set({ seats: p.seats.map((x, j) => (j === 0 ? { ...x, ...patch } : x)) });
  const weight = p ? p.seats.reduce((s, x) => s + Number(x.weight || 0), 0) : 0;
  const tooHeavy = way !== "courier" && wh.max != null && weight > wh.max;
  const toggle = (k: keyof After) => setAfter((a) => { const n = { ...a, [k]: !a[k] }; try { localStorage.setItem(PREF, JSON.stringify(n)); } catch { /* */ } return n; });
  const pickWay = (w: Way) => { setErr(""); setWay(w); if ((w === "postomat") !== (way === "postomat") || w === "courier") setWh({ name: "", ref: "", max: null }); };

  const whereProblem = !city.ref ? "Оберіть місто зі списку довідника НП"
    : way === "courier" ? (!street.ref ? "Оберіть вулицю зі списку довідника НП" : !house.trim() ? "Вкажіть номер будинку" : "")
      : !wh.ref ? `Оберіть ${way === "postomat" ? "поштомат" : "відділення"} зі списку` : "";

  const create = useMutation({
    mutationFn: () => {
      if (!p) throw new Error("Параметри ще завантажуються");
      if (whereProblem) { setMstep(0); throw new Error(whereProblem); }
      if (tooHeavy) { setParcelOpen(true); throw new Error(`Вага ${kg(weight)} кг більша за ліміт відділення — ${wh.max} кг`); }
      return api.post<Created>(`/orders/${order.id}/ttn`, {
        np_account_id: acc || undefined, payer: p.payer, cargo_type: p.cargo_type, service_type: service,
        description: p.description, declared_cost: Number(p.declared_cost) || 1, cod_mode: p.cod_mode,
        cod_amount: p.cod_mode === "none" ? 0 : Number(p.cod_amount) || 0, cod_payer: p.cod_payer, additional_info: p.additional_info,
        seats: p.seats.map((x) => ({ length: Number(x.length), width: Number(x.width), height: Number(x.height), weight: Number(x.weight) })),
        city_name: city.name, city_ref: city.ref,
        ...(way === "courier" ? { warehouse_name: "", warehouse_ref: "", street_ref: street.ref, street_name: street.name, house: house.trim(), flat: flat.trim() }
          : { warehouse_name: wh.name, warehouse_ref: wh.ref }),
        after: { print_label: after.print_label, add_registry: after.add_registry, send_sms: after.send_sms && meta.sms_ready, set_shipped: after.set_shipped },
      });
    },
    onSuccess: (o) => { setDone(o); onCreated(o, o.label_url); },
    onError: (e) => setErr(errText(e)),
  });

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || e.defaultPrevented) return;
      if (done) { if (!(e.target as HTMLElement).closest("button")) { e.preventDefault(); onClose(); } return; }
      if ((e.ctrlKey || e.metaKey) && !create.isPending) { e.preventDefault(); create.mutate(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const accounts = data?.accounts ?? [];
  const sub = [`Замовлення №${order.id}`, order.customer_name, order.phone && `+${order.phone}`.replace(/^\+380(\d{2})(\d{3})(\d{2})(\d{2})$/, "+380 $1 $2 $3 $4")].filter(Boolean).join(" · ");
  const head = (
    <div className="tt-head">
      <button type="button" className="rb m-only" aria-label={mobile && mstep && !done ? "Назад" : "Закрити"} onClick={() => (mobile && mstep && !done ? setMstep(0) : onClose())}>
        {mobile && mstep && !done ? <ChevronLeft size={20} /> : <X size={20} />}</button>
      <span className="np-badge lg d-only">НП</span>
      <div className="tt-title"><b>Нова ТТН{mobile ? ` · №${order.id}` : ""}</b>
        <small>{mobile ? (done ? "Готово" : `Крок ${mstep + 1} з 2 · ${mstep ? "Посилка й оплата" : "Куди"}`) : sub}</small></div>
      {!done && accounts.length > 0 && (
        <label className="tt-key d-only" title={data?.sender || undefined}>
          <KeyRound size={15} aria-hidden /><span className="muted">Відправник:</span>
          <select value={acc} onChange={(e) => setAcc(e.target.value ? Number(e.target.value) : "")} aria-label="Відправник — ключ НП">
            {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}{a.is_default ? " · основний ключ" : ""}</option>)}
          </select><ChevronDown size={15} aria-hidden /></label>
      )}
      <button type="button" className="wz-x d-only" aria-label="Закрити (Esc)" onClick={onClose}><X size={17} /></button>
      {mobile && !done && <div className="wz-prog m-only" aria-hidden>{[0, 1].map((i) => <i key={i} className={i < mstep ? "ok" : i === mstep ? "cur" : ""} />)}</div>}
    </div>
  );

  if (done) return <Window size="md" className="tt2 tt-done" onClose={onClose} head={head} label="ТТН створено" bodyClass="tt-body"><Done o={done} after={after} eta={data?.eta} onClose={onClose} /></Window>;

  const payer = p ? PAYERS[p.payer as keyof typeof PAYERS] ?? "Отримувач" : "Отримувач";
  const codText = data?.prepaid ? "Оплачено — без післяплати" : p ? `${COD[p.cod_mode as keyof typeof COD] ?? p.cod_mode}${p.cod_mode !== "none" ? ` · ${money(p.cod_amount)} ₴` : ""}` : "";
  const priceBig = data?.price ? `≈ ${money(data.price)} ₴` : "—";
  const when = data?.eta ? `Орієнтовно ${dayText(data.eta)}` : city.ref ? "Дату покаже НП" : "Оберіть місто — порахуємо ціну й дату";
  const loading = !p;

  // ---------------- секції
  const where = (
    <section className="tt-sec">
      {mobile && accounts.length > 0 && (
        <label className="tt-mkey"><span className="np-badge lg">НП</span>
          <span className="tt-mkey-t"><b>{accounts.find((a) => a.id === acc)?.name ?? "Ключ НП"}</b><small>{acc === accounts.find((a) => a.is_default)?.id ? "основний ключ · " : ""}відправник</small></span>
          <select value={acc} onChange={(e) => setAcc(e.target.value ? Number(e.target.value) : "")} aria-label="Відправник — ключ НП">
            {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}{a.is_default ? " · основний ключ" : ""}</option>)}
          </select><ChevronDown size={16} aria-hidden /></label>
      )}
      <h3 className="tt-h d-only">Куди</h3>
      <div className="tt-ways" role="radiogroup" aria-label="Спосіб доставки">
        {([["branch", Store, "t-blue", "Відділення", "до 30 кг"], ["postomat", Package, "t-purple", "Поштомат", "до 20 кг"], ["courier", Truck, "t-orange", "Кур'єр", "на адресу"]] as const).map(([k, Icon, t, n, s]) => (
          <button key={k} type="button" role="radio" aria-checked={way === k} className={`tt-way${way === k ? " on" : ""}`} onClick={() => pickWay(k)}>
            <span className={`sq ${t}`}><Icon size={17} /></span><span><b>{n}</b><small>{s}</small></span></button>
        ))}
      </div>
      <div className="tt-where">
        <NpSearch kind="cities" label="Місто" value={city.name} refValue={city.ref} placeholder="Почніть вводити місто" icon={<MapPin size={18} />}
          onPick={(o) => { setErr(""); setCity({ name: o.name, ref: o.ref }); setWh({ name: "", ref: "", max: null }); setStreet({ name: "", ref: "" }); }}
          onType={(t) => setCity({ name: t, ref: "" })} />
        {way === "courier" ? (
          <NpSearch kind="streets" label="Вулиця" cityRef={city.ref} value={street.name} refValue={street.ref} placeholder="Назва вулиці" icon={<Search size={18} />}
            accountId={acc} onPick={(o) => { setErr(""); setStreet({ name: o.name, ref: o.ref }); }} onType={(t) => setStreet({ name: t, ref: "" })} />
        ) : (
          <WarehouseList cityRef={city.ref} way={way} value={wh} onPick={(o) => { setErr(""); setWh({ name: o.name, ref: o.ref, max: o.max_weight ?? null }); }} />
        )}
      </div>
      {way === "courier" && (
        <div className="tt-house">
          <label className="fbox"><span className="wz-lb">Будинок</span><input className="wz-big" value={house} onChange={(e) => { setErr(""); setHouse(e.target.value.slice(0, 10)); }} /></label>
          <label className="fbox"><span className="wz-lb">Квартира</span><input className="wz-big" value={flat} placeholder="—" onChange={(e) => setFlat(e.target.value.slice(0, 10))} /></label>
          <p className="wz-muted"><CircleAlert size={14} />Кур'єр зателефонує отримувачу перед доставкою — номер береться із замовлення</p>
        </div>
      )}
    </section>
  );

  const parcel = p && (
    <section className="tt-sec">
      <h3 className="tt-h">Хто платить за доставку</h3>
      <div className="tt-payers" role="radiogroup" aria-label="Платник">
        {([["Recipient", User], ["Sender", Store], ["ThirdPerson", Users]] as const).map(([k, Icon]) => (
          <button key={k} type="button" role="radio" aria-checked={p.payer === k} className={`tt-way sm${p.payer === k ? " on" : ""}`} onClick={() => set({ payer: k })}>
            <span className={`sq ${p.payer === k ? "t-blue" : "t-gray"}`}><Icon size={15} /></span><b>{PAYERS[k]}</b></button>
        ))}
      </div>
      <h3 className="tt-h">Посилка <small>з товарів замовлення</small></h3>
      <div className={`tt-parcel${tooHeavy ? " bad" : ""}`}>
        <span className="sq t-gray"><Package size={16} /></span>
        <span className="tt-parcel-t"><b>{CARGO[p.cargo_type as keyof typeof CARGO] ?? "Посилка"} · {kg(weight)} кг</b>
          <small>{p.seats[0] ? `${p.seats[0].length} × ${p.seats[0].width} × ${p.seats[0].height} см` : ""} · {p.seats.length} {p.seats.length === 1 ? "місце" : "місць"} · «{p.description}»</small></span>
        <button type="button" className="link-btn" aria-expanded={parcelOpen} onClick={() => setParcelOpen((x) => !x)}>{parcelOpen ? "Готово" : "Змінити"}</button>
      </div>
      {tooHeavy && <p className="wz-err"><CircleAlert size={15} />Ліміт відділення — {wh.max} кг. Оберіть інше відділення або кур'єра.</p>}
      {parcelOpen && (
        <div className="tt-edit">
          <label className="fbox"><span className="wz-lb">Тип вантажу</span>
            <span className="wz-sel"><select value={p.cargo_type} onChange={(e) => set({ cargo_type: e.target.value as TtnParams["cargo_type"] })}>
              {Object.entries(CARGO).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select><ChevronDown size={16} aria-hidden /></span></label>
          <label className="fbox"><span className="wz-lb">Вага, кг</span>
            <input className="wz-big sm" value={p.seats[0]?.weight ?? ""} inputMode="decimal" onChange={(e) => seat({ weight: e.target.value.replace(",", ".") })} /></label>
          <div className="fbox"><span className="wz-lb">Д × Ш × В, см</span>
            <div className="tt-dims">{(["length", "width", "height"] as const).map((k) => (
              <input key={k} className="wz-big sm" value={p.seats[0]?.[k] ?? ""} inputMode="numeric" aria-label={{ length: "Довжина", width: "Ширина", height: "Висота" }[k]}
                onChange={(e) => seat({ [k]: e.target.value.replace(/\D/g, "") })} />))}</div></div>
          <label className="fbox"><span className="wz-lb">Місць</span>
            <input className="wz-big sm" value={p.seats.length} inputMode="numeric" onChange={(e) => {
              const n = Math.max(1, Math.min(20, Number(e.target.value.replace(/\D/g, "")) || 1));
              set({ seats: Array.from({ length: n }, (_, i) => p.seats[i] ?? { ...p.seats[0] }) });
            }} /></label>
          <label className="fbox"><span className="wz-lb">Оголошена вартість, ₴</span>
            <input className="wz-big sm" value={p.declared_cost} inputMode="numeric" onChange={(e) => set({ declared_cost: Number(e.target.value.replace(/\D/g, "")) || 0 })} /></label>
          <label className="fbox wide"><span className="wz-lb">Опис</span><input className="wz-big sm" value={p.description} maxLength={100} onChange={(e) => set({ description: e.target.value })} /></label>
        </div>
      )}
      {mobile && (
        <div className="tt-mrows">
          <div><span>{data?.prepaid ? "Післяплата" : COD[p.cod_mode as keyof typeof COD] ?? "Післяплата"}</span><b>{data?.prepaid || p.cod_mode === "none" ? "немає" : `${money(p.cod_amount)} ₴`}</b></div>
          <div><span>Оголошена вартість</span><b>{money(p.declared_cost)} ₴</b></div>
        </div>
      )}
    </section>
  );

  const afterList = (
    <div className="tt-after">
      <div className="tt-after-h">Одразу після створення</div>
      <Switch on={after.print_label} onClick={() => toggle("print_label")} icon={<Printer size={16} />}>Друкувати наклейку</Switch>
      <Switch on={after.add_registry} onClick={() => toggle("add_registry")} icon={<ListChecks size={16} />}>У реєстр на сьогодні</Switch>
      <Switch on={after.send_sms && meta.sms_ready} disabled={!meta.sms_ready} onClick={() => toggle("send_sms")} icon={<MessageSquare size={16} />}
        title={meta.sms_ready ? undefined : "SMS не підключено"}>SMS покупцю з ТТН</Switch>
      <Switch on={after.set_shipped} onClick={() => toggle("set_shipped")} icon={<Send size={16} />}>Статус «Відправлений»</Switch>
    </div>
  );

  const button = (
    <button type="button" className="btn primary tt-go" disabled={create.isPending || loading} onClick={() => create.mutate()}>
      <Truck size={18} />{create.isPending ? "Створюю…" : "Створити ТТН"}<kbd>Ctrl ⏎</kbd></button>
  );

  // ---------------- телефон: два кроки
  if (mobile) {
    const foot = (
      <div className="tt-mfoot">
        {err && <p className="wz-err" role="alert"><CircleAlert size={15} />{err}</p>}
        <div className="tt-mprice"><span><small>Доставка · платить {payer.toLowerCase()}</small><b>{priceBig}</b></span><span className="tt-when"><Calendar size={15} />{data?.eta ? dayText(data.eta) : "—"}</span></div>
        <div className="wz-btns">
          {mstep === 1 && <button type="button" className="btn wz-back" onClick={() => setMstep(0)} aria-label="Назад"><ChevronLeft size={20} /></button>}
          {mstep === 0
            ? <button type="button" className="btn primary wz-next" onClick={() => { if (whereProblem) setErr(whereProblem); else { setErr(""); setMstep(1); } }}>Далі<ChevronRight size={19} /></button>
            : button}
        </div>
      </div>
    );
    return (
      <Window size="lg" className="tt2" onClose={onClose} head={head} footer={foot} label="Нова ТТН" bodyClass="tt-body">
        {error ? <p className="flash error">{errText(error)}</p> : loading ? <Skeleton /> : mstep === 0 ? where : (<>
          {mstep === 1 && <div className="wz-q"><h2>Посилка й оплата</h2><p>Усе підставлено з замовлення — перевірте</p></div>}
          {parcel}{afterList}</>)}
      </Window>
    );
  }

  // ---------------- комп'ютер: один екран, праворуч ціна й кнопка
  return (
    <Window size="lg" className="tt2" onClose={onClose} head={head} label="Нова ТТН" bodyClass="tt-body">
      {error ? <p className="flash error">{errText(error)}</p> : loading ? <Skeleton /> : (
        <div className="tt-grid">
          <div className="tt-main">{where}{parcel}</div>
          <aside className="tt-side">
            <div className="tt-side-l">Вартість доставки</div>
            <div className="tt-price">{priceBig}</div>
            <div className="tt-when"><Calendar size={15} />{when}</div>
            <div className="tt-kv"><span>Платить</span><b>{payer.toLowerCase()}</b></div>
            <div className="tt-kv"><span>{data?.prepaid ? "Післяплата" : COD[p!.cod_mode as keyof typeof COD] ?? "Післяплата"}</span><b>{data?.prepaid || p!.cod_mode === "none" ? "немає" : `${money(p!.cod_amount)} ₴`}</b></div>
            {data?.cod_commission != null && p!.cod_mode !== "none" && <div className="tt-kv"><span>Комісія НП</span><b>≈ {money(data.cod_commission)} ₴</b></div>}
            <div className="tt-kv"><span>Оголошена вартість</span><b>{money(p!.declared_cost)} ₴</b></div>
            <i className="tt-sep" />
            {afterList}
            <span className="spacer" />
            {err && <p className="wz-err" role="alert"><CircleAlert size={15} />{err}</p>}
            {button}
            <p className="tt-note" title={codText}>Вартість рахує НП за тарифом — остаточна буде в ТТН</p>
          </aside>
        </div>
      )}
    </Window>
  );
}

function Skeleton() {
  return <div className="skel-rows">{[0, 1, 2, 3, 4].map((i) => <div key={i} className="skel-row"><span className="skel" /></div>)}</div>;
}

function Switch({ on, onClick, icon, children, disabled, title }: { on: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode; disabled?: boolean; title?: string }) {
  return (
    <button type="button" role="switch" aria-checked={on} className="tt-sw" disabled={disabled} title={title} onClick={onClick}>
      {icon}<span>{children}</span><i className={`tgl${on ? " on" : ""}`} aria-hidden />
    </button>
  );
}

// ======================================================================== екран «Готово»
function Done({ o, after, eta, onClose }: { o: Created; after: After; eta?: string | null; onClose: () => void }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [reg, setReg] = useState(o.np_registry_ref || "");
  const errs = o.after_errors ?? [];
  const smsErr = errs.some((e) => /sms|шаблон/i.test(e));
  const [sms, setSms] = useState(after.send_sms && meta.sms_ready && !smsErr);
  const status = meta.statuses.find((s) => s.id === o.status_id);
  const run = useMutation({
    mutationFn: (what: "registry" | "sms") => api.post<{ number?: string | null }>(`/orders/${o.id}/${what === "sms" ? "sms-ttn" : "registry"}`),
    onSuccess: (r, what) => {
      if (what === "registry") { setReg(r.number || "так"); toast("Додано в реєстр НП"); } else { setSms(true); toast("SMS з ТТН поставлено в чергу"); }
      qc.invalidateQueries({ queryKey: ["order", o.id] });
    },
    onError: (e) => toast(errText(e), "error"),
  });
  const ok = useRef<HTMLButtonElement>(null);
  useEffect(() => { ok.current?.focus(); }, []);
  const where = [o.city_name, o.warehouse_name === "Адресна доставка" ? o.address : o.warehouse_name].filter(Boolean).join(", ");
  return (
    <div className="tt-ok">
      <span className="tt-ok-ic"><Check size={40} strokeWidth={2.6} /></span>
      <h2>ТТН створено</h2>
      <div className="tt-num"><span className="np-badge lg">НП</span><b>{ttnFmt(o.ttn)}</b>
        <button type="button" className="tt-copy" aria-label="Скопіювати номер" onClick={() => { navigator.clipboard?.writeText(o.ttn); toast("Номер ТТН скопійовано"); }}><Copy size={17} /></button></div>
      <p className="tt-where-l">{[where, eta && `доставка ${dayText(eta).split(",")[0]}`, Number(o.delivery_cost) > 0 && `≈ ${money(o.delivery_cost)} ₴`].filter(Boolean).join(" · ")}</p>
      {status && <div className="tt-st">Статус замовлення: <StatusPill status={status} /></div>}
      {errs.filter((e) => !(smsErr && /sms|шаблон/i.test(e))).map((e) => <p key={e} className="wz-note warn"><CircleAlert size={15} /><span>{e}</span></p>)}
      <div className="tt-acts">
        <button type="button" className="tt-act" onClick={() => printLabel(o.id, toast)}>
          <span className="sq t-blue"><Printer size={18} /></span><span><b>{after.print_label ? "Друкувати ще раз" : "Друкувати наклейку"}</b><small>100 × 100 мм</small></span></button>
        <button type="button" className={`tt-act${reg ? " done" : ""}`} disabled={!!reg || run.isPending} onClick={() => run.mutate("registry")}>
          <span className="sq t-green">{reg ? <CircleCheck size={18} /> : <ListChecks size={18} />}</span><span><b>{reg ? "Додано в реєстр" : "Додати в реєстр"}</b><small>{reg && reg !== "так" ? reg : "на сьогодні"}</small></span></button>
        <button type="button" className={`tt-act${sms ? " done" : ""}`} disabled={sms || !meta.sms_ready || run.isPending} title={meta.sms_ready ? undefined : "SMS не підключено"} onClick={() => run.mutate("sms")}>
          <span className="sq t-purple">{sms ? <CircleCheck size={18} /> : <MessageSquare size={18} />}</span><span><b>{sms ? "SMS із ТТН у черзі" : "Надіслати SMS із ТТН"}</b><small>{meta.sms_ready ? "покупцю" : "SMS не підключено"}</small></span></button>
        <button type="button" className="tt-act" onClick={() => { navigator.clipboard?.writeText(o.ttn); toast("Номер ТТН скопійовано"); }}>
          <span className="sq t-gray"><Copy size={18} /></span><span><b>Скопіювати номер</b><small>у буфер обміну</small></span></button>
      </div>
      <button ref={ok} type="button" className="btn primary tt-go" onClick={onClose}>Готово<kbd>Enter</kbd></button>
    </div>
  );
}

// ======================================================================== довідник НП: місто, вулиця (пошук), відділення (список)
function NpSearch({ kind, label, cityRef, value, refValue, placeholder, icon, accountId, onPick, onType }: {
  kind: "cities" | "streets"; label: string; cityRef?: string; value: string; refValue: string; placeholder: string; icon: React.ReactNode;
  accountId?: number | ""; onPick: (o: Opt) => void; onType: (t: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const dq = useDebounced(value, 250);
  const need = kind === "streets" && !cityRef;
  const enabled = open && !need && dq.trim().length >= 2 && !refValue;
  const q = useQuery({
    queryKey: ["np", kind, cityRef, dq], enabled, retry: false,
    queryFn: () => api.get<{ ok: boolean; items?: Opt[]; error?: string }>(`/np/${kind}${qs({ q: dq, city_ref: cityRef, np_account_id: accountId || undefined })}`),
  });
  const items = q.data?.items ?? [];
  const pick = (o?: Opt) => { if (o) { onPick(o); setOpen(false); } };
  return (
    <div className="fbox tt-search">
      <span className="wz-lb">{label}</span>
      <span className={`wz-big tt-in${refValue ? " ok" : ""}${open ? " focus" : ""}`}>
        {icon}
        <input value={value} placeholder={need ? "Спершу оберіть місто" : placeholder} disabled={need}
          onChange={(e) => { onType(e.target.value); setOpen(true); setHl(0); }} onFocus={(e) => { setOpen(true); e.target.select(); }} onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (!open || !items.length) return;
            if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % items.length); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + items.length) % items.length); }
            else if (e.key === "Enter") { e.preventDefault(); pick(items[hl]); }
            else if (e.key === "Escape") { e.stopPropagation(); setOpen(false); }
          }} aria-label={label} autoComplete="off" />
        {refValue && <CircleCheck size={17} className="tt-in-ok" aria-label="З довідника НП" />}
      </span>
      {open && enabled && (
        <div className="pop np-pop" role="listbox">
          {q.isFetching && !items.length && <div className="note-empty">Пошук…</div>}
          {q.data && !q.data.ok && <div className="note-empty">{q.data.error}</div>}
          {q.data?.ok && !items.length && !q.isFetching && <div className="note-empty">Нічого не знайдено</div>}
          {items.slice(0, 30).map((o, i) => (
            <button key={o.ref} type="button" role="option" aria-selected={o.ref === refValue} className={`pop-item np-opt${i === hl ? " hl" : ""}`}
              onMouseDown={(e) => { e.preventDefault(); pick(o); }} onMouseEnter={() => setHl(i)}>
              <MapPin size={15} /><span className="ell" style={{ flex: 1 }}>{o.label || o.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Відділення або поштомати міста — список одразу під пошуком (номер, адреса, ліміт ваги), вибране підсвічене. */
function WarehouseList({ cityRef, way, value, onPick }: { cityRef: string; way: Way; value: { name: string; ref: string }; onPick: (o: Opt) => void }) {
  const [q, setQ] = useState("");
  const dq = useDebounced(q.trim(), 250);
  const res = useQuery({
    queryKey: ["np", "warehouses", cityRef, dq], enabled: !!cityRef, retry: false, placeholderData: (prev) => prev,
    queryFn: () => api.get<{ ok: boolean; items?: Opt[]; error?: string }>(`/np/warehouses${qs({ city_ref: cityRef, q: dq })}`),
  });
  const all = useMemo(() => (res.data?.items ?? []).filter((o) => (way === "postomat" ? o.kind === "postomat" : o.kind !== "postomat")), [res.data, way]);
  const local = q.trim().toLowerCase();
  const items = local && !dq ? all.filter((o) => o.name.toLowerCase().includes(local)) : all;
  const list = useRef<HTMLDivElement>(null);
  useEffect(() => { list.current?.querySelector<HTMLElement>("[aria-selected=true]")?.scrollIntoView({ block: "nearest" }); }, [items.length]);
  const word = way === "postomat" ? "Поштомат" : "Відділення";
  return (
    <div className="fbox tt-search">
      <span className="wz-lb">{word}</span>
      <span className={`wz-big tt-in${value.ref ? " ok" : ""}`}>
        <Search size={18} />
        <input value={q} disabled={!cityRef} placeholder={!cityRef ? "Спершу оберіть місто" : value.ref ? value.name.split(":")[0] : "Номер або вулиця"} onChange={(e) => setQ(e.target.value)}
          aria-label={`Пошук: ${word.toLowerCase()}`} autoComplete="off"
          onKeyDown={(e) => { if (e.key === "Enter" && items[0]) { e.preventDefault(); onPick(items[0]); setQ(""); } }} />
        {cityRef && res.data?.ok && <small className="muted tt-cnt">{items.length} у місті</small>}
      </span>
      {cityRef && (
        <div className="tt-whs" role="listbox" aria-label={word} ref={list}>
          {res.isFetching && !items.length && <div className="note-empty">Завантажую…</div>}
          {res.data && !res.data.ok && <div className="note-empty">{res.data.error}</div>}
          {res.data?.ok && !items.length && !res.isFetching && <div className="note-empty">Нічого не знайдено</div>}
          {items.map((o) => {
            const [n, ...rest] = (o.label || o.name).split(":");
            return (
              <button key={o.ref} type="button" role="option" aria-selected={o.ref === value.ref} className={`tt-wh${o.ref === value.ref ? " on" : ""}`} onClick={() => { onPick(o); setQ(""); }}>
                <span className="tt-wh-t"><b>{n}</b>{o.max_weight ? <span className="tt-tag">до {o.max_weight} кг</span> : null}{rest.length > 0 && <small>{rest.join(":").trim()}</small>}</span>
                <i className="rd" aria-hidden />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
