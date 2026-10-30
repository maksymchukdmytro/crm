// Вікно ліда (UI-DESIGN §4.3): зліва черга дзвінків 280 px; у центрі Контакт, Запит і Дзвінки; пунктирна плашка «+ Створити замовлення».
// Результати дзвінка: Недодзвон F1 · Передзвонити F2 · Відмова F3 · Дубль. Головна дія — «Створити замовлення» (Ctrl ⏎).
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Check, ChevronLeft, Copy, MessageCircle, Phone, PhoneMissed, PhoneOff, Plus, Send, Timer } from "lucide-react";
import { api, ApiError } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { dt, money, phone } from "../lib/format";
import type { Order, OrderList } from "../lib/types";
import { Block, Button, IconButton, PropertyList, StatusPill, Window, useOutside } from "../components/ui";
import { WaitBadge, callbackTime, leadNo } from "./Leads";
import OrderModal from "./OrderCard";

type Step = { order: Order; next_id: number | null };

export default function LeadWindow({ id, onClose, onOpen }: { id: number; onClose: () => void; onOpen: (id: number) => void }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [pop, setPop] = useState<null | "callback" | "refused" | "duplicate">(null);
  const [fullCard, setFullCard] = useState(false);
  const statuses = Object.fromEntries(meta.statuses.map((s) => [s.id, s]));
  const { data: o, isLoading } = useQuery({ queryKey: ["order", id], queryFn: () => api.get<Order>(`/orders/${id}`) });
  const queue = useQuery({
    queryKey: ["orders", "leads", "queue-rows"],
    queryFn: () => api.get<OrderList>("/orders?stage=lead&tab=open&sort=wait&limit=200&counts=0"),
    refetchInterval: 30_000,
  });
  const code = o ? statuses[o.status_id]?.code : "";
  const isOpen = !!code && ["new", "no_answer", "callback"].includes(code);

  const after = (r: Step, msg: string) => {
    qc.invalidateQueries({ queryKey: ["orders"] });
    qc.invalidateQueries({ queryKey: ["counters"] });
    qc.invalidateQueries({ queryKey: ["leads"] });
    qc.setQueryData(["order", r.order.id], r.order);
    toast(msg, "ok", { action: { label: "Відкрити", onClick: () => onOpen(r.order.id) } });
    setPop(null);
    if (r.next_id) onOpen(r.next_id); else onClose();
  };
  const result = useMutation({
    mutationFn: (body: { result: string; at?: string; reason_id?: number; duplicate_of_id?: number }) => api.post<Step>(`/orders/${id}/lead-result`, body),
    onSuccess: (r, v) => after(r, { no_answer: "Недодзвон — нагадаю пізніше", callback: "Передзвонити — справу поставлено", refused: "Відмова ліда", duplicate: "Позначено як дубль" }[v.result] ?? "Готово"),
    onError: (e) => toast(errText(e), "error"),
  });
  const convert = useMutation({
    mutationFn: () => api.post<Step>(`/orders/${id}/convert`),
    onSuccess: (r) => {
      const prev = o?.status_id;
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["counters"] });
      toast(`Створено замовлення №${r.order.id}`, "ok", {
        undo: () => { if (prev) api.patch(`/orders/${r.order.id}`, { status_id: prev }).then(() => qc.invalidateQueries({ queryKey: ["orders"] })); },
      });
      if (r.next_id) onOpen(r.next_id); else onClose();
    },
    onError: (e) => {
      if (e instanceof ApiError && e.status === 422) { toast(errText(e), "warn"); setFullCard(true); return; }
      toast(errText(e), "error");
    },
  });

  // F1 / F2 / F3 і Ctrl ⏎
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (!isOpen || fullCard) return;
      if (e.key === "F1") { e.preventDefault(); result.mutate({ result: "no_answer" }); }
      else if (e.key === "F2") { e.preventDefault(); setPop("callback"); }
      else if (e.key === "F3") { e.preventDefault(); setPop("refused"); }
      else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); convert.mutate(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [isOpen, fullCard, result, convert]);

  const busy = result.isPending || convert.isPending;
  const qRows = queue.data?.items ?? [];
  const calls = (o?.history ?? []).filter((h) => /Результат дзвінка|Статус|Коментар/.test(h.action));

  const head = (
    <div className="win-head lw-head">
      <IconButton icon={ChevronLeft} label="Назад (Esc)" quiet onClick={onClose} />
      <h2>Лід {leadNo(id)}</h2>
      {o && <StatusPill status={statuses[o.status_id]} />}
      {o && <WaitBadge row={{ ...o, wait_minutes: qRows.find((r) => r.id === id)?.wait_minutes ?? null }} />}
      <div className="acts">
        {o?.duplicate_of_id && <span className="badge warn">Можливий дубль №{o.duplicate_of_id}</span>}
        {o?.customer?.blacklisted && <span className="badge bad"><Ban size={11} />У чорному списку</span>}
      </div>
    </div>
  );

  return (
    <Window size="xl" onClose={onClose} head={head} label={`Лід ${leadNo(id)}`} bodyClass="lw-body"
      footer={o && isOpen ? (
        <div className="lw-foot">
          <Button icon={PhoneMissed} kbd="F1" disabled={busy} onClick={() => result.mutate({ result: "no_answer" })}>Недодзвон</Button>
          <div className="lw-pop-wrap">
            <Button icon={Timer} kbd="F2" disabled={busy} onClick={() => setPop(pop === "callback" ? null : "callback")}>Передзвонити</Button>
            {pop === "callback" && <CallbackPop onClose={() => setPop(null)} onPick={(at) => result.mutate({ result: "callback", at })} />}
          </div>
          <div className="lw-pop-wrap">
            <Button icon={PhoneOff} kbd="F3" disabled={busy} onClick={() => setPop(pop === "refused" ? null : "refused")}>Відмова</Button>
            {pop === "refused" && <ReasonPop onClose={() => setPop(null)} onPick={(rid) => result.mutate({ result: "refused", reason_id: rid })} />}
          </div>
          <div className="lw-pop-wrap">
            <Button icon={Copy} disabled={busy} onClick={() => setPop(pop === "duplicate" ? null : "duplicate")}>Дубль</Button>
            {pop === "duplicate" && <DupPop initial={o.duplicate_of_id ?? undefined} onClose={() => setPop(null)} onPick={(did) => result.mutate({ result: "duplicate", duplicate_of_id: did })} />}
          </div>
          <span className="spacer" />
          <Button variant="primary" icon={Check} kbd="Ctrl ⏎" disabled={busy} onClick={() => convert.mutate()}>Створити замовлення</Button>
        </div>
      ) : undefined}>
      <aside className="lw-queue" aria-label="Черга дзвінків">
        <div className="lw-q-head">Черга дзвінків <span className="count">{qRows.length}</span></div>
        <div className="lw-q-list">
          {qRows.map((r) => (
            <button key={r.id} className={`lw-q-item${r.id === id ? " on" : ""}`} onClick={() => onOpen(r.id)} aria-current={r.id === id}>
              <span className="lw-q-1"><b className="ell">{r.customer_name || phone(r.phone)}</b><span className="num">{money(r.total)} ₴</span></span>
              <span className="lw-q-2"><span className="ell">{r.items[0]?.name ?? "—"}</span><WaitBadge row={r} /></span>
            </button>
          ))}
          {!qRows.length && <div className="note-empty">Черга порожня</div>}
        </div>
      </aside>
      <div className="lw-main">
        {isLoading || !o ? <div className="skel-rows">{[0, 1, 2, 3].map((i) => <div key={i} className="skel-row"><span className="skel" /></div>)}</div> : (<>
          <Block title="Контакт">
            <div className="lw-name">{o.customer_name || "Без імені"}</div>
            <div className="lw-phone-row">
              <a className="phone-pill" href={`tel:+${o.phone.replace(/\D/g, "")}`}><Phone size={14} />{phone(o.phone)}</a>
              <a className="icon-btn" href={`viber://chat?number=%2B${o.phone.replace(/\D/g, "")}`} aria-label="Viber" title="Viber"><MessageCircle size={16} /></a>
              <a className="icon-btn" href={`https://t.me/+${o.phone.replace(/\D/g, "")}`} target="_blank" rel="noreferrer" aria-label="Telegram" title="Telegram"><Send size={16} /></a>
            </div>
            {o.customer && (
              <div className="tiles4">
                <div><b>{o.customer.orders}</b><span>Замовлень</span></div>
                <div className={o.customer.buyout_rate != null && o.customer.buyout_rate < 50 ? "warn" : ""}><b>{o.customer.buyout_rate != null ? `${Math.round(o.customer.buyout_rate)}%` : "—"}</b><span>Викуп</span></div>
                <div><b>{o.customer.refused}</b><span>Відмов</span></div>
                <div><b>{money(o.customer.sum_delivered)} ₴</b><span>Сума</span></div>
              </div>
            )}
          </Block>
          <Block title="Запит" sub={o.site || undefined}>
            <PropertyList items={[
              ...o.items.map((i, n) => ({ key: `i${n}`, label: n === 0 ? "Товар" : i.upsell ? "Допродаж" : "Ще товар", value: <span>{i.name} · {i.qty} шт · <b>{money(i.price)} ₴</b></span> })),
              { key: "sum", label: "Сума", value: <b>{money(o.total)} ₴</b> },
              ...(o.comment ? [{ key: "c", label: "Відповіді форми", value: <span className="pre">{o.comment}</span> }] : []),
              ...(o.utm_source || o.utm_campaign ? [{ key: "utm", label: "UTM", value: <span className="muted">{[o.utm_source, o.utm_medium, o.utm_campaign, o.utm_content, o.utm_term].filter(Boolean).join(" · ")}</span> }] : []),
              { key: "created", label: "Надійшов", value: dt(o.created_at) },
            ]} />
          </Block>
          <Block title="Дзвінки" sub={o.call_attempts ? `${o.call_attempts} ${o.call_attempts === 1 ? "спроба" : "спроби"}` : "ще не дзвонили"}>
            {o.remind_at && <p className="lw-next"><Timer size={14} />Передзвонити {callbackTime(o.remind_at)}</p>}
            {calls.length ? (
              <ul className="lw-calls">{calls.slice(0, 8).map((h) => <li key={h.id}><span className="when">{dt(h.created_at, true)}</span><span>{h.action}{h.details ? `: ${h.details}` : ""}</span><span className="muted">{h.user}</span></li>)}</ul>
            ) : <p className="muted">Історії дзвінків ще немає</p>}
          </Block>
          {isOpen && (
            <button className="lw-create" onClick={() => setFullCard(true)}>
              <Plus size={16} /><span><b>Створити замовлення</b><small>Товари, оплата й доставка — у тих самих блоках, що й у картці замовлення</small></span>
            </button>
          )}
          {!isOpen && o.converted_at && <p className="lw-done"><Check size={15} />З ліда створено замовлення · {dt(o.converted_at, true)}</p>}
        </>)}
      </div>
      {fullCard && <OrderModal id={String(id)} onClose={() => { setFullCard(false); qc.invalidateQueries({ queryKey: ["order", id] }); }} onOpen={onOpen} />}
    </Window>
  );
}

