// Поля (UI-DESIGN §15): підпис над полем, помилка під ним, синій підпис «звідки взялося».
import { useId, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";
import { Minus, Plus, RotateCcw } from "lucide-react";

/** Джерело автозаповнення: «з покупця» / «змінено вручну · повернути». */
export type FromHint = { text: string; manual?: boolean; onReset?: () => void };

export function FieldBox({ label, children, hint, error, from, className = "", htmlFor }: {
  label?: ReactNode; children: ReactNode; hint?: ReactNode; error?: string | null; from?: FromHint | null; className?: string; htmlFor?: string;
}) {
  return (
    <div className={`fbox${error ? " has-err" : ""} ${className}`}>
      {label && <label className="lbl" htmlFor={htmlFor}>{label}</label>}
      {children}
      {error ? <span className="err-hint" role="alert">{error}</span>
        : from ? (
          <span className="from-hint">
            {from.manual ? "змінено вручну" : from.text}
            {from.manual && from.onReset && (
              <button type="button" className="from-reset" onClick={from.onReset}><RotateCcw size={11} /> повернути</button>
            )}
          </span>
        ) : hint ? <span className="hint">{hint}</span> : null}
    </div>
  );
}

type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> & {
  label?: ReactNode; hint?: ReactNode; error?: string | null; from?: FromHint | null;
};

export function TextInput({ label, hint, error, from, value, onChange, ...rest }: InputProps & { value: string; onChange: (v: string) => void }) {
  const id = useId();
  return (
    <FieldBox label={label} hint={hint} error={error} from={from} htmlFor={id}>
      <input id={id} value={value} onChange={(e) => onChange(e.target.value)} aria-invalid={!!error || undefined} {...rest} />
    </FieldBox>
  );
}

export function TextArea({ label, hint, error, value, onChange, rows = 3, ...rest }:
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange" | "value"> & { label?: ReactNode; hint?: ReactNode; error?: string | null; value: string; onChange: (v: string) => void }) {
  const id = useId();
  return (
    <FieldBox label={label} hint={hint} error={error} htmlFor={id}>
      <textarea id={id} rows={rows} value={value} onChange={(e) => onChange(e.target.value)} aria-invalid={!!error || undefined} {...rest} />
    </FieldBox>
  );
}

/** Сума в гривнях: число з двома знаками, «₴» праворуч. */
export function MoneyInput({ label, hint, error, from, value, onChange, ...rest }: InputProps & { value: number | string; onChange: (v: string) => void }) {
  const id = useId();
  return (
    <FieldBox label={label} hint={hint} error={error} from={from} htmlFor={id}>
      <span className="money-in">
        <input id={id} inputMode="decimal" value={value} onChange={(e) => onChange(e.target.value.replace(",", ".").replace(/[^\d.]/g, ""))}
          aria-invalid={!!error || undefined} {...rest} />
        <span className="unit" aria-hidden>₴</span>
      </span>
    </FieldBox>
  );
}

/** Телефон: лише цифри, «+380» за замовчуванням. */
export function PhoneInput({ label, hint, error, from, value, onChange, ...rest }: InputProps & { value: string; onChange: (v: string) => void }) {
  const id = useId();
  return (
    <FieldBox label={label} hint={hint} error={error} from={from} htmlFor={id}>
      <input id={id} type="tel" inputMode="tel" autoComplete="tel" placeholder="+380" value={value}
        onChange={(e) => onChange(e.target.value.replace(/[^\d+ ()-]/g, ""))} aria-invalid={!!error || undefined} {...rest} />
    </FieldBox>
  );
}

/** Кількість − 1 +. */
export function QtyStepper({ value, onChange, min = 1, max = 9999, label = "Кількість" }: {
  value: number; onChange: (v: number) => void; min?: number; max?: number; label?: string;
}) {
  const set = (v: number) => onChange(Math.max(min, Math.min(max, Math.round(v) || min)));
  return (
    <span className="qty-step" role="group" aria-label={label}>
      <button type="button" aria-label="Менше" onClick={() => set(value - 1)} disabled={value <= min}><Minus size={12} /></button>
      <input value={value} inputMode="numeric" aria-label={label} onChange={(e) => set(Number(e.target.value.replace(/\D/g, "")))} />
      <button type="button" aria-label="Більше" onClick={() => set(value + 1)} disabled={value >= max}><Plus size={12} /></button>
    </span>
  );
}

export function Toggle({ checked, onChange, label, disabled, hint }: {
  checked: boolean; onChange: (v: boolean) => void; label?: ReactNode; disabled?: boolean; hint?: ReactNode;
}) {
  return (
    <label className="toggle-row">
      <span className="switch"><input type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} /><span /></span>
      {(label || hint) && <span className="toggle-txt">{label}{hint && <small>{hint}</small>}</span>}
    </label>
  );
}
