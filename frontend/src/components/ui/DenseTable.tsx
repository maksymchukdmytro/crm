// Щільна стрічка як у Notion (UI-DESIGN §4.1): рядок 31 px, шапка 32 px, рядки-групи 30 px, віртуалізація,
// вибір (квадратик, пробіл або X, Shift-клік — діапазон), дії при наведенні, сірі заглушки, порожній стан.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SkeletonRows } from "./blocks";
import { useMobile } from "./hooks";

export type DenseCol<T> = {
  key: string;
  label: ReactNode;
  /** Ширина для grid-template-columns: «64px», «minmax(120px, 1.4fr)». */
  width: string;
  align?: "right" | "center";
  render: (row: T) => ReactNode;
  /** Повний текст для підказки, коли значення обрізане трикрапкою. */
  title?: (row: T) => string | undefined;
  headTitle?: string;
  /** Де показувати на телефоні (картка): title — перший рядок, end — праворуч угорі, sub — другий рядок, hide — ні. */
  mobile?: "title" | "end" | "sub" | "hide";
};

export type DenseGroup = { key: string; label: ReactNode };

type Item<T> = { type: "group"; key: string; label: ReactNode } | { type: "row"; key: string | number; row: T; index: number };

const ROW_H = 31;
const GROUP_H = 30;

/** На телефоні колонки розкладаються в картку: що в заголовку, що праворуч, що другим рядком. */
function cardPlace<T>(cols: DenseCol<T>[]) {
  const named = cols.filter((c) => c.mobile !== "hide");
  const auto = named.filter((c) => !c.mobile);
  const end = named.filter((c) => c.mobile === "end");
  if (!end.length) { const last = [...auto].reverse().find((c) => c.align === "right"); if (last) end.push(last); }
  const title = named.filter((c) => c.mobile === "title");
  if (!title.length) title.push(...auto.filter((c) => !end.includes(c)).slice(0, 2));
  const sub = named.filter((c) => !title.includes(c) && !end.includes(c));
  return { title, end, sub };
}

