import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { DndContext, DragOverlay, MouseSensor, TouchSensor, useDraggable, useDroppable, useSensor, useSensors, type DragEndEvent } from "@dnd-kit/core";
import { Check, Eye, EyeOff, KanbanSquare, List } from "lucide-react";
import { MobileActs, RoundButton, Segmented, Sheet, useMobile } from "../components/ui";
import { api, qs } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { ago, itemsLabel, money, phone } from "../lib/format";
import type { OrderList, OrderRow, Status } from "../lib/types";
import OrderModal from "./OrderCard";

// Канбан: колонка — статус. Перетягування картки змінює статус (з усіма діями зі складом, оплатами й SMS).
export default function BoardPage() {
  const meta = useMeta();
  const nav = useNavigate();
  const { id } = useParams();
  const toast = useToast();
  const qc = useQueryClient();
  const [showFinal, setShowFinal] = useState(() => localStorage.getItem("crm-board-final") === "1");
  const columns = meta.statuses.filter((s) => s.active && (showFinal || !s.final));

  const results = useQueries({
    queries: columns.map((s) => ({
      queryKey: ["orders", "board", s.id],
      queryFn: () => api.get<OrderList>(`/orders${qs({ status: s.id, limit: 60 })}`),
    })),
  });
  const data = useMemo(() => Object.fromEntries(columns.map((s, i) => [s.id, results[i]?.data])), [columns, results]);

  const [dragging, setDragging] = useState<OrderRow | null>(null);
  // миша — з місця (6 px), палець — довгим натиском (PointerSensor на телефоні перебивав прокрутку й не давав перетягувати)
  const sensors = useSensors(useSensor(MouseSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 8 } }));

  const move = useMutation({
    mutationFn: ({ order, to }: { order: OrderRow; to: Status }) => api.patch(`/orders/${order.id}`, { status_id: to.id }),
    onMutate: async ({ order, to }) => {
      // оптимістично: картка одразу в новій колонці
      const from = order.status_id;
      await qc.cancelQueries({ queryKey: ["orders", "board"] });
      const prevFrom = qc.getQueryData<OrderList>(["orders", "board", from]);
      const prevTo = qc.getQueryData<OrderList>(["orders", "board", to.id]);
      if (prevFrom) qc.setQueryData(["orders", "board", from], { ...prevFrom, items: prevFrom.items.filter((o) => o.id !== order.id), total: (prevFrom.total ?? 1) - 1 });
      if (prevTo) qc.setQueryData(["orders", "board", to.id], { ...prevTo, items: [{ ...order, status_id: to.id }, ...prevTo.items], total: (prevTo.total ?? 0) + 1 });
      return { from, prevFrom, prevTo, to: to.id };
    },
    onError: (e, _v, ctx) => {
      if (ctx?.prevFrom) qc.setQueryData(["orders", "board", ctx.from], ctx.prevFrom);
      if (ctx?.prevTo) qc.setQueryData(["orders", "board", ctx.to], ctx.prevTo);
      toast(errText(e), "error");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["orders"] }),
  });

  const mobile = useMobile();
  const toggleFinal = () => { const v = !showFinal; setShowFinal(v); try { localStorage.setItem("crm-board-final", v ? "1" : "0"); } catch { /* приватне вікно */ } };
  const onDragEnd = (e: DragEndEvent) => {
    setDragging(null);
    const order = e.active.data.current?.order as OrderRow | undefined;
    const to = meta.statuses.find((s) => `col-${s.id}` === e.over?.id);
    if (order && to && to.id !== order.status_id) move.mutate({ order, to });
  };

  if (mobile) return (
    <div className="page-board m-board">
      <MobileActs><RoundButton icon={showFinal ? EyeOff : Eye} label={showFinal ? "Сховати завершені" : "Показати завершені"} onClick={toggleFinal} /></MobileActs>
      <div className="head"><h1>Дошка</h1></div>
      <MobileBoard columns={columns} data={data} onOpen={(oid) => nav(`/board/${oid}`)} onMove={(order, to) => move.mutate({ order, to })} />
      {id && <OrderModal id={id} onClose={() => nav("/board")} onOpen={(oid) => nav(`/board/${oid}`)} />}
    </div>
  );
  return (
    <div className="page-board">
      <div className="head">
        <h1><span className="h-ico"><KanbanSquare size={18} /></span>Дошка</h1>
        <div className="actions">
          <Segmented label="Вигляд" value="board" onChange={(k) => { if (k === "list") nav("/orders"); }}
            items={[{ key: "list", label: "Стрічка", icon: <List size={14} /> }, { key: "board", label: "Дошка", icon: <KanbanSquare size={14} /> }]} />
          <button className="btn ghost" onClick={toggleFinal}>
            {showFinal ? <EyeOff size={15} /> : <Eye size={15} />} {showFinal ? "Сховати завершені" : "Показати завершені"}
          </button>
        </div>
      </div>
      <DndContext sensors={sensors} onDragStart={(e) => { setDragging(e.active.data.current?.order ?? null); navigator.vibrate?.(12); }} onDragEnd={onDragEnd} onDragCancel={() => setDragging(null)}>
        <p className="board-hint m-only">Щоб перенести замовлення в інший статус, утримуйте картку й перетягніть</p>
        <div className="board">
          {columns.map((s) => (
            <Column key={s.id} status={s} list={data[s.id]} onOpen={(oid) => nav(`/board/${oid}`)} />
          ))}
        </div>
        <DragOverlay dropAnimation={null}>{dragging && <Card order={dragging} overlay />}</DragOverlay>
      </DndContext>
      {id && <OrderModal id={id} onClose={() => nav("/board")} onOpen={(oid) => nav(`/board/${oid}`)} />}
    </div>
  );
}

