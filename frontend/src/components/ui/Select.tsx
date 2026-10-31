// Випадний список замість системного <select> (рішення власника 31.10: «меню має бути як скрізь — гарне»).
// Той самий API, що й у <select>: value, onChange(e => e.target.value), діти <option>/<optgroup>, disabled, className, aria-label.
// Список відкривається поверх усього (portal, position: fixed), тож не обрізається таблицями й вікнами; клавіші — ↑↓, Enter, Esc, літери.
import {
  Children, Fragment, isValidElement, useEffect, useLayoutEffect, useRef, useState,
  type ChangeEvent, type CSSProperties, type KeyboardEvent, type ReactElement, type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { Check } from "lucide-react";

type Opt = { value: string; label: string; disabled?: boolean; group?: string };
type OptProps = { value?: string | number; children?: ReactNode; disabled?: boolean; label?: string };

function textOf(n: ReactNode): string {
  if (n == null || typeof n === "boolean") return "";
  if (typeof n === "string" || typeof n === "number") return String(n);
  if (Array.isArray(n)) return n.map(textOf).join("");
  if (isValidElement(n)) return textOf((n.props as { children?: ReactNode }).children);
  return "";
}

function collect(children: ReactNode, out: Opt[], group?: string) {
  Children.forEach(children, (ch) => {
    if (!isValidElement(ch)) return;
    const el = ch as ReactElement<OptProps>;
    if (el.type === "option") out.push({ value: String(el.props.value ?? textOf(el.props.children)), label: textOf(el.props.children), disabled: el.props.disabled, group });
    else if (el.type === "optgroup") collect(el.props.children, out, el.props.label);
    else if (el.type === Fragment) collect(el.props.children, out, group);
  });
}

export type SelectProps = {
  value?: string | number | readonly string[]; defaultValue?: string | number; onChange?: (e: ChangeEvent<HTMLSelectElement>) => void;
  children?: ReactNode; disabled?: boolean; className?: string; id?: string; name?: string; title?: string; style?: CSSProperties;
  "aria-label"?: string; "aria-labelledby"?: string; autoFocus?: boolean; required?: boolean;
};

export function Select({ value, defaultValue, onChange, children, disabled, className = "", id, name, title, style, autoFocus, ...aria }: SelectProps) {
  const opts: Opt[] = [];
  collect(children, opts);
  const [inner, setInner] = useState(String(defaultValue ?? opts[0]?.value ?? ""));
  const cur = value !== undefined ? String(value) : inner;
  const sel = opts.find((o) => o.value === cur);
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const [pos, setPos] = useState<CSSProperties>({});
  const btn = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const typed = useRef({ s: "", t: 0 });

  const place = () => {
    const r = btn.current?.getBoundingClientRect();
    if (!r) return;
    const h = Math.min(320, opts.length * 40 + 12);
    const below = window.innerHeight - r.bottom - 8;
    const up = below < h && r.top > below;
    const width = Math.max(r.width, 200);
    const left = Math.max(8, Math.min(r.left, window.innerWidth - width - 8));
    setPos(up ? { left, width, bottom: window.innerHeight - r.top + 4, maxHeight: Math.min(320, r.top - 12) }
      : { left, width, top: r.bottom + 4, maxHeight: Math.min(320, below) });
  };
  const show = () => {
    if (disabled) return;
    place();
    setHl(Math.max(0, opts.findIndex((o) => o.value === cur)));
    setOpen(true);
  };
  const pick = (o?: Opt) => {
    if (!o || o.disabled) return;
    setOpen(false);
    btn.current?.focus();
    if (o.value === cur) return;
    if (value === undefined) setInner(o.value);
    const target = { value: o.value, name: name ?? "" };
    onChange?.({ target, currentTarget: target } as unknown as ChangeEvent<HTMLSelectElement>);
  };

  useLayoutEffect(() => { if (open) list.current?.querySelector<HTMLElement>(".xsel-opt.hl")?.scrollIntoView({ block: "nearest" }); }, [open, hl]);
  useEffect(() => {
    if (!open) return;
    const away = (e: Event) => {
      const t = e.target as Node;
      if (list.current?.contains(t) || btn.current?.contains(t)) return;
      setOpen(false);
    };
    const close = () => setOpen(false);
    document.addEventListener("mousedown", away, true);
    document.addEventListener("touchstart", away, true);
    window.addEventListener("resize", close);
    document.addEventListener("scroll", away, true);
    return () => {
      document.removeEventListener("mousedown", away, true);
      document.removeEventListener("touchstart", away, true);
      window.removeEventListener("resize", close);
      document.removeEventListener("scroll", away, true);
    };
  }, [open]);

  const move = (d: number) => {
    let i = hl;
    for (let k = 0; k < opts.length; k++) { i = (i + d + opts.length) % opts.length; if (!opts[i].disabled) break; }
    setHl(i);
  };
  const onKey = (e: KeyboardEvent) => {
    if (disabled) return;
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) { e.preventDefault(); show(); }
      else if (e.key.length === 1 && /\S/.test(e.key)) {  // друк літер — одразу до потрібного пункту, як у системному списку
        const now = Date.now();
        typed.current = { s: (now - typed.current.t < 700 ? typed.current.s : "") + e.key.toLowerCase(), t: now };
        const o = opts.find((x) => !x.disabled && x.label.toLowerCase().startsWith(typed.current.s));
        if (o) pick(o);
      }
      return;
    }
    if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(opts[hl]); }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setOpen(false); }
    else if (e.key === "Tab") setOpen(false);
  };

  let lastGroup: string | undefined;
  return (
    <>
      <button ref={btn} type="button" id={id} title={title ?? sel?.label} style={style} disabled={disabled} autoFocus={autoFocus}
        className={`xsel ${className}${open ? " open" : ""}${sel ? "" : " empty"}`} aria-haspopup="listbox" aria-expanded={open}
        aria-label={aria["aria-label"]} aria-labelledby={aria["aria-labelledby"]} onClick={() => (open ? setOpen(false) : show())} onKeyDown={onKey}>
        {sel?.label ?? "—"}
      </button>
      {name && <input type="hidden" name={name} value={cur} />}
      {open && createPortal(
        <div ref={list} className="xsel-list" role="listbox" aria-label={aria["aria-label"]} style={pos} onKeyDown={onKey}>
          {opts.map((o, i) => {
            const head = o.group && o.group !== lastGroup ? <div className="xsel-group" key={`g-${o.group}`}>{o.group}</div> : null;
            lastGroup = o.group;
            return (
              <Fragment key={`${o.value}-${i}`}>
                {head}
                <button type="button" role="option" aria-selected={o.value === cur} disabled={o.disabled} tabIndex={-1}
                  className={`xsel-opt${i === hl ? " hl" : ""}${o.value === cur ? " on" : ""}`}
                  onMouseEnter={() => setHl(i)} onClick={() => pick(o)}>
                  <span>{o.label}</span>{o.value === cur && <Check size={14} />}
                </button>
              </Fragment>
            );
          })}
        </div>,
        document.body,
      )}
    </>
  );
}
