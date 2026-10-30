// Блоки картки: блок, блок підсумку, список властивостей, чеклист, стрічка подій.
import type { ReactNode } from "react";
import { AlertCircle, Check } from "lucide-react";

export function Block({ title, sub, step, acts, children, className = "", id }: {
  title?: ReactNode; sub?: ReactNode; step?: { n: number; done?: boolean }; acts?: ReactNode; children?: ReactNode; className?: string; id?: string;
}) {
  return (
    <section className={`block ${className}`} id={id} aria-label={typeof title === "string" ? title : undefined}>
      {(title || acts) && (
        <div className="block-head">
          {step && <span className={`step${step.done ? " done" : ""}`} aria-label={step.done ? "Заповнено" : `Крок ${step.n}`}>
            {step.done ? <Check size={12} strokeWidth={3} /> : step.n}</span>}
          {title && <h2>{title}</h2>}
          {sub && <span className="sub">{sub}</span>}
          {acts && <div className="acts">{acts}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function SummaryBlock({ label, value, paid, children, foot, className = "" }: {
  label: ReactNode; value: ReactNode; paid?: boolean; children?: ReactNode; foot?: ReactNode; className?: string;
}) {
  return (
    <section className={`summary-block ${className}`}>
      <div className="lbl">{label}</div>
      <div className={`big${paid ? " paid" : ""}`}>{value}</div>
      {children && <div className="sum-rows">{children}</div>}
      {foot && <div className="sum-foot">{foot}</div>}
    </section>
  );
}

export function PropertyList({ items, className = "" }: { items: { label: ReactNode; value: ReactNode; key?: string }[]; className?: string }) {
  return (
    <dl className={`props ${className}`}>
      {items.map((i, n) => [<dt key={`t${i.key ?? n}`}>{i.label}</dt>, <dd key={`d${i.key ?? n}`}>{i.value}</dd>])}
    </dl>
  );
}

export type CheckItem = { key: string; label: ReactNode; state: "done" | "pending" | "error"; hint?: ReactNode; onClick?: () => void };

export function Checklist({ items }: { items: CheckItem[] }) {
  return (
    <div className="checklist" role="list">
      {items.map((i) => (
        <button key={i.key} type="button" role="listitem" className={`ci ${i.state}`} disabled={i.state === "done" || !i.onClick} onClick={i.onClick}
          aria-label={`${typeof i.label === "string" ? i.label : ""}${i.state === "done" ? " — зроблено" : ""}`}>
          <span className="mk" aria-hidden>{i.state === "done" ? <Check size={11} strokeWidth={3} /> : i.state === "error" ? <AlertCircle size={12} /> : null}</span>
          <span>{i.label}</span>
          {i.hint && <span className="hint">{i.hint}</span>}
        </button>
      ))}
    </div>
  );
}

export function Feed({ items }: { items: { key: string | number; icon?: ReactNode; text: ReactNode; when: ReactNode }[] }) {
  return (
    <div className="feed">
      {items.map((i) => (
        <div key={i.key} className="ev"><span className="ev-ic" aria-hidden>{i.icon}</span><div>{i.text}<div className="when">{i.when}</div></div></div>
      ))}
    </div>
  );
}

/** Сірі рядки-заглушки під час завантаження. */
export function SkeletonRows({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="skel-rows" aria-busy="true" aria-label="Завантаження">
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="skel-row">{Array.from({ length: cols }, (_, c) => <span key={c} className="skel" style={{ width: `${40 + ((r * 7 + c * 13) % 50)}%` }} />)}</div>
      ))}
    </div>
  );
}