function Column({ status, list, onOpen }: { status: Status; list?: OrderList; onOpen: (id: number) => void }) {
  const { setNodeRef, isOver } = useDroppable({ id: `col-${status.id}` });
  const sum = list?.items.reduce((s, o) => s + o.total, 0) ?? 0;
  return (
    <div className={`col ${isOver ? "over" : ""}`} ref={setNodeRef} style={{ ["--c" as string]: status.color }}>
      <div className="col-head">
        <span className="pill" style={{ ["--c" as string]: status.color }}>{status.name}</span>
        <span className="muted">{list?.total ?? ""}</span>
        <span className="spacer" />
        {sum > 0 && <small className="muted">{money(sum)} ₴</small>}
      </div>
      <div className="col-body">
        {!list && <div className="spinner sm" />}
        {list?.items.map((o) => <Draggable key={o.id} order={o} onOpen={onOpen} />)}
        {list && list.items.length === 0 && <div className="board-empty">Перетягніть сюди замовлення</div>}
        {list && list.total != null && list.total > list.items.length && <div className="hint" style={{ textAlign: "center", padding: 6 }}>ще {list.total - list.items.length} у списку</div>}
      </div>
    </div>
  );
}

function Draggable({ order, onOpen }: { order: OrderRow; onOpen: (id: number) => void }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: `o-${order.id}`, data: { order } });
  return (
    <div ref={setNodeRef} {...listeners} {...attributes} style={{ opacity: isDragging ? 0.35 : 1 }} onClick={() => onOpen(order.id)}>
      <Card order={order} />
    </div>
  );
}

function Card({ order: o, overlay = false }: { order: OrderRow; overlay?: boolean }) {
  return (
    <div className={`kcard ${overlay ? "overlay" : ""}`}>
      <div className="kcard-top"><b>№{o.id}</b><span className="muted">{ago(o.status_changed_at || o.created_at)}</span></div>
      <div className="kcard-name">{o.customer_name || phone(o.phone)}</div>
      <div className="kcard-items ell">{itemsLabel(o.items) || "без товарів"}</div>
      <div className="kcard-foot"><b>{money(o.total)} ₴</b>{o.ttn && <span className={`dstate ${o.delivery_state}`} title={o.delivery_status} />}
        {o.duplicate_of_id && <span className="badge warn">дубль</span>}</div>
    </div>
  );
}

