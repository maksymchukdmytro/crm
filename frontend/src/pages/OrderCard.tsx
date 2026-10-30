// Картка замовлення (UI-DESIGN §5, макети 01 і 02): велике вікно поверх списку, дві колонки 4/12 + 8/12.
// Ліворуч Покупець → Оплата → Доставка, праворуч Товари, під ними Деталі й Підсумок. Історія — бічна панель під значком.
// Збереження автоматичне (0,8 с після введення, Ctrl S — одразу); «Створити ТТН», «Друк» і «Чек» спершу самі зберігають замовлення.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlarmClock, ArrowLeft, ArrowUpRight, Ban, Bell, Building2, Check, ChevronDown, CircleCheck, Copy, CreditCard, ExternalLink, FileText, History,
  Landmark, ListChecks, Lock, MessageCircle, MessageSquare, MoreHorizontal, Pencil, Phone, Plus, Printer, Receipt, RefreshCw, ScanBarcode,
  Send, ShieldCheck, Tag as TagIcon, Trash2, Truck, Wallet, X,
} from "lucide-react";
import { api, ApiError, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money, num } from "../lib/format";
import type { Order } from "../lib/types";
import {
  Block, Button, Checklist, IconButton, MenuButton, PayCheck, Segmented, SidePanel, StatusPill, Tag, UaPhone, Window, inField, useOutside, type CheckItem,
} from "../components/ui";
import { flag, PayLabel } from "../components/payicons";
import { IconPick, MarkIcon } from "../components/marks";
import TtnDialog from "./TtnDialog";
import { DOC_KINDS, KIND_OF, printDocument, type DocKind } from "../lib/docs";
import { EXTRA, UTM, payload, toForm, type Form } from "./card/state";
import { Goods, type GoodsHandle } from "./card/Goods";
import { dateTime, digits, plural, printLabel, shortDate } from "./card/util";

const TRACK = ["unsorted", "confirmed", "shipped", "arrived", "delivered"];
const BRANCH = ["refused", "returned", "cancelled"];
const CLOSED = ["delivered", "returned", "cancelled", "lead_refused", "duplicate"];
const SHIPPED = ["shipped", "arrived", "delivered", "refused", "returned"];
const STOCK_TEXT: Record<string, string> = { reserve: "товар буде зарезервовано", ship: "товар буде списано зі складу", return: "товар повернеться на залишок", release: "резерв буде знято" };
const COD_TEXT: Record<string, string> = { control: "контроль оплати", backward: "грошовий переказ", none: "без післяплати" };

// «Створити ТТН» у ще не створеному замовленні: спершу створюємо замовлення, а вікно ТТН відкриваємо вже в ньому
// (картка перемонтовується з новим id, тому номер переносимо через змінну модуля)
let ttnAfterCreate: number | null = null;

export default function OrderModal({ id, onClose, onOpen, ids }: { id: string; onClose: () => void; onOpen: (id: number) => void; ids?: number[] }) {
  return <OrderCard key={id} id={id} onClose={onClose} onOpen={onOpen} ids={ids} />;
}

