// «Колонки»: користувач вмикає й перетягує колонки списку; вибір зберігається для нього (user_prefs).
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Columns3, GripVertical, RotateCcw } from "lucide-react";
import { api } from "../../lib/api";
import { useMeta } from "../../lib/app";
import { MenuButton } from "./bars";

export type ColDef = { key: string; label: string; locked?: boolean };

/** Видимі колонки в порядку користувача. Нові колонки, яких ще немає в збереженому списку, не з'являються самі. */
export function useColumns(prefKey: string, all: ColDef[], defaults: string[]) {
  const meta = useMeta();
  const qc = useQueryClient();
  const saved = meta.prefs?.[prefKey];
  const order: string[] = Array.isArray(saved) && saved.length ? (saved as string[]).filter((k) => all.some((c) => c.key === k)) : defaults;
  const locked = all.filter((c) => c.locked).map((c) => c.key);
  const visible = [...locked.filter((k) => !order.includes(k)), ...order];
  const save = useMutation({
    mutationFn: (value: string[] | null) => api.put(`/me/prefs/${prefKey}`, { value }),
    onMutate: (value) => qc.setQueryData(["meta"], (m: typeof meta | undefined) => m && ({ ...m, prefs: { ...m.prefs, [prefKey]: value ?? undefined } })),
    onSettled: () => qc.invalidateQueries({ queryKey: ["meta"] }),
  });
  return { visible, set: (keys: string[]) => save.mutate(keys), reset: () => save.mutate(null) };
}

export function ColumnsMenu({ all, visible, onChange, onReset }: {
  all: ColDef[]; visible: string[]; onChange: (keys: string[]) => void; onReset: () => void;
}) {
  const [drag, setDrag] = useState<string | null>(null);
  const ordered = [...visible.map((k) => all.find((c) => c.key === k)!).filter(Boolean), ...all.filter((c) => !visible.includes(c.key))];
  const move = (from: string, to: string) => {
    if (from === to || !visible.includes(from)) return;
    const next = visible.filter((k) => k !== from);
    const at = visible.includes(to) ? next.indexOf(to) : next.length;
    next.splice(at, 0, from);
    onChange(next);
  };
  return (
    <MenuButton button={({ open, toggle }) => (
      <button className="btn" aria-haspopup="menu" aria-expanded={open} onClick={toggle}><Columns3 size={15} />Колонки</button>
    )}>
      {() => (
        <div className="cols-menu">
          <div className="note-head">Перетягніть, щоб змінити порядок</div>
          {ordered.map((c) => {
            const on = visible.includes(c.key);
            return (
              <div key={c.key} className={`cols-item${drag === c.key ? " drag" : ""}`} draggable={on && !c.locked}
                onDragStart={() => setDrag(c.key)} onDragEnd={() => setDrag(null)}
                onDragOver={(e) => { e.preventDefault(); if (drag) move(drag, c.key); }}>
                <GripVertical size={14} className="grip" aria-hidden />
                <label className="cols-lbl">
                  <input type="checkbox" checked={on} disabled={c.locked}
                    onChange={() => onChange(on ? visible.filter((k) => k !== c.key) : [...visible, c.key])} />
                  <span>{c.label}</span>
                </label>
              </div>
            );
          })}
          <button className="pop-item" onClick={onReset}><RotateCcw size={14} />Як було</button>
        </div>
      )}
    </MenuButton>
  );
}