function CallbackPop({ onPick, onClose }: { onPick: (iso: string) => void; onClose: () => void }) {
  const box = useRef<HTMLDivElement>(null);
  useOutside(box, onClose);
  const [own, setOwn] = useState("");
  const at = (f: (d: Date) => void) => { const d = new Date(); f(d); return d.toISOString(); };
  const presets: [string, string][] = [
    ["Через 30 хв", at((d) => d.setMinutes(d.getMinutes() + 30))],
    ["Через годину", at((d) => d.setHours(d.getHours() + 1))],
    ["Сьогодні о 18:00", at((d) => d.setHours(18, 0, 0, 0))],
    ["Завтра о 10:00", at((d) => { d.setDate(d.getDate() + 1); d.setHours(10, 0, 0, 0); })],
  ];
  return (
    <div className="pop lw-pop" ref={box} role="menu">
      {presets.map(([l, iso]) => <button key={l} className="pop-item" onClick={() => onPick(iso)}>{l}</button>)}
      <form className="lw-own" onSubmit={(e) => { e.preventDefault(); if (own) onPick(new Date(own).toISOString()); }}>
        <input type="datetime-local" value={own} onChange={(e) => setOwn(e.target.value)} aria-label="Свій час" />
        <Button type="submit" size={30} disabled={!own}>OK</Button>
      </form>
    </div>
  );
}