function OrderCard({ id, onClose, onOpen, ids }: { id: string; onClose: () => void; onOpen: (id: number) => void; ids?: number[] }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const isNew = id === "new";
  const oid = isNew ? 0 : Number(id);
  const fromId = isNew ? Number(sp.get("from") || 0) : 0;
  const byCode = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.code, s])), [meta.statuses]);
  const newStatus = (window.location.pathname.includes("/leads") ? byCode.new : byCode.unsorted?.active ? byCode.unsorted : byCode.new)?.id ?? meta.statuses[0]?.id;
  const goods = useRef<GoodsHandle>(null);

  const { data: order, error, isLoading } = useQuery({ queryKey: ["order", oid], queryFn: () => api.get<Order>(`/orders/${oid}`), enabled: !isNew });
  const { data: source } = useQuery({ queryKey: ["order", fromId], queryFn: () => api.get<Order>(`/orders/${fromId}`), enabled: !!fromId });

  const [form, setForm] = useState<Form>(() => toForm(undefined, newStatus));
  const formRef = useRef(form);
  formRef.current = form;
  const [baseline, setBaseline] = useState("");
  const [version, setVersion] = useState("");
  const [saveState, setSaveState] = useState<"" | "saving" | "saved" | "error">("");
  const [ttnOpen, setTtnOpen] = useState(false);
  const [history, setHistory] = useState(false);
  const [unlocked, setUnlocked] = useState(false);
  const sentRef = useRef("");
  const wantTtnRef = useRef(false);
  const againRef = useRef(false);

  // заповнити форму (і оновлювати, якщо замовлення змінили інші, а ми нічого не редагували)
  useEffect(() => {
    if (isNew) {
      const f = source ? toForm({ country: source.country, office_id: source.office_id, source_id: source.source_id, legal_entity_id: source.legal_entity_id,
        customer_name: source.customer_name, phone: source.phone, email: source.email, delivery_method: source.delivery_method, city_name: source.city_name,
        city_ref: source.city_ref, warehouse_name: source.warehouse_name, warehouse_ref: source.warehouse_ref, address: source.address, postcode: source.postcode }, newStatus)
        : toForm(sp.get("phone") ? { phone: sp.get("phone")! } : undefined, newStatus);
      if (!fromId || source) { setForm(f); setBaseline(JSON.stringify(f)); }
      return;
    }
    if (!order || order.version === version) return;
    const dirtyNow = baseline !== "" && JSON.stringify(formRef.current) !== baseline;
    if (!dirtyNow || !version) {
      const f = toForm(order, newStatus);
      setForm(f); setBaseline(JSON.stringify(f)); setVersion(order.version);
    } else toast("Замовлення змінив інший користувач. Ваші зміни збережуться поверх.", "warn");
  }, [order, source]); // eslint-disable-line react-hooks/exhaustive-deps

  const dirty = baseline !== "" && JSON.stringify(form) !== baseline;
  const set = (patch: Partial<Form>) => setForm((f) => ({ ...f, ...patch }));
  const status = meta.statuses.find((s) => s.id === form.status_id);
  const code = status?.code ?? "";
  const closed = !isNew && CLOSED.includes(code) && !unlocked;
  const shippedLock = !isNew && SHIPPED.includes(code);

  // ---------------- підсумки
  const subtotal = form.items.reduce((s, i) => s + num(i.price) * (i.qty || 0), 0);
  const total = Math.max(subtotal - num(form.discount), 0);
  const method = meta.payment_methods.find((m) => m.id === form.payment_method_id);
  const kind = method?.kind ?? form.payment_type;
  const prepay = kind === "prepaid" ? total : kind === "partial" ? num(form.prepayment) : 0;
  const cod = Math.max(total - prepay, 0);

  // ---------------- збереження
  const save = useMutation({
    mutationFn: async (): Promise<Order> => {
      const snap = formRef.current;
      sentRef.current = JSON.stringify(snap);
      if (isNew) return api.post<Order>("/orders", payload(snap));
      return api.patch<Order>(`/orders/${oid}`, payload(snap, version || order?.version));
    },
    onMutate: () => setSaveState("saving"),
    onSuccess: (o) => {
      qc.setQueryData(["order", o.id], o);
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["counters"] });
      setVersion(o.version);
      setBaseline(sentRef.current);
      setSaveState("saved");
      if (isNew) {
        if (wantTtnRef.current) { wantTtnRef.current = false; ttnAfterCreate = o.id; }
        toast(`Замовлення №${o.id} створено`); onOpen(o.id);
      }
    },
    onError: (e) => {
      setSaveState("error");
      toast(errText(e), "error");
      if (e instanceof ApiError && e.status === 409) { setVersion(""); qc.invalidateQueries({ queryKey: ["order", oid] }); }
    },
    onSettled: () => { if (againRef.current) { againRef.current = false; setTimeout(() => saveNow(), 0); } },
  });
  const saveNow = useCallback(() => {
    if (save.isPending) { againRef.current = true; return; }
    if (JSON.stringify(formRef.current) === baseline && !isNew) return;
    save.mutate();
  }, [save, baseline, isNew]);
  const saveAsync = async () => { if (dirty || isNew) await save.mutateAsync(); };

  // автозбереження: 0,8 с після введення (нове замовлення — кнопкою «Створити», щоб не перебивати введення)
  useEffect(() => {
    if (!dirty || isNew || closed) return;
    const t = setTimeout(saveNow, 800);
    return () => clearTimeout(t);
  }, [form]); // eslint-disable-line react-hooks/exhaustive-deps

  const action = useMutation({
    mutationFn: async ({ path, method: m = "post", body }: { path: string; method?: "post" | "del"; body?: Record<string, unknown> }) => {
      await saveAsync();
      return m === "del" ? api.del<Order>(`/orders/${oid}${path}`) : api.post<Order>(`/orders/${oid}${path}`, body);
    },
    onSuccess: (o, vars) => {
      if (o && (o as Order).version) {
        qc.setQueryData(["order", o.id], o);
        const f = toForm(o, newStatus);
        setForm(f); setBaseline(JSON.stringify(f)); setVersion(o.version);
      } else qc.invalidateQueries({ queryKey: ["order", oid] });
      qc.invalidateQueries({ queryKey: ["orders"] });
      const msg: Record<string, string> = { "/track": "Статус доставки оновлено", "/take": "Замовлення ваше", "/comments": "Коментар додано",
        "/sms": "Повідомлення поставлено в чергу", "/sms-ttn": "SMS з ТТН поставлено в чергу", "/payments": "Оплату додано", "/receipts": "Чек створено",
        "/fiscalize": "Чек продажу створено", "/prepayment/confirm": "Передоплату підтверджено", "/registry": "Додано в реєстр НП" };
      toast(vars.method === "del" ? "ТТН видалено" : msg[vars.path] ?? "Готово");
    },
    onError: (e) => toast(errText(e), "error"),
  });

  const changeStatus = (sid: number, reasonId?: number) => {
    const s = meta.statuses.find((x) => x.id === sid);
    if (!s || sid === form.status_id) return;
    const acts = [STOCK_TEXT[s.stock_action ?? ""], s.code === "shipped" || s.code === "delivered" ? "SMS покупцю й чек — якщо налаштовано для статусу" : ""].filter(Boolean);
    if (acts.length && !window.confirm(`Статус «${s.name}»: ${acts.join("; ")}. Продовжити?`)) return;
    setForm((f) => ({ ...f, status_id: sid, reason_id: reasonId ?? f.reason_id }));
    setTimeout(() => (isNew ? null : saveNow()), 0);
  };

  // ---------------- клавіші: Ctrl S, Ctrl ⏎ (ТТН), H (історія), J / K
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); saveNow(); return; }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && (isNew || (order && !order.ttn)) && form.delivery_method === "novaposhta") { e.preventDefault(); openTtn(); return; }
      if (e.ctrlKey || e.metaKey || e.altKey || inField(e) || ttnOpen) return;
      const k = e.key.toLowerCase();
      if (k === "h" && !isNew) { e.preventDefault(); setHistory((x) => !x); }
      if ((k === "j" || k === "k") && ids?.length) {
        const i = ids.indexOf(oid);
        const next = ids[i + (k === "j" ? 1 : -1)];
        if (i >= 0 && next != null) { e.preventDefault(); if (dirty) saveNow(); onOpen(next); }
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const openTtn = async () => {
    if (save.isPending || action.isPending) return;
    if (isNew) {
      wantTtnRef.current = true;
      try { await save.mutateAsync(); } catch { wantTtnRef.current = false; }
      return;
    }
    await saveAsync();
    if (form.delivery_method === "novaposhta") setTtnOpen(true);
    else action.mutate({ path: "/ttn" });
  };
  // щойно створене кнопкою «Створити ТТН» — одразу відкрити вікно ТТН
  useEffect(() => {
    if (isNew || !order || ttnAfterCreate !== order.id) return;
    ttnAfterCreate = null;
    if (order.ttn) return;
    if (order.delivery_method === "novaposhta") setTtnOpen(true);
    else action.mutate({ path: "/ttn" });
  }, [order]); // eslint-disable-line react-hooks/exhaustive-deps

  const close = () => { if (dirty && !isNew) saveNow(); else if (dirty && isNew && !window.confirm("Замовлення ще не створено. Закрити без збереження?")) return; onClose(); };

  if (!isNew && (isLoading || !order || !baseline)) {
    return (
      <Window size="xl" onClose={onClose} label="Замовлення" head={<div className="oc-head"><IconButton icon={ArrowLeft} label="Назад" quiet onClick={onClose} /><span className="skel" style={{ width: 420 }} /></div>}>
        {error ? <div className="empty big"><h1>Не вдалося відкрити</h1><p>{errText(error)}</p></div> : <div className="oc-grid oc-loading">{[0, 1].map((i) => <div key={i} className="block"><span className="skel" /><span className="skel" /><span className="skel" /></div>)}</div>}
      </Window>
    );
  }

  const steps = isNew || code === "unsorted";
  const custDone = digits(form.phone).length >= 10 && !!form.customer_name.trim();
  const delivDone = !!(form.ttn || form.city_name || form.delivery_method === "pickup");

  const head = (
    <div className="oc-head">
      <IconButton icon={ArrowLeft} label="Назад (Esc)" quiet onClick={close} />
      {isNew ? <h2 className="oc-new-title">Нове замовлення</h2> : <StatusTrack statusId={form.status_id} onPick={changeStatus} disabled={closed} />}
      <div className="oc-head-acts">
        <span className={`oc-save-st ${saveState}`} aria-live="polite">
          {saveState === "saving" ? "Зберігаю…" : saveState === "error" ? "Не збережено" : dirty && !isNew ? "Є зміни" : saveState === "saved" ? "Збережено" : ""}
        </span>
        {order && <PrintMenu order={order} onBefore={saveAsync} onError={(m) => toast(m, "error")} />}
        {order && order.checkbox_ready && <CheckMenu order={order} busy={action.isPending} onReceipt={(k) => action.mutate({ path: "/receipts", body: { kind: k } })} />}
        <Button variant="primary" icon={Check} kbd="Ctrl S" disabled={save.isPending || closed} onClick={() => saveNow()}>{isNew ? "Створити" : "Зберегти"}</Button>
        {order && <RemindButton value={form.remind_at} onChange={(v) => { set({ remind_at: v }); }} />}
        {order && <IconButton icon={History} label="Історія (H)" count={(order.history?.length ?? 0) + (order.comments?.length ?? 0)} onClick={() => setHistory(true)} />}
        <IconButton icon={X} label="Закрити (Esc)" quiet onClick={close} />
      </div>
    </div>
  );

  return (
    <Window size="xl" onClose={close} head={head} label={isNew ? "Нове замовлення" : `Замовлення №${oid}`} bodyClass="oc-body">
      {closed && (
        <div className="oc-strip lock"><Lock size={15} /><span>Замовлення закрите — «{status?.name}». Зміни вимкнено, щоб не зачепити склад і оплати.</span>
          <button className="btn sm" onClick={() => setUnlocked(true)}><Pencil size={14} />Редагувати</button></div>
      )}
      <div className={`oc-grid${closed ? " ro" : ""}`}>
        {/* ======== ліва колонка ======== */}
        <div className="oc-left">
          <CustomerBlock order={order} form={form} set={set} isNew={isNew} step={steps ? { n: 1, done: custDone } : undefined}
            onNewForClient={() => navigate(`/orders/new?from=${oid}`)} onOpen={onOpen} readOnly={closed} />
          <PaymentBlock order={order} form={form} set={set} total={total} cod={cod} prepay={prepay} step={steps ? { n: 3, done: !!form.payment_method_id } : undefined}
            readOnly={closed} busy={action.isPending}
            onConfirm={(account_id) => action.mutate({ path: "/prepayment/confirm", body: { account_id } })}
            onReceipt={(k) => action.mutate({ path: "/receipts", body: { kind: k } })}
            onAddPayment={(body) => action.mutate({ path: "/payments", body })} />
          <DeliveryBlock order={order} form={form} set={set} cod={cod} codKind={method?.np_cod ?? ""} step={steps ? { n: 4, done: delivDone } : undefined}
            readOnly={closed} locked={shippedLock} busy={action.isPending || save.isPending} isNew={isNew}
            onCreateTtn={openTtn} onAction={(path, m) => action.mutate({ path, method: m })} />
        </div>
        {/* ======== права колонка ======== */}
        <div className="oc-right">
          <Block title="Товари" sub={form.items.length ? `${form.items.length} ${plural(form.items.length, "позиція", "позиції", "позицій")}` : undefined}
            step={steps ? { n: 2, done: form.items.length > 0 } : undefined} className="oc-goods"
            acts={!closed && <>
              <Button size={30} icon={Plus} onClick={() => goods.current?.focusSearch()}>Товар</Button>
              <Button size={30} icon={Plus} onClick={() => goods.current?.startUpsell()}>Допродаж</Button>
            </>}>
            <Goods ref={goods} items={form.items} products={meta.products} onChange={(items) => set({ items })} readOnly={closed} />
            <div className="oc-totals">
              <div><span>Товари</span><b className="num">{money(subtotal)} ₴</b></div>
              <div><span>Знижка</span>
                <span className="oc-disc"><input value={form.discount} disabled={closed} onChange={(e) => set({ discount: e.target.value.replace(",", ".") })} placeholder="0" inputMode="decimal" aria-label="Знижка, ₴" /> ₴</span></div>
              {order?.items_cost != null && <div><span>Собівартість · прибуток</span><b className="num">{money(order.items_cost)} ₴ · {money(total - order.items_cost)} ₴</b></div>}
            </div>
          </Block>
          <div className="oc-bottom">
            <DetailsBlock order={order} form={form} set={set} readOnly={closed} onTake={() => action.mutate({ path: "/take" })} />
            <SummaryCard order={order} form={form} total={total} cod={cod} prepay={prepay} subtotal={subtotal}
              onTodo={(a) => runTodo(a)} onReceipt={(k) => action.mutate({ path: "/receipts", body: { kind: k } })} />
          </div>
        </div>
      </div>

      {ttnOpen && order && (
        <TtnDialog order={order} accountId={form.np_account_id} onClose={() => setTtnOpen(false)}
          onCreated={(o, labelUrl) => {
            qc.invalidateQueries({ queryKey: ["documents"] });
            qc.setQueryData(["order", o.id], o);
            const f = toForm(o, newStatus);
            setForm(f); setBaseline(JSON.stringify(f)); setVersion(o.version);
            qc.invalidateQueries({ queryKey: ["orders"] });
            setTtnOpen(false);
            toast(`ТТН ${o.ttn} створено`);
            if (labelUrl) printLabel(o.id, toast);
          }} />
      )}
      {history && order && <HistoryPanel order={order} onClose={() => setHistory(false)}
        onComment={(text) => action.mutate({ path: "/comments", body: { text } })}
        onSms={(text, channel) => action.mutate({ path: "/sms", body: { text, channel } })} />}
    </Window>
  );

  function runTodo(a: string) {
    if (!order) return;
    if (a === "ttn") openTtn();
    else if (a === "label") printLabel(order.id, toast).then(() => qc.invalidateQueries({ queryKey: ["order", oid] }));
    else if (a === "registry") action.mutate({ path: "/registry" });
    else if (a === "sms_ttn") action.mutate({ path: "/sms-ttn" });
    else if (a === "prepay_confirm") action.mutate({ path: "/prepayment/confirm", body: {} });
    else if (a === "prepay_receipt") action.mutate({ path: "/receipts", body: { kind: "prepay" } });
    else if (a === "cod_receipt") action.mutate({ path: "/receipts", body: { kind: "postpay" } });
    else if (a === "waybill") saveAsync().then(() => printDocument("nakladna", order.id, (m) => toast(m, "error")));
  }
}

