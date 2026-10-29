import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { DndContext, DragOverlay, PointerSensor, TouchSensor, useDraggable, useDroppable, useSensor, useSensors, type DragEndEvent } from "@dnd-kit/core";
import { Eye, EyeOff, KanbanSquare } from "lucide-react";
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
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 220, tolerance: 6 } }));

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

  const onDragEnd = (e: DragEndEvent) => {
    setDragging(null);
    const order = e.active.data.current?.order as OrderRow | undefined;
    const to = meta.statuses.find((s) => `col-${s.id}` === e.over?.id);
    if (order && to && to.id !== order.status_id) move.mutate({ order, to });
  };

  return (
    <div className="page-board">
      <div className="head">
        <h1><span className="h-ico"><KanbanSquare size={18} /></span>Дошка</h1>
        <div className="actions">
          <button className="btn ghost" onClick={() => { const v = !showFinal; setShowFinal(v); localStorage.setItem("crm-board-final", v ? "1" : "0"); }}>
            {showFinal ? <EyeOff size={15} /> : <Eye size={15} />} {showFinal ? "Сховати завершені" : "Показати завершені"}
          </button>
        </div>
      </div>
      <DndContext sensors={sensors} onDragStart={(e) => setDragging(e.active.data.current?.order ?? null)} onDragEnd={onDragEnd} onDragCancel={() => setDragging(null)}>
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