// телефон (B14): одна колонка на весь екран, свайп між колонками (scroll-snap), угорі чипи статусів з лічильниками,
// крапки-індикатор. Перенести — довгий натиск на картку → шторка зі статусами.
function MobileBoard({ columns, data, onOpen, onMove }: {
  columns: Status[]; data: Record<number, OrderList | undefined>; onOpen: (id: number) => void; onMove: (o: OrderRow, to: Status) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const chips = useRef<HTMLDivElement>(null);
  const [idx, setIdx] = useState(0);
  const [pick, setPick] = useState<OrderRow | null>(null);
  const press = useRef<{ t: number; long: boolean }>({ t: 0, long: false });
  useEffect(() => { chips.current?.children[idx]?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" }); }, [idx]);
  const go = (i: number) => { const el = box.current; if (el) el.scrollTo({ left: i * el.clientWidth, behavior: "smooth" }); };
  return (<>
    <div className="mb-chips" ref={chips} role="tablist" aria-label="Статуси">
      {columns.map((s, i) => (
        <button key={s.id} type="button" role="tab" aria-selected={i === idx} className={`mb-chip${i === idx ? " on" : ""}`} style={{ ["--c" as string]: s.color }} onClick={() => go(i)}>
          <i />{s.name}<em>{data[s.id]?.total ?? ""}</em></button>
      ))}
    </div>
    <div className="mb-cols" ref={box} onScroll={(e) => { const el = e.currentTarget; const i = Math.round(el.scrollLeft / Math.max(1, el.clientWidth)); if (i !== idx) setIdx(i); }}>
      {columns.map((s) => {
        const list = data[s.id];
        return (
          <section key={s.id} className="mb-col" aria-label={s.name}>
            {!list && <div className="spinner sm" />}
            {list?.items.map((o) => (
              <div key={o.id} role="button" tabIndex={0} className="mb-card"
                onTouchStart={() => { press.current.long = false; press.current.t = window.setTimeout(() => { press.current.long = true; navigator.vibrate?.(12); setPick(o); }, 450); }}
                onTouchMove={() => clearTimeout(press.current.t)} onTouchEnd={() => clearTimeout(press.current.t)}
                onContextMenu={(e) => e.preventDefault()}
                onClick={() => { if (press.current.long) { press.current.long = false; return; } onOpen(o.id); }}
                onKeyDown={(e) => { if (e.key === "Enter") onOpen(o.id); }}>
                <Card order={o} />
              </div>
            ))}
            {list && list.items.length === 0 && <div className="board-empty">Тут порожньо</div>}
            {list && list.total != null && list.total > list.items.length && <div className="hint mb-more">ще {list.total - list.items.length} у списку замовлень</div>}
          </section>
        );
      })}
    </div>
    <div className="mb-dots" aria-hidden>{columns.map((s, i) => <i key={s.id} className={i === idx ? "on" : ""} />)}</div>
    {pick && (
      <Sheet title={`Перенести №${pick.id}`} onClose={() => setPick(null)}>
        <div className="m-stlist">
          {columns.map((s) => (
            <button key={s.id} type="button" className={`m-stopt${s.id === pick.status_id ? " on" : ""}`} disabled={s.id === pick.status_id}
              onClick={() => { onMove(pick, s); setPick(null); }}>
              <span className="m-stpill" style={{ ["--c" as string]: s.color }}><i />{s.name}</span>
              {s.id === pick.status_id ? <Check size={17} /> : <span className="m-stck" />}
            </button>
          ))}
        </div>
      </Sheet>
    )}
  </>);
}