// ======================================================================== шапка: доріжка статусів
function StatusTrack({ statusId, onPick, disabled }: { statusId: number; onPick: (id: number, reasonId?: number) => void; disabled?: boolean }) {
  const meta = useMeta();
  const [reasonFor, setReasonFor] = useState<number | null>(null);
  const byCode = Object.fromEntries(meta.statuses.map((s) => [s.code, s]));
  const track = TRACK.map((c) => byCode[c]).filter((s) => s && s.active);
  const cur = meta.statuses.find((s) => s.id === statusId);
  const curIdx = track.findIndex((s) => s.id === statusId);
  const branch = meta.statuses.filter((s) => s.active && (s.stage ?? "order") === "order" && !TRACK.includes(s.code));
  const isBranch = cur && curIdx < 0 && (cur.stage ?? "order") === "order";
  const isLead = cur && (cur.stage ?? "order") === "lead";
  const pick = (id: number) => {
    const s = meta.statuses.find((x) => x.id === id);
    if (s && (s.code === "cancelled" || s.code === "refused") && meta.reasons.some((r) => r.active && r.status_ids.includes(id))) { setReasonFor(id); return; }
    onPick(id);
  };
  return (
    <nav className="track" aria-label="Статус замовлення">
      {isLead && <><span className="pill lg cur"><Check size={13} strokeWidth={2.4} />{cur!.name}</span><i className="track-sep" /></>}
      {track.map((s, i) => {
        const state = curIdx < 0 ? (isBranch && i <= 1 ? "past" : "future") : i < curIdx ? "past" : i === curIdx ? "cur" : "future";
        return (
          <span key={s.id} className="track-step">
            {i > 0 && <i className="track-sep" />}
            <button type="button" className={`track-pill ${state}`} disabled={disabled || state === "cur"} aria-current={state === "cur" ? "step" : undefined}
              onClick={() => pick(s.id)} title={state === "cur" ? "Поточний статус" : `Змінити на «${s.name}»`}>
              {(state === "past" || state === "cur") && <Check size={13} strokeWidth={2.4} />}{s.name}
            </button>
          </span>
        );
      })}
      {isBranch && <><i className="track-sep bad" /><span className="track-pill branch"><Check size={13} strokeWidth={2.4} />{cur!.name}</span></>}
      <MenuButton align="left" className="track-more" button={({ open, toggle }) => (
        <button type="button" className="track-pill future icon" aria-label="Інші статуси" aria-expanded={open} disabled={disabled} onClick={toggle}><MoreHorizontal size={16} /></button>
      )}>
        {(closeMenu) => (<>
          {[...branch.filter((s) => BRANCH.includes(s.code)), ...branch.filter((s) => !BRANCH.includes(s.code))].map((s) => (
            <button key={s.id} className="pop-item" onClick={() => { closeMenu(); pick(s.id); }}><StatusPill status={s} /></button>
          ))}
          {meta.statuses.filter((s) => s.active && s.stage === "lead").length > 0 && <div className="note-head">Повернути в ліди</div>}
          {meta.statuses.filter((s) => s.active && s.stage === "lead").map((s) => (
            <button key={s.id} className="pop-item" onClick={() => { closeMenu(); pick(s.id); }}><StatusPill status={s} /></button>
          ))}
        </>)}
      </MenuButton>
      {reasonFor && (
        <ReasonPicker statusId={reasonFor} onClose={() => setReasonFor(null)} onPick={(rid) => { onPick(reasonFor, rid); setReasonFor(null); }} />
      )}
    </nav>
  );
}

function ReasonPicker({ statusId, onPick, onClose }: { statusId: number; onPick: (rid: number) => void; onClose: () => void }) {
  const meta = useMeta();
  const box = useRef<HTMLDivElement>(null);
  useOutside(box, onClose);
  const s = meta.statuses.find((x) => x.id === statusId);
  return (
    <div className="pop reason-pop" ref={box} role="menu">
      <div className="note-head">«{s?.name}» — причина</div>
      {meta.reasons.filter((r) => r.active && r.status_ids.includes(statusId)).map((r) => (
        <button key={r.id} className="pop-item" onClick={() => onPick(r.id)}>{r.name}</button>
      ))}
    </div>
  );
}

