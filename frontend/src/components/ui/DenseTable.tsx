// Щільна стрічка як у Notion (UI-DESIGN §4.1): рядок 31 px, шапка 32 px, рядки-групи 30 px, віртуалізація,
// вибір (квадратик, пробіл або X, Shift-клік — діапазон), дії при наведенні, сірі заглушки, порожній стан.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SkeletonRows } from "./blocks";

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
};

export type DenseGroup = { key: string; label: ReactNode };

type Item<T> = { type: "group"; key: string; label: ReactNode } | { type: "row"; key: string | number; row: T; index: number };

const ROW_H = 31;
const GROUP_H = 30;

export function DenseTable<T>({
  rows, cols, rowKey, groupOf, selected, onSelect, onOpen, actions, isLoading, empty, onEndReached, current, className = "", label, rowClass,
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
}) {
  const scroll = useRef<HTMLDivElement>(null);
  const anchor = useRef<number | null>(null);
  const [focus, setFocus] = useState(-1);
  const selectable = !!onSelect && !!selected;

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
    const lastV = vItems[vItems.length - 1];
    if (lastV && lastV.index >= items.length - 25) onEndReached?.();
  }, [vItems, items.length, onEndReached]);

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