export function DenseTable<T>({
  rows, cols, rowKey, groupOf, selected, onSelect, onOpen, actions, isLoading, empty, onEndReached, current, className = "", label, rowClass, mobileCard,
}: {
  rows: T[];
  cols: DenseCol<T>[];
  rowKey: (r: T) => number;
  /** Рядок-група над рядком, коли значення змінюється: { key, label }. */
  groupOf?: (r: T) => DenseGroup | null;
  selected?: Set<number>;
  onSelect?: (next: Set<number>) => void;
  onOpen?: (r: T) => void;
  actions?: (r: T) => ReactNode;
  isLoading?: boolean;
  empty?: ReactNode;
  onEndReached?: () => void;
  current?: number | null;
  className?: string;
  label?: string;
  rowClass?: (r: T) => string;
  /** Телефон: власна картка рядка (макети мобільної v2). Без неї — картка з колонок за підказками mobile. */
  mobileCard?: (r: T) => ReactNode;
}) {
  const scroll = useRef<HTMLDivElement>(null);
  const anchor = useRef<number | null>(null);
  const [focus, setFocus] = useState(-1);
  const selectable = !!onSelect && !!selected;
  const mobile = useMobile();
  const place = useMemo(() => cardPlace(cols), [cols]);
  const press = useRef<number | null>(null);

  const items = useMemo<Item<T>[]>(() => {
    const out: Item<T>[] = [];
    let last: string | null = null;
    rows.forEach((r, index) => {
      const g = groupOf?.(r);
      if (g && g.key !== last) { out.push({ type: "group", key: `g-${g.key}`, label: g.label }); last = g.key; }
      out.push({ type: "row", key: rowKey(r), row: r, index });
    });
    return out;
  }, [rows, groupOf, rowKey]);

  const v = useVirtualizer({
    count: items.length, getScrollElement: () => scroll.current, overscan: 16,
    estimateSize: (i) => (items[i]?.type === "group" ? GROUP_H : ROW_H),
    getItemKey: (i) => items[i]?.key ?? i,
  });
  const vItems = v.getVirtualItems();
  useEffect(() => {
    if (mobile) return;
    const lastV = vItems[vItems.length - 1];
    if (lastV && lastV.index >= items.length - 25) onEndReached?.();
  }, [vItems, items.length, onEndReached, mobile]);

  const grid = (selectable ? "34px " : "") + cols.map((c) => c.width).join(" ") + (actions ? " 0px" : "");
  const allSel = selectable && rows.length > 0 && rows.every((r) => selected!.has(rowKey(r)));

  const toggle = (r: T, shift: boolean) => {
    if (!selectable) return;
    const id = rowKey(r);
    const idx = rows.indexOf(r);
    const next = new Set(selected);
    if (shift && anchor.current != null) {
      const [a, b] = [anchor.current, idx].sort((x, y) => x - y);
      const on = !selected!.has(id);
      for (let i = a; i <= b; i++) on ? next.add(rowKey(rows[i])) : next.delete(rowKey(rows[i]));
    } else {
      next.has(id) ? next.delete(id) : next.add(id);
    }
    anchor.current = idx;
    onSelect!(next);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (!rows.length) return;
    if (e.key === "ArrowDown" || e.key === "j") { e.preventDefault(); setFocus((f) => Math.min(f + 1, rows.length - 1)); }
    else if (e.key === "ArrowUp" || e.key === "k") { e.preventDefault(); setFocus((f) => Math.max(f - 1, 0)); }
    else if ((e.key === " " || e.key.toLowerCase() === "x") && focus >= 0) { e.preventDefault(); toggle(rows[focus], e.shiftKey); }
    else if (e.key === "Enter" && focus >= 0) { e.preventDefault(); onOpen?.(rows[focus]); }
  };
  useEffect(() => {
    if (focus < 0) return;
    const i = items.findIndex((it) => it.type === "row" && it.index === focus);
    if (i >= 0) v.scrollToIndex(i, { align: "auto" });
  }, [focus]); // eslint-disable-line react-hooks/exhaustive-deps

  // телефон: звичайний список карток без віртуалізації, гортається вся сторінка; підвантаження — коли низ списку видно
  const sentinel = useRef<HTMLDivElement>(null);
  const endRef = useRef(onEndReached);
  endRef.current = onEndReached;
  useEffect(() => {
    if (!mobile || !sentinel.current) return;
    const io = new IntersectionObserver((e) => { if (e[0]?.isIntersecting) endRef.current?.(); }, { rootMargin: "600px" });
    io.observe(sentinel.current);
    return () => io.disconnect();
  }, [mobile, rows.length]);

  if (mobile) {
    const cell = (r: T, c: DenseCol<T>) => <span key={c.key} className={`c-${c.key}`}>{c.render(r)}</span>;
    return (
      <div className={`m-list ${className}`} role="list" aria-label={label}>
        {isLoading && Array.from({ length: 5 }, (_, i) => <div key={i} className="m-card m-skel" aria-hidden><i /><i /><i /></div>)}
        {!isLoading && rows.length === 0 && <div className="m-card m-empty">{empty}</div>}
        {items.map((it) => {
          if (it.type === "group") return <div key={it.key} className="m-group">{it.label}</div>;
          const r = it.row;
          const id = rowKey(r);
          const on = selectable && selected!.has(id);
          return (
            // довге натискання — вибрати (знизу панель масових дій), коротке — відкрити
            <div key={it.key} role="listitem" aria-selected={on || undefined} tabIndex={0}
              className={`m-card${on ? " sel" : ""}${current === id ? " cur" : ""} ${rowClass?.(r) ?? ""}`}
              onTouchStart={() => { if (!selectable) return; press.current = window.setTimeout(() => { press.current = -1; toggle(r, false); }, 480); }}
              onTouchEnd={() => { if (press.current && press.current > 0) clearTimeout(press.current); }}
              onTouchMove={() => { if (press.current && press.current > 0) clearTimeout(press.current); press.current = null; }}
              onContextMenu={(e) => { if (selectable) e.preventDefault(); }}
              onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) onOpen?.(r); }}
              onClick={(e) => {
                const t = e.target as HTMLElement;
                if (press.current === -1) { press.current = null; return; }
                if (t.closest("input, button, a, .c-sel, .m-stop")) return;
                if (selectable && selected!.size > 0) { toggle(r, false); return; }
                onOpen?.(r);
              }}>
              {mobileCard ? mobileCard(r) : (<>
                <div className="dc-top"><span className="dc-title">{place.title.map((c) => cell(r, c))}</span>{place.end.length > 0 && <span className="dc-end">{place.end.map((c) => cell(r, c))}</span>}</div>
                {place.sub.length > 0 && <div className="dc-sub">{place.sub.map((c) => cell(r, c))}</div>}
              </>)}
            </div>
          );
        })}
        <div ref={sentinel} className="m-sentinel" aria-hidden />
      </div>
    );
  }

  return (
    <div className={`dense ${className}`} role="grid" aria-label={label} aria-rowcount={rows.length} aria-multiselectable={selectable || undefined}>
      <div className="dense-head dense-row" style={{ gridTemplateColumns: grid }} role="row">
        {selectable && (
          <span className="c-sel" role="columnheader">
            <input type="checkbox" aria-label="Вибрати всі" checked={allSel} onChange={() => onSelect!(allSel ? new Set() : new Set(rows.map(rowKey)))} />
          </span>
        )}
        {cols.map((c) => <span key={c.key} role="columnheader" className={c.align ? `a-${c.align}` : ""} title={c.headTitle}>{c.label}</span>)}
        {actions && <span aria-hidden />}
      </div>
      <div className="dense-body" ref={scroll} tabIndex={0} onKeyDown={onKey} onBlur={() => setFocus(-1)} aria-label={label ? `${label}: стрілки — перехід, пробіл — вибрати, Enter — відкрити` : undefined}>
        {isLoading && <SkeletonRows rows={14} cols={Math.min(cols.length, 8)} />}
        {!isLoading && rows.length === 0 && <div className="dense-empty">{empty}</div>}
        <div style={{ height: v.getTotalSize(), position: "relative" }}>
          {vItems.map((vi) => {
            const it = items[vi.index];
            if (!it) return null;
            if (it.type === "group") {
              return <div key={it.key} className="dense-group" style={{ transform: `translateY(${vi.start}px)`, height: GROUP_H }} role="row">{it.label}</div>;
            }
            const r = it.row;
            const id = rowKey(r);
            const on = selectable && selected!.has(id);
            return (
              <div key={it.key} role="row" aria-selected={on || undefined}
                className={`dense-row${on ? " sel" : ""}${current === id ? " cur" : ""}${focus === it.index ? " focus" : ""} ${rowClass?.(r) ?? ""}`}
                style={{ gridTemplateColumns: grid, transform: `translateY(${vi.start}px)`, height: ROW_H }}
                onClick={(e) => {
                  const t = e.target as HTMLElement;
                  if (t.closest("input, button, a, .c-sel")) return;
                  if (e.shiftKey && selectable) { e.preventDefault(); toggle(r, true); return; }
                  onOpen?.(r);
                }}>
                {selectable && (
                  <span className="c-sel" onClick={(e) => { e.stopPropagation(); toggle(r, e.shiftKey); }}>
                    <input type="checkbox" aria-label={`Вибрати ${id}`} checked={on} readOnly tabIndex={-1} />
                  </span>
                )}
                {cols.map((c) => (
                  <span key={c.key} role="gridcell" className={`${c.align ? `a-${c.align}` : ""} c-${c.key}`} title={c.title?.(r)}>{c.render(r)}</span>
                ))}
                {actions && <span className="dense-acts" onClick={(e) => e.stopPropagation()}>{actions(r)}</span>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