// ======================================================================== шапка: друк, чек, нагадування
function PrintMenu({ order, onBefore, onError }: { order: Order; onBefore: () => Promise<void>; onError: (m: string) => void }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const docs: [DocKind, typeof FileText][] = [["nakladna", FileText], ["rahunok", Receipt], ["garantiya", ShieldCheck]];
  return (
    <MenuButton button={({ open, toggle }) => (
      <button className="btn" aria-haspopup="menu" aria-expanded={open} disabled={busy} onClick={toggle}><Printer size={15} />{busy ? "Готую…" : "Друк"}<ChevronDown size={14} /></button>
    )}>
      {(close) => (<>
        {docs.map(([k, Icon]) => {
          const issued = (order.documents ?? []).find((x) => x.kind === KIND_OF[k]);
          return (
            <button key={k} className="pop-item" onClick={async () => { close(); setBusy(true); await onBefore(); await printDocument(k, order.id, onError); setBusy(false); }}>
              <Icon size={16} /><span style={{ flex: 1 }}>{DOC_KINDS[k].title}</span>
              {issued && <span className="doc-issued" title="Документ видано"><Check size={13} />{issued.number_text}</span>}
            </button>
          );
        })}
        {order.label && (
          <button className="pop-item" onClick={() => { close(); printLabel(order.id, toast); }}>
            <TagIcon size={16} />{order.label === "rozetka" ? "Маркування Rozetka" : "Наклейка (PDF)"}</button>
        )}
        <a className="pop-item" href={`${ROOT}/classic/orders/${order.id}/print`} target="_blank" rel="noreferrer" onClick={close}><Printer size={16} />Бланк замовлення</a>
      </>)}
    </MenuButton>
  );
}

function CheckMenu({ order, busy, onReceipt }: { order: Order; busy: boolean; onReceipt: (kind: string) => void }) {
  const rs = order.receipts ?? [];
  const sold = rs.some((r) => r.kind === "sell" && r.status === "done");
  return (
    <MenuButton button={({ open, toggle }) => (
      <button className="btn" aria-haspopup="menu" aria-expanded={open} disabled={busy} onClick={toggle}><Receipt size={15} />Чек</button>
    )}>
      {(close) => (<>
        {!sold && <button className="pop-item" onClick={() => { close(); onReceipt("sell"); }}><Receipt size={16} />Чек продажу</button>}
        <button className="pop-item" onClick={() => { close(); onReceipt("prepay"); }}><Wallet size={16} />Чек передоплати</button>
        <button className="pop-item" onClick={() => { close(); onReceipt("postpay"); }}><Wallet size={16} />Чек післяплати</button>
        <button className="pop-item" onClick={() => { close(); if (window.confirm("Створити чек повернення?")) onReceipt("return"); }}><RefreshCw size={16} />Чек повернення</button>
        {rs.length > 0 && <div className="note-head">Чеки замовлення</div>}
        {rs.map((r) => (
          <a key={r.id} className="pop-item" href={r.url || undefined} target="_blank" rel="noreferrer" title={r.error || undefined}>
            <span className={`dot-st ${r.status}`} />{r.kind_name} · {money(r.total)} ₴{r.test && " · тест"}{r.url && <ExternalLink size={13} />}
          </a>
        ))}
      </>)}
    </MenuButton>
  );
}

