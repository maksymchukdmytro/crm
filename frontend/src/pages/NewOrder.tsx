// Нове замовлення покроково (макети docs/design/wizard-ttn, рішення власника 31.10 — «варіант A»):
// 1 телефон → ПІБ (покупець з бази підставляється сам) · 2 товар · 3 вид оплати великими значками · 4 доставка
// (НП: «Створити ТТН» або «Ввести готову ТТН»; інші перевізники — лише номер) · 5 джерело й деталі.
// Поточний крок — по центру, великі поля, «Далі» (Enter). Чернетка зберігається в браузері сама й відновлюється.
// На ПК — біла картка по центру; на телефоні — на весь екран зі смугою прогресу й кнопками під пальцем.
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRight, Ban, Check, ChevronDown, ChevronLeft, ChevronRight, CircleAlert, CircleCheck, LayoutGrid, Package, Plus, ReceiptText,
  ScanBarcode, Search, Store, Truck, X,
} from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money, num } from "../lib/format";
import type { Customer, Order } from "../lib/types";
import { UaPhone, Window } from "../components/ui";
import { SelectPick } from "../components/marks";
import { flag, PayIcon } from "../components/payicons";
import { EXTRA, UTM, payload, toForm, type Form } from "./card/state";
import { Goods } from "./card/Goods";
import { digits, plural, shortDate } from "./card/util";

// доставка — останній крок: «Створити й оформити ТТН» одразу веде у вікно ТТН (рішення власника 31.10)
const STEPS = ["Покупець", "Товар", "Оплата", "Деталі", "Доставка"] as const;
const DRAFT = "crm-new-order-draft-2";
const USAGE = "crm-pay-usage";
const KIND_TEXT: Record<string, string> = { cod: "післяплата", partial: "передоплата + решта", prepaid: "повна оплата" };
const COD_TEXT: Record<string, string> = { control: "контроль оплати", backward: "грошовий переказ", none: "без післяплати" };

type Lookup = {
  found: boolean; error: string; number: string; status: string; city_name: string; city_ref: string; warehouse_name: string; warehouse_ref: string;
  cost: number; cod_amount: number; cod_kind: string; recipient: string; phone_match: boolean | null; eta: string | null;
};
type Draft = { form: Form; step: number; mode: "create" | "ready"; at: number };

function readJson<T>(key: string, fallback: T): T {
  try { const v = localStorage.getItem(key); return v ? (JSON.parse(v) as T) : fallback; } catch { return fallback; }
}
function writeJson(key: string, v: unknown) {
  try { if (v === null) localStorage.removeItem(key); else localStorage.setItem(key, JSON.stringify(v)); } catch { /* приватне вікно */ }
}
const ttnFmt = (v: string) => digits(v).slice(0, 14).replace(/^(\d{2})(\d{0,4})(\d{0,4})(\d{0,4}).*/, (_, a, b, c, d) => [a, b, c, d].filter(Boolean).join(" "));