function ReasonPop({ onPick, onClose }: { onPick: (id?: number) => void; onClose: () => void }) {
  const meta = useMeta();
  const box = useRef<HTMLDivElement>(null);
  useOutside(box, onClose);
  const reasons = meta.reasons.filter((r) => r.active);
  return (
    <div className="pop lw-pop" ref={box} role="menu">
      <div className="note-head">Причина відмови</div>
      {reasons.map((r) => <button key={r.id} className="pop-item" onClick={() => onPick(r.id)}>{r.name}</button>)}
      {!reasons.length && <button className="pop-item" onClick={() => onPick(undefined)}>Без причини</button>}
    </div>
  );
}

function DupPop({ initial, onPick, onClose }: { initial?: number; onPick: (id?: number) => void; onClose: () => void }) {
  const box = useRef<HTMLFormElement>(null);
  useOutside(box, onClose);
  const [v, setV] = useState(initial ? String(initial) : "");
  return (
    <form className="pop lw-pop lw-dup" ref={box} onSubmit={(e) => { e.preventDefault(); onPick(v ? Number(v) : undefined); }}>
      <label className="lbl" htmlFor="dup-of">№ першого ліда чи замовлення</label>
      <input id="dup-of" autoFocus inputMode="numeric" value={v} onChange={(e) => setV(e.target.value.replace(/\D/g, ""))} placeholder="Напр., 1482" />
      <Button type="submit" size={30} variant="primary">Позначити дублем</Button>
    </form>
  );
}