function RemindButton({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const local = (d: Date) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  const at = (days: number, h: number) => { const d = new Date(); d.setDate(d.getDate() + days); d.setHours(h, 0, 0, 0); return local(d); };
  const presets: [string, () => string][] = [
    ["Через годину", () => local(new Date(Date.now() + 3600_000))], ["Сьогодні о 18:00", () => at(0, 18)],
    ["Завтра о 10:00", () => at(1, 10)], ["Через 3 дні", () => at(3, 10)],
  ];
  const due = value && new Date(value) <= new Date();
  const label = value ? `Нагадування ${value.slice(8, 10)}.${value.slice(5, 7)} о ${value.slice(11, 16)}` : "Нагадати про замовлення";
  return (
    <MenuButton button={({ open, toggle }) => (
      <button type="button" className={`icon-btn remind${value ? (due ? " due" : " on") : ""}`} aria-label={label} title={label} aria-expanded={open} onClick={toggle}>
        {due ? <AlarmClock size={16} /> : <Bell size={16} />}
      </button>
    )}>
      {(close) => (
        <div className="remind-menu">
          <div className="note-head">{value ? label : "Нагадати про замовлення"}</div>
          {presets.map(([t, f]) => <button key={t} className="pop-item" onClick={() => { onChange(f()); close(); }}>{t}</button>)}
          <label className="remind-own"><span className="lbl">Свій час</span><input type="datetime-local" value={value} onChange={(e) => onChange(e.target.value)} /></label>
          {value && <button className="pop-item danger" onClick={() => { onChange(""); close(); }}><X size={15} />Прибрати нагадування</button>}
        </div>
      )}
    </MenuButton>
  );
}

// ======================================================================== Покупець
function CustomerBlock({ order, form, set, isNew, step, onNewForClient, onOpen, readOnly }: {
  order?: Order; form: Form; set: (p: Partial<Form>) => void; isNew: boolean; step?: { n: number; done: boolean };
  onNewForClient: () => void; onOpen: (id: number) => void; readOnly: boolean;
}) {
  const meta = useMeta();
  const navigate = useNavigate();
  const [editName, setEditName] = useState(isNew || !form.customer_name);
  const [showEmail, setShowEmail] = useState(false);
  const [others, setOthers] = useState(false);
  const c = order?.customer;
  const tel = digits(form.phone);
  const src = meta.order_sources.find((s) => s.id === form.source_id)?.name;
  const entity = meta.legal_entities.find((e) => e.id === form.legal_entity_id) ?? meta.legal_entities.find((e) => e.is_default);
  return (
    <Block title={isNew ? "Покупець" : undefined} step={isNew ? step : undefined} className="oc-cust">
      {c?.blacklisted && <div className="oc-strip bad"><Ban size={15} /><span><b>Чорний список.</b> {c.blacklist_reason || "Причину не вказано"}</span>
        <button className="link-btn" onClick={() => navigate(`/customers/${c.id}`)}>Картка</button></div>}
      {order?.duplicate_of_id && <div className="oc-strip warn"><Copy size={15} /><span>Можливий дубль замовлення №{order.duplicate_of_id}</span>
        <button className="link-btn" onClick={() => onOpen(order.duplicate_of_id!)}>Відкрити</button></div>}
      {!isNew && order && (
        <div className="oc-meta">
          {step && <span className={`step${step.done ? " done" : ""}`}>{step.done ? <Check size={11} strokeWidth={3} /> : step.n}</span>}
          Замовлення №{order.id} · {dateTime(order.created_at)}{src && ` · ${src}`}
          {order.shop_id && <Tag kind="info">{meta.shops[String(order.shop_id)] ?? "Маркетплейс"} №{order.external_id}</Tag>}
        </div>
      )}
      {editName && !readOnly ? (
        <NameField value={form.customer_name} onChange={(v) => set({ customer_name: v })} saved={order?.customer_name ?? ""} autoFocus={!isNew && !form.customer_name}
          onDone={() => form.customer_name.trim() && setEditName(false)} />
      ) : (
        <button type="button" className="oc-name" onClick={() => !readOnly && setEditName(true)} title="Змінити ПІБ">{form.customer_name || "Без імені"}</button>
      )}
      <div className="oc-phone-row">
        <span className="phone-pill-in">
          <span className="ph-flag" aria-hidden>{flag(form.country)}</span>
          <select className="ph-country" value={form.country} disabled={readOnly} onChange={(e) => set({ country: e.target.value })} aria-label="Країна">
            {Object.entries(meta.countries).map(([cc, n]) => <option key={cc} value={cc} title={n}>{cc} · {n}</option>)}
          </select>
          <UaPhone value={form.phone} country={form.country} onChange={(v) => set({ phone: v })} aria-label="Телефон" disabled={readOnly} autoFocus={isNew} />
        </span>
        {tel.length >= 10 && <>
          <a className="icon-btn" href={`tel:+${tel}`} aria-label="Подзвонити" title="Подзвонити"><Phone size={16} /></a>
          <a className="icon-btn" href={`viber://chat?number=%2B${tel}`} aria-label="Viber" title="Viber"><MessageCircle size={16} /></a>
          <a className="icon-btn" href={`https://t.me/+${tel}`} target="_blank" rel="noreferrer" aria-label="Telegram" title="Telegram"><Send size={16} /></a>
          <a className="icon-btn" href={`sms:+${tel}`} aria-label="SMS" title="SMS"><MessageSquare size={16} /></a>
        </>}
      </div>
      {meta.legal_entities.length > 0 && (
        <label className="oc-entity" title="Від чийого імені продаж: за юрособою обирається каса Checkbox, ключ НП і реквізити документів">
          <Landmark size={14} aria-hidden />
          <span className="ell">{entity?.name ?? "Юрособа"}{entity?.has_cashier ? " · каса" : ""}{meta.np_accounts.length ? " і ключ НП" : ""}</span>
          <select value={form.legal_entity_id} disabled={readOnly} onChange={(e) => set({ legal_entity_id: e.target.value ? Number(e.target.value) : "" })} aria-label="Юрособа">
            <option value="">{meta.legal_entities.find((x) => x.is_default)?.name ?? "за замовчуванням"} (за замовч.)</option>
            {meta.legal_entities.map((x) => <option key={x.id} value={x.id}>{x.name}{x.has_cashier ? "" : " · без каси"}</option>)}
          </select>
        </label>
      )}
      {c && (
        <div className="tiles4">
          <div><b>{c.orders}</b><span>Замовлень</span></div>
          <div className={c.buyout_rate != null && c.buyout_rate < 50 ? "warn" : ""}><b>{c.buyout_rate != null ? `${Math.round(c.buyout_rate)}%` : "—"}</b><span>Викуп</span></div>
          <div><b>{c.refused}</b><span>Відмов</span></div>
          <div><b>{money(c.sum_delivered)} ₴</b><span>Сума</span></div>
        </div>
      )}
      {(form.email || showEmail) ? (
        <input className="oc-email" type="email" value={form.email} disabled={readOnly} autoFocus={showEmail && !form.email} onChange={(e) => set({ email: e.target.value })} placeholder="name@example.com" aria-label="Email" />
      ) : !readOnly && <button type="button" className="add-chip" onClick={() => setShowEmail(true)}><Plus size={13} />Email</button>}
      {order && (
        <div className="oc-others">
          {(order.others?.length ?? 0) > 0 && (
            <button type="button" className="link-btn" aria-expanded={others} onClick={() => setOthers((x) => !x)}>
              Інші замовлення · {order.others.length} <ChevronDown size={13} className={others ? "rot" : ""} /></button>
          )}
          <button type="button" className="link-btn" onClick={onNewForClient}><Plus size={13} />Нове замовлення цьому клієнту</button>
        </div>
      )}
      {others && order && (
        <div className="oc-others-list">
          {order.others.map((o) => (
            <button key={o.id} type="button" onClick={() => onOpen(o.id)}>
              <span className="mono">№{o.id}</span><span className="muted">{shortDate(o.created_at)}</span>
              <span className="ell">{o.items.map((i) => i.name).join(", ")}</span><b className="num">{money(o.total)} ₴</b>
              <StatusPill status={meta.statuses.find((s) => s.id === o.status_id)} />
            </button>
          ))}
        </div>
      )}
    </Block>
  );
}

/** ПІБ одним рядком з розпізнаванням (прізвище, ім'я, по батькові — у будь-якому порядку). */
function NameField({ value, onChange, saved, autoFocus, onDone }: { value: string; onChange: (v: string) => void; saved: string; autoFocus?: boolean; onDone?: () => void }) {
  const dv = useDebounced(value.trim(), 250);
  const { data } = useQuery({
    queryKey: ["name-split", dv], enabled: dv.length > 1 && dv !== saved,
    queryFn: () => api.get<{ last_name: string; first_name: string; middle_name: string; full: string }>(`/names/split${qs({ q: dv })}`),
    staleTime: Infinity,
  });
  const show = data && dv.length > 1 && dv !== saved;
  return (
    <div className="oc-name-edit">
      <input value={value} onChange={(e) => onChange(e.target.value)} autoFocus={autoFocus} placeholder="ПІБ одним рядком — у будь-якому порядку" aria-label="ПІБ"
        onBlur={onDone} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); onDone?.(); } }} />
      {show && (
        <div className="name-parts" title="Як CRM розпізнала ПІБ">
          <span><small>Прізвище</small>{data.last_name || "—"}</span><span><small>Ім'я</small>{data.first_name || "—"}</span><span><small>По батькові</small>{data.middle_name || "—"}</span>
        </div>
      )}
    </div>
  );
}