export default function NewOrder({ onClose, onCreated }: { onClose: () => void; onCreated: (o: Order, wantTtn: boolean) => void }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [sp] = useSearchParams();
  const fromId = Number(sp.get("from") || 0);
  const byCode = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.code, s])), [meta.statuses]);
  const newStatus = (byCode.unsorted?.active ? byCode.unsorted : byCode.new)?.id ?? meta.statuses[0]?.id;

  // чернетка: відновлюємо, якщо замовлення починається «з нуля» (не копія іншого й не з номера)
  const saved = useMemo(() => (fromId || sp.get("phone") ? null : readJson<Draft | null>(DRAFT, null)), []); // eslint-disable-line react-hooks/exhaustive-deps
  const fresh = saved && Date.now() - saved.at < 3 * 86400_000 && (digits(saved.form.phone).length > 3 || saved.form.items.length > 0) ? saved : null;
  const [form, setForm] = useState<Form>(() => fresh?.form ?? {
    ...toForm(sp.get("phone") ? { phone: sp.get("phone")! } : undefined, newStatus),
    manager_id: meta.managers.some((m) => m.id === meta.user.id) ? meta.user.id : "",  // менеджер — автоматично той, хто створює; адмін може змінити
  });
  const [step, setStep] = useState(fresh?.step ?? 0);
  const [reached, setReached] = useState(fresh?.step ?? 0);
  const [mode, setMode] = useState<"create" | "ready">(fresh?.mode ?? "create");
  const [restored, setRestored] = useState(!!fresh);
  const [err, setErr] = useState("");
  const set = (patch: Partial<Form>) => { setErr(""); setForm((f) => ({ ...f, ...patch })); };

  // нове замовлення цьому покупцю (?from=…): покупець і адреса — з того замовлення, одразу до товару
  const { data: source } = useQuery({ queryKey: ["order", fromId], queryFn: () => api.get<Order>(`/orders/${fromId}`), enabled: !!fromId });
  useEffect(() => {
    if (!source) return;
    setForm(toForm({ country: source.country, office_id: source.office_id, source_id: source.source_id, legal_entity_id: source.legal_entity_id,
      customer_name: source.customer_name, phone: source.phone, email: source.email, delivery_method: source.delivery_method, np_account_id: source.np_account_id,
      city_name: source.city_name, city_ref: source.city_ref, warehouse_name: source.warehouse_name, warehouse_ref: source.warehouse_ref,
      address: source.address, postcode: source.postcode }, newStatus));
    setStep(1); setReached(1);
  }, [source]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { writeJson(DRAFT, { form, step, mode, at: Date.now() } satisfies Draft); }, [form, step, mode]);

  // ---------------- суми
  const subtotal = form.items.reduce((s, i) => s + num(i.price) * (i.qty || 0), 0);
  const total = Math.max(subtotal - num(form.discount), 0);
  const method = meta.payment_methods.find((m) => m.id === form.payment_method_id);
  const kind = method?.kind ?? form.payment_type;
  const prepay = kind === "prepaid" ? total : kind === "partial" ? num(form.prepayment) : 0;
  const cod = Math.max(total - prepay, 0);
  const isNp = form.delivery_method === "novaposhta";
  const npReady = !!meta.carriers.novaposhta?.configured;
  const wantTtn = isNp && mode === "create" && npReady;

  // ---------------- перевірка кроку
  const tel = digits(form.phone);
  const problem = (i: number): string => {
    if (i === 0) {
      if (tel.length < (form.country === "UA" ? 12 : 9)) return "Вкажіть номер телефону";
      if (!form.customer_name.trim()) return "Вкажіть ПІБ покупця";
    }
    if (i === 1 && !form.items.some((x) => x.name.trim())) return "Додайте хоча б один товар";
    if (i === 2 && meta.payment_methods.length && !form.payment_method_id) return "Оберіть, як покупець оплачує";
    return "";
  };
  const go = (i: number) => { setErr(""); setStep(i); setReached((r) => Math.max(r, i)); };
  const next = () => {
    const p = problem(step);
    if (p) { setErr(p); return; }
    if (step < STEPS.length - 1) go(step + 1);
  };

  const create = useMutation({
    mutationFn: (ttn: boolean) => {
      for (let i = 0; i < STEPS.length; i++) { const p = problem(i); if (p) { go(i); throw new Error(p); } }
      const f = isNp && mode === "create" ? { ...form, ttn: "" } : form;
      return api.post<Order>("/orders", payload(f)).then((o) => ({ o, ttn }));
    },
    onSuccess: ({ o, ttn }) => {
      writeJson(DRAFT, null);
      if (form.payment_method_id) {
        const u = readJson<Record<string, number>>(USAGE, {});
        u[form.payment_method_id] = (u[form.payment_method_id] ?? 0) + 1;
        writeJson(USAGE, u);
      }
      qc.setQueryData(["order", o.id], o);
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["counters"] });
      toast(`Замовлення №${o.id} створено`);
      onCreated(o, ttn);
    },
    onError: (e) => setErr(errText(e)),
  });
  const last = step === STEPS.length - 1;

  // Enter — далі (поле пошуку товару й коментар Enter забирають собі), Ctrl ⏎ — створити
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || e.defaultPrevented || e.isComposing) return;
      const t = e.target as HTMLElement;
      if (t.tagName === "TEXTAREA" || (t.tagName === "BUTTON" && t.getAttribute("role") !== "radio") || t.closest(".pop, .menu-pop, .ac-list")) return;
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) { if (!create.isPending) create.mutate(wantTtn); return; }
      if (last) { if (!create.isPending) create.mutate(wantTtn); } else next();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const startOver = () => {
    writeJson(DRAFT, null);
    setForm(toForm(undefined, newStatus)); setStep(0); setReached(0); setMode("create"); setRestored(false); setErr("");
  };

  const head = (
    <div className="wz-head">
      <button type="button" className="rb m-only" aria-label="Закрити" onClick={onClose}><X size={20} /></button>
      <div className="wz-title"><b>Нове замовлення</b><small className="m-only">Крок {step + 1} з {STEPS.length} · {STEPS[step]}</small></div>
      <button type="button" className="wz-x d-only" aria-label="Закрити (Esc)" title="Закрити — чернетка збережеться" onClick={onClose}><X size={17} /></button>
      <div className="wz-prog m-only" aria-hidden>{STEPS.map((_, i) => <i key={i} className={i < step ? "ok" : i === step ? "cur" : ""} />)}</div>
      <nav className="wz-rail d-only" aria-label="Кроки">
        {STEPS.map((n, i) => (
          <span key={n} className="wz-rs">
            {i > 0 && <i className={`wz-ln${i <= step ? " ok" : ""}`} />}
            <button type="button" className={`wz-dot${i < step ? " ok" : i === step ? " cur" : ""}`} disabled={i > reached || i === step}
              aria-current={i === step ? "step" : undefined} onClick={() => go(i)}>
              <i>{i < step ? <Check size={13} strokeWidth={3} /> : i + 1}</i>{n}
            </button>
          </span>
        ))}
      </nav>
    </div>
  );

  const draftLine = (
    <span className="wz-draft">
      <ReceiptText size={14} aria-hidden />
      {last && !restored ? <>Разом <b>{money(total)} ₴</b></> : restored ? <>Чернетку відновлено · <button type="button" className="link-btn" onClick={startOver}>почати заново</button></>
        : <>Чернетка · <b>{form.items.length ? `${money(total)} ₴` : "товарів ще немає"}</b> · зберігається сама</>}
    </span>
  );
  const footer = (
    <div className={`wz-foot${last ? " last" : ""}`}>
      {err && <p className="wz-err" role="alert"><CircleAlert size={15} />{err}</p>}
      <div className="wz-btns">
        {step > 0 && <button type="button" className="btn wz-back" onClick={() => go(step - 1)} aria-label="Назад"><ChevronLeft size={20} /><span>Назад</span></button>}
        <span className="spacer" />
        {draftLine}
        {last ? (<>
          {wantTtn && <button type="button" className="btn wz-alt" disabled={create.isPending} onClick={() => create.mutate(false)}>Створити без ТТН</button>}
          <button type="button" className="btn primary wz-next" disabled={create.isPending} onClick={() => create.mutate(wantTtn)}>
            {wantTtn ? <><Truck size={18} />{create.isPending ? "Створюю…" : "Створити й оформити ТТН"}</> : <><Check size={18} />{create.isPending ? "Створюю…" : `Створити · ${money(total)} ₴`}</>}
            <kbd>Ctrl ⏎</kbd>
          </button>
        </>) : (
          <button type="button" className="btn primary wz-next" onClick={next}>Далі<ChevronRight size={19} /><kbd>Enter</kbd></button>
        )}
      </div>
    </div>
  );

  return (
    <Window size="md" className="wz" onClose={onClose} head={head} footer={footer} label="Нове замовлення" bodyClass="wz-body">
      <div className="wz-step" key={step}>
        {step === 0 && <StepCustomer form={form} set={set} />}
        {step === 1 && <StepGoods form={form} set={set} subtotal={subtotal} total={total} />}
        {step === 2 && <StepPayment form={form} set={set} total={total} cod={cod} isNp={isNp} />}
        {step === 4 && <StepDelivery form={form} set={set} mode={npReady ? mode : "ready"} setMode={setMode} npReady={npReady} cod={cod} codKind={method?.np_cod ?? ""} />}
        {step === 3 && <StepDetails form={form} set={set} />}
      </div>
    </Window>
  );
}

