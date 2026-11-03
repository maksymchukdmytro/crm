// Підтвердження (етап A5, docs/UI-NEXT.md) замість системного window.confirm.
// const ok = await ask({ title: "Видалити замовлення №12?", text: "Резерв повернеться на склад.", action: "Видалити", danger: true });
// Вікно CRM: питання, що станеться, «Скасувати» і дія (червона для видалення). Enter — дія, Esc — скасувати.
// На телефоні — шторка знизу з великими кнопками. <ConfirmHost /> один раз у корені застосунку.
import { useEffect, useState, type ReactNode } from "react";
import { AlertTriangle, CircleHelp } from "lucide-react";
import { Window } from "./windows";
import { Button } from "./buttons";

export type ConfirmOpts = { title: string; text?: ReactNode; action?: string; cancel?: string; danger?: boolean };
type Item = ConfirmOpts & { resolve: (ok: boolean) => void };

let push: ((x: Item) => void) | null = null;

/** Питання з кнопками «Скасувати» і дія; true — користувач погодився. */
export function ask(o: ConfirmOpts | string): Promise<boolean> {
  const opts = typeof o === "string" ? { title: o } : o;
  if (!push) return Promise.resolve(window.confirm([opts.title, typeof opts.text === "string" ? opts.text : ""].filter(Boolean).join("\n\n")));
  return new Promise((resolve) => push!({ ...opts, resolve }));
}

/** Те саме, що ask(), — для компонентів. */
export const useConfirm = () => ask;

export function ConfirmHost() {
  const [queue, setQueue] = useState<Item[]>([]);
  useEffect(() => {
    push = (x) => setQueue((q) => [...q, x]);
    return () => { push = null; };
  }, []);
  const cur = queue[0];
  if (!cur) return null;
  const done = (ok: boolean) => { cur.resolve(ok); setQueue((q) => q.slice(1)); };
  const Icon = cur.danger ? AlertTriangle : CircleHelp;
  return (
    <Window size="sm" className="confirm" label={cur.title} onClose={() => done(false)}
      head={<span />}
      footer={<>
        <Button onClick={() => done(false)}>{cur.cancel ?? "Скасувати"}</Button>
        <Button variant={cur.danger ? "danger" : "primary"} data-autofocus onClick={() => done(true)}>{cur.action ?? "Так"}</Button>
      </>}>
      <div className={`cf${cur.danger ? " bad" : ""}`}>
        <span className="cf-ic" aria-hidden><Icon size={20} /></span>
        <div><h2>{cur.title}</h2>{cur.text && <p>{cur.text}</p>}</div>
      </div>
    </Window>
  );
}