// ======================================================================== Оплата
function PaymentBlock({ order, form, set, total, cod, prepay, step, readOnly, busy, onConfirm, onReceipt, onAddPayment }: {
  order?: Order; form: Form; set: (p: Partial<Form>) => void; total: number; cod: number; prepay: number; step?: { n: number; done: boolean };
  readOnly: boolean; busy: boolean; onConfirm: (accountId: number | null) => void; onReceipt: (kind: string) => void; onAddPayment: (b: Record<string, unknown>) => void;
}) {
  const meta = useMeta();
  const method = meta.payment_methods.find((m) => m.id === form.payment_method_id);
  const kind = method?.kind ?? form.payment_type;
  const entity = meta.legal_entities.find((e) => e.id === form.legal_entity_id) ?? meta.legal_entities.find((e) => e.is_default);
  const accounts = entity?.accounts ?? [];
  const pays = order?.payments ?? [];
  const received = pays.filter((p) => p.kind === "prepayment" && p.status === "received");
  const confirmed = received.find((p) => p.confirmed_at) ?? received[0];
  const [acc, setAcc] = useState<number | "">(confirmed?.account_id ?? accounts[0]?.id ?? "");
  const [adding, setAdding] = useState(false);
  const [extra, setExtra] = useState({ amount: "", method: "card" });
  const rs = order?.receipts ?? [];
  const rcDone = rs.find((r) => r.status === "done" && (r.kind === "prepay" || r.kind === "sell"));
  const codText = cod <= 0 ? "без післяплати" : COD_TEXT[method?.np_cod || ""] ?? "післяплата";
  const paidFully = total > 0 && cod <= 0 && (kind === "prepaid" ? received.length > 0 : true) && kind !== "cod";
  return (
    <Block title="Оплата" step={step} className="oc-pay"
      acts={rcDone ? <Tag kind="ok">Чек: {rcDone.kind === "prepay" ? "передоплата" : "продаж"} <Check size={11} /></Tag> : paidFully ? <Tag kind="ok">Повністю оплачено</Tag> : undefined}>
      <div className="oc-row">
        <CreditCard size={16} className="oc-row-ic" aria-hidden />
        <IconPick items={meta.payment_methods} value={form.payment_method_id || null} ariaLabel="Вид оплати" className="oc-grow"
          onChange={(id) => { if (readOnly) return; const m = meta.payment_methods.find((x) => x.id === id); set({ payment_method_id: id ?? "", payment_type: m?.kind ?? "cod" }); }}
          render={(m) => <PayLabel icon={m.icon} image={m.image} name={m.name} size={18} />} placeholder={<span>Оберіть вид оплати</span>} />
        {order?.checkbox_ready && <Button icon={Receipt} disabled={busy || readOnly} onClick={() => onReceipt(kind === "cod" ? "sell" : "prepay")}>Чек</Button>}
      </div>
      {(kind === "partial" || kind === "prepaid") && (<>
        <div className="oc-sublbl">{kind === "prepaid" ? "Повна оплата" : "Передоплата"} · куди надійшли кошти</div>
        <div className="oc-row">
          <Wallet size={16} className="oc-row-ic" aria-hidden />
          <span className="money-in oc-prepay">
            <input value={kind === "prepaid" ? money(total) : form.prepayment} disabled={readOnly || kind === "prepaid"} inputMode="decimal" aria-label="Сума передоплати"
              onChange={(e) => set({ prepayment: e.target.value.replace(",", ".").replace(/[^\d.]/g, "") })} placeholder="0" />
            <span className="unit">₴</span>
          </span>
          <label className="oc-acc">
            <Building2 size={14} aria-hidden />
            <select value={acc} disabled={readOnly} onChange={(e) => setAcc(e.target.value ? Number(e.target.value) : "")} aria-label="Рахунок, куди надійшли кошти">
              {!accounts.length && <option value="">Рахунок не вказано</option>}
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name} · {entity?.name}</option>)}
            </select>
            <ChevronDown size={14} aria-hidden />
          </label>
          <button type="button" className={`oc-ok${confirmed ? " on" : ""}`} disabled={busy || readOnly || !order || prepay <= 0}
            aria-label={confirmed ? "Передоплата надійшла" : "Позначити: передоплата надійшла"} title={confirmed ? "Надійшла" : "Позначити: кошти надійшли"}
            onClick={() => onConfirm(acc || null)}><CircleCheck size={20} /></button>
        </div>
        {confirmed && (
          <div className="oc-confirmed"><Check size={13} />надійшла {dateTime(confirmed.received_at ?? confirmed.confirmed_at)}{confirmed.confirmed_by && ` · підтвердив(ла) ${confirmed.confirmed_by}`}{confirmed.account && ` · ${confirmed.account}`}</div>
        )}
        {!accounts.length && entity && <div className="hint">Рахунки для передоплат додаються в «Налаштування → Юрособи».</div>}
      </>)}
      {form.delivery_method === "novaposhta" && (
        <div className="oc-ttn-hint"><ArrowUpRight size={14} />У ТТН піде: {codText}{cod > 0 && ` · ${money(cod)} ₴`}</div>
      )}
      {pays.filter((p) => p.kind !== "prepayment" || p.status !== "received").length > 0 && (
        <div className="oc-pays">
          {pays.filter((p) => p.kind !== "prepayment" || p.status !== "received").map((p) => (
            <div key={p.id}><span>{p.kind_name}</span><b className="num">{money(p.amount)} ₴</b>
              <Tag kind={p.status === "received" ? "ok" : p.status === "cancelled" ? "bad" : p.status === "collected" ? "info" : "warn"}>{p.status_name}</Tag></div>
          ))}
        </div>
      )}
      {!readOnly && order && (adding ? (
        <form className="oc-addpay" onSubmit={(e) => { e.preventDefault(); onAddPayment({ amount: extra.amount, method: extra.method }); setAdding(false); setExtra({ amount: "", method: "card" }); }}>
          <span className="money-in"><input autoFocus value={extra.amount} onChange={(e) => setExtra({ ...extra, amount: e.target.value })} inputMode="decimal" placeholder="Сума" aria-label="Сума оплати" /><span className="unit">₴</span></span>
          <select value={extra.method} onChange={(e) => setExtra({ ...extra, method: e.target.value })} aria-label="Спосіб">
            <option value="card">Карта</option><option value="iban">Рахунок</option><option value="cash">Готівка</option><option value="other">Інше</option></select>
          <Button type="submit" size={30} disabled={!extra.amount}>Додати</Button>
          <IconButton icon={X} label="Скасувати" quiet size={28} onClick={() => setAdding(false)} />
        </form>
      ) : <button type="button" className="add-chip" onClick={() => setAdding(true)}><Plus size={13} />Оплата</button>)}
    </Block>
  );
}

// ======================================================================== Доставка
function DeliveryBlock({ order, form, set, cod, codKind, step, readOnly, locked, busy, isNew, onCreateTtn, onAction }: {
  order?: Order; form: Form; set: (p: Partial<Form>) => void; cod: number; codKind: string; step?: { n: number; done: boolean };
  readOnly: boolean; locked: boolean; busy: boolean; isNew: boolean; onCreateTtn: () => void; onAction: (path: string, method?: "post" | "del") => void;
}) {
  const meta = useMeta();
  const toast = useToast();
  const dm = form.delivery_method;
  const carrier = meta.carriers[dm];
  const value = dm === "novaposhta" && form.np_account_id ? `novaposhta:${form.np_account_id}` : dm;
  const hasTtn = !!(order?.ttn || form.ttn);
  const stateName = order?.delivery_state ? meta.delivery_states[order.delivery_state] ?? order.delivery_state : "";
  const dis = readOnly || locked;
  const opts: [string, string][] = [];
  Object.entries(meta.delivery_methods).forEach(([k, n]) => {
    if (k === "novaposhta" && meta.np_accounts.length > 1) meta.np_accounts.forEach((a) => opts.push([`novaposhta:${a.id}`, `${n} · ${a.name}`]));
    else if (k === "novaposhta" && meta.np_accounts.length === 1) opts.push([k, `${n} · ${meta.np_accounts[0].name}`]);
    else opts.push([k, `${n}${meta.carriers[k]?.beta ? " (бета)" : ""}`]);
  });
  const whereLine = [form.city_name, form.warehouse_name].filter(Boolean).join(", ");
  return (
    <Block title="Доставка" step={step} className="oc-dlv"
      acts={hasTtn && stateName ? <Tag kind={order?.delivery_state === "delivered" ? "ok" : order?.delivery_state === "refused" || order?.delivery_state === "returned" ? "bad" : "warn"}>{stateName}</Tag> : undefined}>
      <div className="oc-row">
        <Truck size={16} className="oc-row-ic" aria-hidden />
        <label className="oc-select">
          {dm === "novaposhta" && <span className="np-badge">НП</span>}
          <select value={value} disabled={dis || hasTtn} aria-label="Перевізник"
            onChange={(e) => { const [m, acc] = e.target.value.split(":"); set({ delivery_method: m, np_account_id: acc ? Number(acc) : "", ...(m !== dm ? { city_ref: "", warehouse_ref: "", warehouse_name: "" } : {}) }); }}>
            {opts.map(([k, n]) => <option key={k} value={k}>{n}</option>)}
          </select>
          <ChevronDown size={14} aria-hidden />
        </label>
      </div>
      {dm !== "pickup" && (
        <div className="oc-row">
          <ScanBarcode size={16} className="oc-row-ic" aria-hidden />
          <input className="mono oc-grow" value={form.ttn} disabled={dis} readOnly={!!order?.carrier_ref} onChange={(e) => set({ ttn: e.target.value.trim() })}
            placeholder="ТТН з'явиться після створення" aria-label="ТТН" />
        </div>
      )}
      {hasTtn && (
        <div className="oc-ship-line">
          <span>{whereLine || "Адреса не вказана"}{num(order?.delivery_cost) > 0 && ` · ${money(order!.delivery_cost)} ₴`}{order?.delivery_eta && ` · очікується ${shortDate(order.delivery_eta)}`}</span>
          {order?.delivery_status && <small className="muted">{order.delivery_status}{order.delivery_checked_at && ` · ${dateTime(order.delivery_checked_at)}`}</small>}
        </div>
      )}
      {/* для перевізників без вікна ТТН — місто й відділення тут */}
      {!hasTtn && dm !== "novaposhta" && dm !== "pickup" && (
        <div className="oc-addr">
          <input value={form.city_name} disabled={dis} onChange={(e) => set({ city_name: e.target.value })} placeholder="Місто" aria-label="Місто" />
          {dm === "ukrposhta" && <input value={form.postcode} disabled={dis} onChange={(e) => set({ postcode: e.target.value })} placeholder="Індекс" maxLength={5} inputMode="numeric" aria-label="Індекс" />}
          {(dm === "meest" || dm === "rozetka") && <input value={form.warehouse_name} disabled={dis} onChange={(e) => set({ warehouse_name: e.target.value })} placeholder={dm === "rozetka" ? "Відділення ROZETKA" : "Відділення"} aria-label="Відділення" />}
          {dm === "meest" && <input className="mono" value={form.warehouse_ref} disabled={dis} onChange={(e) => set({ warehouse_ref: e.target.value })} placeholder="ID відділення для ТТН" aria-label="ID відділення" />}
          {dm === "courier" && <input value={form.address} disabled={dis} onChange={(e) => set({ address: e.target.value })} placeholder="Вулиця, будинок, квартира" aria-label="Адреса" />}
        </div>
      )}
      {!hasTtn && dm === "novaposhta" && whereLine && <div className="oc-ship-line"><span>{whereLine}</span></div>}
      {dm !== "pickup" && (
        <div className="oc-row oc-cod">
          <Wallet size={16} className="oc-row-ic" aria-hidden />
          <span className="oc-ro">{cod > 0 ? `Післяплата ${money(cod)} ₴ · ${COD_TEXT[codKind] ?? "післяплата"}` : "Без післяплати"} · з оплати</span>
        </div>
      )}
      {order?.pay_check && hasTtn && <div className={`pc-line pc-${order.pay_check.state}`}><PayCheck check={order.pay_check} text /></div>}
      {dm !== "pickup" && (
        <div className="oc-row oc-ttn-acts">
          {hasTtn ? (
            order?.label
              ? <Button variant="soft" wide icon={TagIcon} onClick={() => printLabel(order.id, toast)}>{order.label === "rozetka" ? "Маркування Rozetka" : "Друк наклейки"}</Button>
              : <Button variant="soft" wide icon={RefreshCw} disabled={busy || !carrier} onClick={() => onAction("/track")}>Оновити статус</Button>
          ) : dm === "rozetka" ? (
            <p className="hint">ТТН RMP-… створюється в кабінеті продавця Rozetka; вставте її сюди — маркування друкується з API Rozetka.</p>
          ) : carrier?.configured ? (
            <Button variant="soft" wide icon={Truck} kbd={dm === "novaposhta" ? "Ctrl ⏎" : undefined} disabled={readOnly}
              title={isNew ? "Замовлення буде створено, і відкриється вікно ТТН" : undefined} onClick={onCreateTtn}>Створити ТТН</Button>
          ) : carrier ? <p className="hint">Щоб створювати ТТН, заповніть доступи в «Налаштування → Доставка».</p> : null}
          {order && (hasTtn || carrier) && (
            <MenuButton button={({ open, toggle }) => <IconButton icon={MoreHorizontal} label="Ще дії з ТТН" aria-expanded={open} onClick={toggle} />}>
              {(close) => (<>
                {order.label && <button className="pop-item" onClick={() => { close(); printLabel(order.id, toast); }}><TagIcon size={16} />Наклейка</button>}
                {hasTtn && dm === "novaposhta" && <button className="pop-item" disabled={!!order.np_registry_ref} onClick={() => { close(); onAction("/registry"); }}>
                  <ListChecks size={16} />{order.np_registry_ref ? `У реєстрі ${order.np_registry_ref}` : "Додати в реєстр НП"}</button>}
                {hasTtn && carrier && <button className="pop-item" onClick={() => { close(); onAction("/track"); }}><RefreshCw size={16} />Оновити статус</button>}
                {hasTtn && <button className="pop-item" onClick={() => { close(); navigator.clipboard?.writeText(order.ttn || form.ttn); toast("ТТН скопійовано"); }}><Copy size={16} />Копіювати ТТН</button>}
                {order.carrier_ref && !locked && <button className="pop-item danger" onClick={() => { close(); if (window.confirm(`Видалити ТТН ${order.ttn} у перевізника?`)) onAction("/ttn", "del"); }}><Trash2 size={16} />Видалити ТТН</button>}
              </>)}
            </MenuButton>
          )}
        </div>
      )}
      {!hasTtn && dm === "novaposhta" && carrier?.configured && <p className="oc-note">Місто, відділення й платник — у вікні створення ТТН</p>}
    </Block>
  );
}