function Q({ title, sub }: { title: string; sub: string }) {
  return <div className="wz-q"><h2>{title}</h2><p>{sub}</p></div>;
}

// ======================================================================== 1. Телефон, потім ПІБ
function StepCustomer({ form, set }: { form: Form; set: (p: Partial<Form>) => void }) {
  const meta = useMeta();
  const tel = digits(form.phone);
  const full = tel.length >= (form.country === "UA" ? 12 : 9);
  const dq = useDebounced(full ? tel : "", 250);
  const [auto, setAuto] = useState(false);
  const [email, setEmail] = useState(!!form.email);
  const { data } = useQuery({
    queryKey: ["cust-by-phone", dq], enabled: dq.length >= 9, staleTime: 60_000, retry: false,
    queryFn: () => api.get<{ rows: Customer[] }>(`/customers${qs({ q: dq.slice(-9), limit: 5 })}`),
  });
  const c = full ? data?.rows.find((r) => digits(r.phone).endsWith(tel.slice(-9)) || digits(r.phone2 ?? "").endsWith(tel.slice(-9))) : undefined;
  useEffect(() => {
    if (c && !form.customer_name.trim()) { set({ customer_name: c.name, email: form.email || c.email }); setAuto(true); }
  }, [c?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const done = (c?.delivered ?? 0) + (c?.refused ?? 0);
  return (<>
    <Q title="Хто замовляє?" sub="Почніть з телефону — якщо покупець уже є, ПІБ підставиться сам" />
    <label className="wz-lb" htmlFor="wz-phone">Телефон</label>
    <div className="wz-big wz-phone">
      <span className="ph-flag" aria-hidden>{flag(form.country)}</span>
      <select className="ph-country" value={form.country} onChange={(e) => set({ country: e.target.value })} aria-label="Країна">
        {Object.entries(meta.countries).map(([cc, n]) => <option key={cc} value={cc} title={n}>{cc} · {n}</option>)}
      </select>
      <UaPhone id="wz-phone" value={form.phone} country={form.country} onChange={(v) => { set({ phone: v }); setAuto(false); }} aria-label="Телефон" autoFocus />
    </div>
    {c && (c.blacklisted ? (
      <div className="wz-note bad"><Ban size={16} /><span><b>Чорний список.</b> {c.blacklist_reason || "Причину не вказано"}</span></div>
    ) : (
      <div className="wz-note ok"><CircleCheck size={16} /><span>Покупець уже є: <b>{c.orders} {plural(c.orders, "замовлення", "замовлення", "замовлень")}
        {done > 0 && c.buyout_rate != null ? ` · викуп ${Math.round(c.buyout_rate)}%` : ""}</b>{c.last_order_at && ` · останнє ${shortDate(c.last_order_at)}`}</span></div>
    ))}
    <label className="wz-lb" htmlFor="wz-name">ПІБ{auto && <span className="wz-from">· підставлено з бази</span>}</label>
    <input id="wz-name" className="wz-big" value={form.customer_name} placeholder="Прізвище ім'я по батькові — у будь-якому порядку"
      onChange={(e) => { set({ customer_name: e.target.value }); setAuto(false); }} autoComplete="off" />
    {email || form.email
      ? <><label className="wz-lb" htmlFor="wz-email">Email</label>
        <input id="wz-email" className="wz-big" type="email" value={form.email} autoFocus={!form.email} onChange={(e) => set({ email: e.target.value })} placeholder="name@example.com" /></>
      : <button type="button" className="wz-add" onClick={() => setEmail(true)}><Plus size={15} />Email</button>}
    <SourceChips form={form} set={set} />
  </>);
}

/** Джерело замовлення — чипами (найпопулярніші першими, решта — «Ще»); той самий вибір і у «Новий лід». */
export function SourceChips({ form, set }: { form: Pick<Form, "source_id">; set: (p: { source_id: number | "" }) => void }) {
  const meta = useMeta();
  const [more, setMore] = useState(false);
  const sources = meta.order_sources;
  const TOP = 7;
  if (!sources.length) return null;
  const shown = more ? sources : sources.slice(0, TOP);
  const cur = sources.find((x) => x.id === form.source_id);
  const chips = cur && !shown.includes(cur) ? [...shown, cur] : shown;
  return (<>
    <div className="wz-lb wz-lb-src">Джерело</div>
    <div className="wz-chips" role="radiogroup" aria-label="Джерело">
      {chips.map((x) => (
        <button key={x.id} type="button" role="radio" aria-checked={x.id === form.source_id} className={`wz-chip${x.id === form.source_id ? " on" : ""}`}
          onClick={() => set({ source_id: x.id === form.source_id ? "" : x.id })}>{x.name}</button>
      ))}
      {!more && sources.length > TOP && <button type="button" className="wz-chip dash" onClick={() => setMore(true)}>Ще {sources.length - TOP}</button>}
    </div>
  </>);
}

// ======================================================================== 2. Товар
function StepGoods({ form, set, subtotal, total }: { form: Form; set: (p: Partial<Form>) => void; subtotal: number; total: number }) {
  const meta = useMeta();
  return (<>
    <Q title="Що замовляє?" sub="Назва, артикул або штрихкод · ↑↓ і Enter — додати" />
    <div className="wz-goods">
      <Goods items={form.items} products={meta.products} onChange={(items) => set({ items })} />
    </div>
    {form.items.length > 0 && (
      <div className="wz-total">
        <label className="wz-disc">Знижка<input value={form.discount} inputMode="decimal" placeholder="0" aria-label="Знижка, ₴"
          onChange={(e) => set({ discount: e.target.value.replace(",", ".").replace(/[^\d.]/g, "") })} /> ₴</label>
        <span>Разом <b>{money(total)} ₴</b>{subtotal !== total && <small> з {money(subtotal)} ₴</small>}</span>
      </div>
    )}
  </>);
}

// ======================================================================== 3. Вид оплати — великі значки, найчастіші першими, пошук серед усіх
function StepPayment({ form, set, total, cod, isNp }: { form: Form; set: (p: Partial<Form>) => void; total: number; cod: number; isNp: boolean }) {
  const meta = useMeta();
  const [q, setQ] = useState("");
  const [all, setAll] = useState(false);
  const usage = useMemo(() => readJson<Record<string, number>>(USAGE, {}), []);
  const methods = useMemo(() => [...meta.payment_methods].sort((a, b) => (usage[b.id] ?? 0) - (usage[a.id] ?? 0) || a.sort - b.sort || a.id - b.id),
    [meta.payment_methods, usage]);
  const LIMIT = 11;
  const low = q.trim().toLowerCase();
  let shown = low ? methods.filter((m) => m.name.toLowerCase().includes(low)) : all ? methods : methods.slice(0, LIMIT);
  const sel = methods.find((m) => m.id === form.payment_method_id);
  if (sel && !shown.includes(sel) && !low) shown = [...shown.slice(0, LIMIT - 1), sel];
  const rest = methods.length - shown.length;
  const kind = sel?.kind ?? form.payment_type;
  const codKind = sel?.np_cod || (kind === "prepaid" ? "none" : "");
  return (<>
    <Q title="Як оплачує?" sub="Від виду оплати залежить, що піде в ТТН · ваші найчастіші — першими" />
    {methods.length > LIMIT && (
      <label className="wz-big wz-search"><Search size={18} aria-hidden />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Знайти серед ${methods.length} видів оплати`} aria-label="Пошук виду оплати" /></label>
    )}
    <div className="wz-pays" role="radiogroup" aria-label="Вид оплати">
      {shown.map((m) => (
        <button key={m.id} type="button" role="radio" aria-checked={m.id === form.payment_method_id} className={`wz-pt${m.id === form.payment_method_id ? " on" : ""}`}
          onClick={() => set({ payment_method_id: m.id, payment_type: m.kind })}>
          <span className="wz-pic"><PayIcon icon={m.icon} image={m.image} size={30} /></span>
          <span className="wz-pn">{m.name}</span><small>{KIND_TEXT[m.kind] ?? ""}</small>
        </button>
      ))}
      {!low && !all && rest > 0 && (
        <button type="button" className="wz-pt more" onClick={() => setAll(true)}>
          <span className="wz-pic"><LayoutGrid size={24} /></span><span className="wz-pn">Усі види</span><small>ще {rest}</small>
        </button>
      )}
      {low && !shown.length && <p className="wz-empty">Нічого не знайдено</p>}
    </div>
    {kind === "partial" && (
      <div className="wz-row2">
        <div><label className="wz-lb" htmlFor="wz-prepay">Сума передоплати</label>
          <span className="wz-big wz-money"><input id="wz-prepay" value={form.prepayment} inputMode="decimal" placeholder="0"
            onChange={(e) => set({ prepayment: e.target.value.replace(",", ".").replace(/[^\d.]/g, "") })} /><span>₴</span></span></div>
        <div className="wz-hint-box">Решта <b>{money(cod)} ₴</b> — при отриманні</div>
      </div>
    )}
    {isNp && sel && (
      <div className="wz-ttnline"><ArrowUpRight size={15} />У ТТН піде: <b>{cod > 0 ? `${COD_TEXT[codKind] ?? "післяплата"} · ${money(cod)} ₴` : `без післяплати${total ? " — оплачено" : ""}`}</b></div>
    )}
  </>);
}

// ======================================================================== 4. Доставка
function StepDelivery({ form, set, mode, setMode, npReady, cod, codKind }: {
  form: Form; set: (p: Partial<Form>) => void; mode: "create" | "ready"; setMode: (m: "create" | "ready") => void; npReady: boolean; cod: number; codKind: string;
}) {
  const meta = useMeta();
  const dm = form.delivery_method;
  const opts: { key: string; method: string; acc: number | ""; name: string; sub: string }[] = [];
  Object.entries(meta.delivery_methods).forEach(([k, n]) => {
    if (k === "novaposhta" && meta.np_accounts.length > 1) meta.np_accounts.forEach((a) => opts.push({ key: `np:${a.id}`, method: k, acc: a.id, name: n, sub: a.name }));
    else opts.push({ key: k, method: k, acc: "", name: n, sub: k === "novaposhta" ? meta.np_accounts[0]?.name ?? "" : meta.carriers[k]?.beta ? "бета" : "" });
  });
  const cur = dm === "novaposhta" && meta.np_accounts.length > 1 ? `np:${form.np_account_id || meta.np_accounts.find((a) => a.is_default)?.id || meta.np_accounts[0]?.id}` : dm;
  const pick = (o: (typeof opts)[number]) => set({
    delivery_method: o.method, np_account_id: o.acc,
    ...(o.method !== dm ? { ttn: "", city_name: "", city_ref: "", warehouse_name: "", warehouse_ref: "" } : {}),
  });
  const icon = (m: string) => m === "novaposhta" ? <span className="np-badge lg">НП</span>
    : <span className={`sq ${m === "pickup" ? "t-gray" : m === "ukrposhta" ? "t-orange" : m === "meest" ? "t-purple" : "t-blue"}`}>{m === "pickup" ? <Store size={16} /> : m === "meest" ? <Package size={16} /> : <Truck size={16} />}</span>;
  return (<>
    <Q title="Як доставити?" sub="Останній крок — далі створюємо замовлення й одразу ТТН" />
    <div className="wz-carriers" role="radiogroup" aria-label="Перевізник">
      {opts.map((o) => (
        <button key={o.key} type="button" role="radio" aria-checked={o.key === cur} className={`wz-cr${o.key === cur ? " on" : ""}`} onClick={() => pick(o)}>
          {icon(o.method)}<span><b>{o.name}</b>{o.sub && <small>{o.sub}</small>}</span>
        </button>
      ))}
    </div>
    {dm === "novaposhta" && (<>
      <div className="wz-sub">ТТН Нової Пошти</div>
      <div className="wz-modes" role="radiogroup" aria-label="ТТН">
        <button type="button" role="radio" aria-checked={mode === "create"} disabled={!npReady} className={`wz-mode${mode === "create" ? " on" : ""}`} onClick={() => { setMode("create"); set({ ttn: "" }); }}>
          <span className="sq t-blue"><Truck size={17} /></span>
          <span><b>Створити ТТН</b><small>{npReady ? "після створення замовлення відкриється вікно ТТН: місто, відділення, платник" : "спершу додайте ключ НП у «Налаштування → Доставка»"}</small></span><i className="rd" /></button>
        <button type="button" role="radio" aria-checked={mode === "ready"} className={`wz-mode${mode === "ready" ? " on" : ""}`} onClick={() => setMode("ready")}>
          <span className={`sq ${mode === "ready" ? "t-blue" : "t-gray"}`}><ScanBarcode size={17} /></span>
          <span><b>Ввести готову ТТН</b><small>посилку вже оформили в кабінеті НП — лише вставте номер</small></span><i className="rd" /></button>
      </div>
      {mode === "ready" ? <ReadyTtn form={form} set={set} /> : (
        <div className="wz-ttnline grey"><Truck size={15} />{cod > 0 ? `Післяплата ${money(cod)} ₴ · ${COD_TEXT[codKind] ?? "післяплата"}` : "Без післяплати"} · береться з оплати</div>
      )}
    </>)}
    {dm !== "novaposhta" && dm !== "pickup" && dm !== "courier" && (<>
      <div className="wz-sub">ТТН · {meta.delivery_methods[dm]}</div>
      <label className="wz-lb" htmlFor="wz-num">Номер відправлення</label>
      <input id="wz-num" className="wz-big mono" value={form.ttn} onChange={(e) => set({ ttn: e.target.value.replace(/\s/g, "") })} placeholder="Можна додати пізніше" autoComplete="off" />
      <p className="wz-muted"><CircleAlert size={14} />Номер вводиться вручну, коли оформите посилку. Можна пропустити й додати пізніше в картці.</p>
    </>)}
    {dm === "courier" && (<>
      <div className="wz-sub">Адреса для кур'єра</div>
      <div className="wz-row2">
        <div><label className="wz-lb" htmlFor="wz-city">Місто</label><input id="wz-city" className="wz-big" value={form.city_name} onChange={(e) => set({ city_name: e.target.value })} /></div>
        <div><label className="wz-lb" htmlFor="wz-addr">Вулиця, будинок, квартира</label><input id="wz-addr" className="wz-big" value={form.address} onChange={(e) => set({ address: e.target.value })} /></div>
      </div>
    </>)}
    {dm === "pickup" && <p className="wz-muted"><Store size={14} />Покупець забере замовлення сам — ТТН не потрібна.</p>}
  </>);
}

/** «Ввести готову ТТН»: номер → пошук у НП (куди їде, вартість, післяплата, чи збігається телефон); місто й відділення — у замовлення. */
function ReadyTtn({ form, set }: { form: Form; set: (p: Partial<Form>) => void }) {
  const num14 = digits(form.ttn).length === 14 ? digits(form.ttn) : "";
  const dq = useDebounced(num14, 300);
  const { data, isFetching } = useQuery({
    queryKey: ["ttn-lookup", dq, form.np_account_id], enabled: !!dq, staleTime: 60_000, retry: false,
    queryFn: () => api.get<Lookup>(`/np/ttn-lookup${qs({ number: dq, phone: digits(form.phone), np_account_id: form.np_account_id || undefined })}`),
  });
  const applied = useRef("");
  useEffect(() => {
    if (!data?.found || applied.current === data.number) return;
    applied.current = data.number;
    if (data.city_name || data.warehouse_name) set({ city_name: data.city_name, city_ref: data.city_ref, warehouse_name: data.warehouse_name, warehouse_ref: data.warehouse_ref });
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
  return (<>
    <label className="wz-lb" htmlFor="wz-ttn">Номер ТТН</label>
    <input id="wz-ttn" className="wz-big mono wz-ttn" value={ttnFmt(form.ttn)} inputMode="numeric" placeholder="20 0000 0000 0000" autoFocus autoComplete="off"
      onChange={(e) => set({ ttn: digits(e.target.value).slice(0, 14) })} />
    {num14 && (isFetching && !data ? <div className="wz-note"><Search size={16} />Шукаю в Новій Пошті…</div>
      : data?.found ? (
        <div className={`wz-note ${data.phone_match === false ? "warn" : "ok"}`}>{data.phone_match === false ? <CircleAlert size={16} /> : <CircleCheck size={16} />}
          <span>Знайдено: <b>{[data.city_name, data.warehouse_name].filter(Boolean).join(", ") || data.status}</b>
            {data.cod_amount > 0 && ` · ${COD_TEXT[data.cod_kind] ?? "післяплата"} ${money(data.cod_amount)} ₴`}
            {data.phone_match === false ? " · телефон отримувача в ТТН інший" : data.phone_match ? " · отримувач збігається" : ""}</span></div>
      ) : data && <div className="wz-note warn"><CircleAlert size={16} /><span>{data.error || "ТТН не знайдено"} — номер усе одно збережеться в замовленні</span></div>)}
  </>);
}

// ======================================================================== 5. Джерело й деталі
function StepDetails({ form, set }: { form: Form; set: (p: Partial<Form>) => void }) {
  const meta = useMeta();
  const [extra, setExtra] = useState(false);
  const [utm, setUtm] = useState(false);
  const curSrc = meta.order_sources.find((s) => s.id === form.source_id);
  const office = meta.offices.find((o) => o.id === (curSrc?.office_id ?? form.office_id))?.name;
  const extras = EXTRA.map((f, i) => ({ f, i, name: meta.extra_fields[i] || `Поле ${i + 1}` })).filter((x) => meta.extra_on?.[x.i] ?? true);
  // вибір — таким самим меню, як у картці замовлення (SelectPick), а не системним списком
  const sel = (id: string, label: string, v: number | "", on: (v: number | "") => void, items: { id: number; name: string }[], empty: string, emptyHint?: string) => (
    <div><div className="wz-lb" id={`${id}-l`}>{label}</div>
      <SelectPick<number | ""> ariaLabel={label} value={v} onChange={on} className="wz-pick"
        options={[{ value: "", label: <span className="muted">{empty}</span>, hint: emptyHint }, ...items.map((x) => ({ value: x.id as number | "", label: x.name }))]} /></div>
  );
  const me = meta.managers.find((m) => m.id === meta.user.id);
  return (<>
    <Q title="Деталі замовлення" sub="Менеджер, юрособа й коментар — далі доставка" />
    <div className="wz-grid2">
      {meta.user.role === "admin" ? sel("wz-mgr", "Менеджер", form.manager_id, (v) => set({ manager_id: v }), meta.managers.map((m) => (m.id === meta.user.id ? { ...m, name: `${m.name} (ви)` } : m)),
        "Автоматично", "за правилом розподілу")
        : <div><div className="wz-lb">Менеджер</div><div className="wz-ro">{me?.name ?? meta.user.name} · ви</div></div>}
      <div><div className="wz-lb">Відділ</div><div className="wz-ro">{office ?? "за джерелом"}</div></div>
      {meta.legal_entities.length > 0
        ? sel("wz-le", "Юрособа", form.legal_entity_id, (v) => set({ legal_entity_id: v }), meta.legal_entities, meta.legal_entities.find((x) => x.is_default)?.name ?? "за замовчуванням")
        : null}
      {meta.marks.length > 0 ? sel("wz-mark", "Позначка", form.mark_id, (v) => set({ mark_id: v }), meta.marks, "без позначки") : null}
      <div className="wide"><label className="wz-lb" htmlFor="wz-cm">Коментар</label>
        <textarea id="wz-cm" className="wz-big wz-area" rows={2} value={form.comment} onChange={(e) => set({ comment: e.target.value })} placeholder="Що важливо знати складу чи кур'єру…" /></div>
    </div>
    <div className="wz-folds">
      {extras.length > 0 && <button type="button" className="wz-add" aria-expanded={extra} onClick={() => setExtra((x) => !x)}>{extras.length === 4 ? "Поля 1–4" : "Додаткові поля"}<ChevronDown size={14} className={extra ? "rot" : ""} /></button>}
      <button type="button" className="wz-add" aria-expanded={utm} onClick={() => setUtm((x) => !x)}>UTM і сайт<ChevronDown size={14} className={utm ? "rot" : ""} /></button>
    </div>
    {extra && <div className="wz-grid2">{extras.map(({ f, name }) => (
      <div key={f}><label className="wz-lb" htmlFor={`wz-${f}`}>{name}</label><input id={`wz-${f}`} className="wz-big sm" value={form[f]} onChange={(e) => set({ [f]: e.target.value } as Partial<Form>)} /></div>
    ))}</div>}
    {utm && <div className="wz-grid2">
      <div><label className="wz-lb" htmlFor="wz-site">Сайт</label><input id="wz-site" className="wz-big sm" value={form.site} onChange={(e) => set({ site: e.target.value })} /></div>
      {UTM.map((u) => <div key={u}><label className="wz-lb mono" htmlFor={`wz-${u}`}>{u}</label><input id={`wz-${u}`} className="wz-big sm" value={form[u]} onChange={(e) => set({ [u]: e.target.value } as Partial<Form>)} /></div>)}
    </div>}
  </>);
}
