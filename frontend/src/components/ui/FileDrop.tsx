// Файли (етап A9, docs/UI-NEXT.md) замість системного <input type="file">.
// FileDrop — зона «Перетягніть сюди або оберіть файл» з прев'ю картинки, назвою й розміром.
// FileButton — кнопка для панелей («Імпорт реєстру НП»); файл можна й перетягнути на неї.
import { useRef, useState, type DragEvent, type ReactNode } from "react";
import { ImagePlus, Upload, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const size = (b: number) => (b < 1024 ? `${b} Б` : b < 1048576 ? `${Math.round(b / 1024)} КБ` : `${(b / 1048576).toFixed(1)} МБ`);
const fits = (f: File, accept?: string) => !accept || accept.split(",").some((a) => {
  const t = a.trim().toLowerCase();
  return t.startsWith(".") ? f.name.toLowerCase().endsWith(t) : t.endsWith("/*") ? f.type.startsWith(t.slice(0, -1)) : f.type === t;
});

function useDrop(onFiles: (fs: File[]) => void, accept?: string, disabled?: boolean) {
  const [over, setOver] = useState(false);
  return {
    over,
    props: {
      onDragOver: (e: DragEvent) => { if (disabled || !e.dataTransfer.types.includes("Files")) return; e.preventDefault(); setOver(true); },
      onDragLeave: () => setOver(false),
      onDrop: (e: DragEvent) => {
        if (disabled || !e.dataTransfer.files.length) return;
        e.preventDefault(); setOver(false);
        const fs = [...e.dataTransfer.files].filter((f) => fits(f, accept));
        if (fs.length) onFiles(fs);
      },
    },
  };
}

/** Зона для файлу: прев'ю (src) або підказка; клік, Enter чи перетягування — вибір файлу. */
export function FileDrop({ accept, onFile, preview, hint, label = "Перетягніть сюди або оберіть файл", onClear, disabled, busy }: {
  accept?: string; onFile: (f: File) => void; preview?: string | null; hint?: ReactNode; label?: string;
  onClear?: () => void; disabled?: boolean; busy?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [last, setLast] = useState<File | null>(null);
  const pick = (f: File) => { setLast(f); onFile(f); };
  const { over, props } = useDrop((fs) => pick(fs[0]), accept, disabled);
  return (
    <div className={`fdrop${over ? " over" : ""}${preview ? " has" : ""}${busy ? " busy" : ""}`} {...props}>
      <button type="button" className="fdrop-zone" disabled={disabled} onClick={() => input.current?.click()} aria-label={label}>
        {preview ? <img src={preview} alt="" /> : <span className="fdrop-ic"><ImagePlus size={20} /></span>}
        <span className="fdrop-t">
          <b>{preview ? "Замінити — перетягніть або оберіть" : label}</b>
          <small>{last ? `${last.name} · ${size(last.size)}` : hint}</small>
        </span>
      </button>
      {preview && onClear && <button type="button" className="fdrop-x" aria-label="Прибрати файл" onClick={() => { setLast(null); onClear(); }}><X size={15} /></button>}
      <input ref={input} type="file" accept={accept} hidden onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) pick(f); }} />
    </div>
  );
}

/** Кнопка вибору файлу для панелей; на неї можна й перетягнути файл. */
export function FileButton({ accept, onFile, children, icon: Icon = Upload, busy, className = "" }: {
  accept?: string; onFile: (f: File) => void; children: ReactNode; icon?: LucideIcon; busy?: boolean; className?: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  const { over, props } = useDrop((fs) => onFile(fs[0]), accept, busy);
  return (
    <>
      <button type="button" className={`btn${over ? " drop-over" : ""} ${className}`} disabled={busy} onClick={() => input.current?.click()} {...props}>
        {busy ? <span className="spinner sm" /> : <Icon size={15} />}{children}
      </button>
      <input ref={input} type="file" accept={accept} hidden onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) onFile(f); }} />
    </>
  );
}