// ======================================================================== Деталі
function DetailsBlock({ order, form, set, readOnly, onTake }: { order?: Order; form: Form; set: (p: Partial<Form>) => void; readOnly: boolean; onTake: () => void }) {
  const meta = useMeta();
  const [utm, setUtm] = useState(false);
  const [extra, setExtra] = useState(false);
  const status = meta.statuses.find((s) => s.id === form.status_id);
  const reasons = meta.reasons.filter((r) => r.status_ids.includes(form.status_id));
  const srcOffice = meta.order_sources.find((x) => x.id === form.source_id)?.office_id;
  const office = meta.offices.find((o) => o.id === (srcOffice ?? form.office_id))?.name;
  const canTake = order && meta.user.role !== "warehouse" && order.manager_id !== meta.user.id && (!order.manager_id || meta.user.role === "admin");
  const sel = (v: number | "", on: (v: number | "") => void, items: { id: number; name: string }[], empty: string, label: string) => (
    <select className="prop-sel" value={v} disabled={readOnly} aria-label={label} onChange={(e) => on(e.target.value ? Number(e.target.value) : "")}>
      <option value="">{empty}</option>{items.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
    </select>
  );
  const mgr = meta.user.role === "admin"
    ? sel(form.manager_id, (v) => set({ manager_id: v }), meta.managers, "не призначений", "Менеджер")
    : <span className="prop-val">{order?.manager?.name ?? "не призначений"}{canTake && !readOnly && <button className="link-btn" onClick={onTake}>Взяти собі</button>}</span>;
  // розкладка (вимога власника): Джерело | Менеджер, Відділ | Юрособа, далі коментар на всю ширину у 2 рядки
  const rows: { k: string; label: string; v: React.ReactNode; wide?: boolean }[] = [
    { k: "src", label: "Джерело", v: sel(form.source_id, (v) => set({ source_id: v }), meta.order_sources, "не вказано", "Джерело") },
    { k: "mgr", label: "Менеджер", v: mgr },
    { k: "office", label: "Відділ", v: <span className="prop-val muted">{office ?? "—"}</span> },
    { k: "le", label: "Юрособа", v: meta.legal_entities.length
      ? sel(form.legal_entity_id, (v) => set({ legal_entity_id: v }), meta.legal_entities, "за замовчуванням", "Юрособа")
      : <span className="prop-val muted">—</span> },
    { k: "comment", label: "Коментар", wide: true, v: <textarea className="prop-area" rows={2} value={form.comment} disabled={readOnly} onChange={(e) => set({ comment: e.target.value })}
      placeholder="Коментар до замовлення" aria-label="Коментар" /> },
    { k: "mark", label: "Позначка", v: (
      <IconPick items={meta.marks} value={form.mark_id || null} ariaLabel="Позначка" emptyLabel="Без позначки" className="prop-ipick"
        onChange={(id) => !readOnly && set({ mark_id: id ?? "" })}
        render={(m) => <span className="mark-line"><MarkIcon icon={m.icon} color={m.color} size={15} /><span>{m.name}</span></span>}
        placeholder={<span className="muted">—</span>} />
    ) },
    ...(reasons.length || ["cancelled", "refused", "lead_refused"].includes(status?.code ?? "") ? [{ k: "reason", label: "Причина", v: sel(form.reason_id, (v) => set({ reason_id: v }), reasons.length ? reasons : meta.reasons.filter((r) => r.active), "не вказано", "Причина") }] : []),
    ...(order?.shop_id ? [{ k: "mp", label: "Маркетплейс", wide: true, v: <span className="prop-val">{meta.shops[String(order.shop_id)] ?? "Маркетплейс"} · №{order.external_id}{order.external_status && <span className="muted"> · {order.external_status}</span>}</span> }] : []),
  ];
  // поля 1–4 — згорнуто, як UTM
  const extras = EXTRA.map((f, i) => ({ f, i, name: meta.extra_fields[i] || `Поле ${i + 1}` })).filter((x) => meta.extra_on?.[x.i] ?? true);
  const filled = extras.filter((x) => form[x.f]).length;
  return (
    <Block title="Деталі" className="oc-details">
      <dl className="props">{rows.map((r) => [<dt key={`t-${r.k}`} className={r.wide ? "wide" : undefined}>{r.label}</dt>,
        <dd key={`d-${r.k}`} className={r.wide ? "wide" : undefined}>{r.v}</dd>])}</dl>
      <div className="det-toggles">
        {extras.length > 0 && (
          <button type="button" className="link-btn utm-toggle" aria-expanded={extra} onClick={() => setExtra((x) => !x)}>
            {extras.length === 4 ? "Поля 1–4" : "Додаткові поля"} {filled > 0 && <span className="muted">· заповнено {filled}</span>}<ChevronDown size={13} className={extra ? "rot" : ""} /></button>
        )}
        <button type="button" className="link-btn utm-toggle" aria-expanded={utm} onClick={() => setUtm((x) => !x)}>
          UTM і сайт {form.utm_source && <span className="muted">· {form.utm_source}</span>}<ChevronDown size={13} className={utm ? "rot" : ""} /></button>
      </div>
      {extra && (
        <dl className="props utm">
          {extras.map(({ f, name }) => [<dt key={`t${f}`}>{name}</dt>, <dd key={`d${f}`}><span className="prop-val">
            <input className="prop-in" value={form[f]} disabled={readOnly} onChange={(e) => set({ [f]: e.target.value } as Partial<Form>)} placeholder="—" aria-label={name} />
            {/^https?:\/\//.test(form[f]) && <a href={form[f]} target="_blank" rel="noreferrer" aria-label="Відкрити посилання"><ExternalLink size={13} /></a>}</span></dd>])}
        </dl>
      )}
      {utm && (
        <dl className="props utm">
          <dt>Сайт</dt><dd><input className="prop-in" value={form.site} disabled={readOnly} onChange={(e) => set({ site: e.target.value })} placeholder="—" aria-label="Сайт" /></dd>
          {UTM.map((u) => [<dt key={`t${u}`} className="mono">{u}</dt>, <dd key={`d${u}`}><input className="prop-in" value={form[u]} disabled={readOnly} onChange={(e) => set({ [u]: e.target.value } as Partial<Form>)} placeholder="—" aria-label={u} /></dd>])}
          {order?.ip && <><dt>IP</dt><dd className="mono">{order.ip}</dd></>}
        </dl>
      )}
    </Block>
  );
}

// ======================================================================== Підсумок
function SummaryCard({ order, form, total, cod, prepay, subtotal, onTodo, onReceipt }: {
  order?: Order; form: Form; total: number; cod: number; prepay: number; subtotal: number; onTodo: (a: string) => void; onReceipt: (k: string) => void;
}) {
  const meta = useMeta();
  const [showTodo, setShowTodo] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useOutside(box, () => setShowTodo(false), showTodo);
  const method = meta.payment_methods.find((m) => m.id === form.payment_method_id);
  const conf = order?.payments.find((p) => p.kind === "prepayment" && p.status === "received");
  const rc = (order?.receipts ?? []).find((r) => r.status === "done");
  const todo = order?.todo ?? [];
  const left = todo.filter((t) => t.state !== "done");
  const items: CheckItem[] = todo.map((t) => ({ key: t.key, label: t.label, state: t.state, hint: t.hint || undefined, onClick: t.action ? () => { setShowTodo(false); onTodo(t.action); } : undefined }));
  const paid = total > 0 && cod <= 0;
  return (
    <section className="summary-block oc-sum">
      <div className="lbl">{paid ? "Оплачено" : "До сплати при отриманні"}</div>
      <div className={`big${paid ? " paid" : ""}`}>{money(paid ? total : cod)} <span className="cur">₴</span></div>
      <div className="sum-rows">
        <div><span>Товари</span><b className="num">{money(subtotal)} ₴</b></div>
        {num(form.discount) > 0 && <div><span>Знижка</span><b className="num">−{money(form.discount)} ₴</b></div>}
        {prepay > 0 && <div><span>Передоплата{conf?.account ? ` · ${conf.account}` : ""}</span><b className="num">−{money(prepay)} ₴</b></div>}
        <div><span>Оплата</span><b>{method?.name ?? "не вибрано"}</b></div>
        {order?.checkbox_ready && (rc
          ? <div><span>Чек</span><b>{rc.kind_name} <Check size={13} /></b></div>
          : <div><span>Чек</span><button type="button" className="sum-warn" onClick={() => onReceipt(method?.kind === "cod" ? "sell" : "prepay")}>не пробитий</button></div>)}
      </div>
      {order && todo.length > 0 && (
        <div className="sum-foot" ref={box}>
          <ListChecks size={15} aria-hidden />
          {left.length ? <span className="ell">Лишилось: <b>{left.map((t) => t.label.split(" ")[0].replace("Товар", "резерв").toLowerCase()).join(" · ")}</b></span> : <span>Усе зроблено</span>}
          <button type="button" className="link-btn" aria-expanded={showTodo} onClick={() => setShowTodo((x) => !x)}>Показати</button>
          {showTodo && <div className="pop todo-pop"><div className="note-head">Що лишилось</div><Checklist items={items} /></div>}
        </div>
      )}
    </section>
  );
}

// ======================================================================== Історія — бічна панель 360 px
function HistoryPanel({ order, onClose, onComment, onSms }: { order: Order; onClose: () => void; onComment: (t: string) => void; onSms: (t: string, ch: string) => void }) {
  const meta = useMeta();
  const [kind, setKind] = useState<"all" | "status" | "sms" | "comments">("all");
  const [text, setText] = useState("");
  const [channel, setChannel] = useState("sms");
  const q = useQuery({ queryKey: ["order-history", order.id, kind, order.version], queryFn: () => api.get<{ events: { kind: string; text: string; details: string; user: string; at: string | null }[] }>(`/orders/${order.id}/history?kind=${kind}`) });
  const ic = { status: <Check size={14} />, sms: <MessageSquare size={14} />, comment: <MessageCircle size={14} />, other: <Pencil size={13} /> } as Record<string, React.ReactNode>;
  return (
    <SidePanel title={`Історія · №${order.id}`} onClose={onClose}
      footer={kind === "sms" && meta.sms_ready ? (
        <form className="hp-form" onSubmit={(e) => { e.preventDefault(); if (text.trim()) { onSms(text, channel); setText(""); } }}>
          <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)} placeholder="Текст SMS. Можна {ttn}, {total}, {cod}, {first_name}…" aria-label="Текст SMS" />
          <div className="hp-row"><select value={channel} onChange={(e) => setChannel(e.target.value)} aria-label="Канал"><option value="sms">SMS</option><option value="viber">Viber</option><option value="hybrid">Viber → SMS</option></select>
            <Button type="submit" size={30} icon={Send} disabled={!text.trim()}>Надіслати</Button></div>
        </form>
      ) : (
        <form className="hp-form" onSubmit={(e) => { e.preventDefault(); if (text.trim()) { onComment(text); setText(""); } }}>
          <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)} placeholder="Коментар для колег…" aria-label="Коментар для колег" />
          <div className="hp-row"><span className="hint">Покупець його не бачить</span><Button type="submit" size={30} disabled={!text.trim()}>Додати</Button></div>
        </form>
      )}>
      <Segmented label="Фільтр історії" value={kind} onChange={setKind}
        items={[{ key: "all", label: "Все" }, { key: "status", label: "Статуси" }, { key: "sms", label: "SMS" }, { key: "comments", label: "Коментарі" }]} />
      <div className="feed hp-feed">
        {q.isLoading && <div className="skel-rows"><div className="skel-row"><span className="skel" /></div></div>}
        {q.data?.events.map((e, i) => (
          <div key={i} className={`ev ev-${e.kind}`}>
            <span className="ev-ic" aria-hidden>{ic[e.kind] ?? ic.other}</span>
            <div><b>{e.text}</b>{e.user && <span className="muted"> · {e.user}</span>}{e.details && <div className="ev-d">{e.details}</div>}<div className="when">{dateTime(e.at)}</div></div>
          </div>
        ))}
        {q.data && !q.data.events.length && <p className="muted">Подій ще немає</p>}
      </div>
    </SidePanel>
  );
}


