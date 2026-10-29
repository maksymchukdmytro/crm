// Вікно «Створення накладної» Нової Пошти: параметри з картки й налаштувань ключа, які можна змінити перед створенням.
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Send } from "lucide-react";
import { api } from "../lib/api";
import { errText } from "../lib/app";
import { money } from "../lib/format";
import type { TtnParams, TtnPreview } from "../lib/types";
import { Field, Modal, Spinner } from "../components/ui";

const PAYERS = { Recipient: "Одержувач", Sender: "Відправник", ThirdPerson: "Третя особа" };
const CARGO = { Parcel: "Посилка", Cargo: "Вантаж", Documents: "Документи", TiresWheels: "Шини-диски", Pallet: "Палети" };
const SERVICE = { WarehouseWarehouse: "Відділення → відділення", WarehouseDoors: "Відділення → адреса", DoorsWarehouse: "Адреса → відділення", DoorsDoors: "Адреса → адреса" };

type Seat = { length: string; width: string; height: string; weight: string };

export default function TtnDialog({ orderId, accountId, onClose, onCreate, busy }: {
  orderId: number; accountId: number | ""; onClose: () => void; busy: boolean;
  onCreate: (body: Record<string, unknown>) => void;
}) {
  const [acc, setAcc] = useState<number | "">(accountId);
  const { data, error, isFetching } = useQuery({
    queryKey: ["ttn-preview", orderId, acc],
    queryFn: () => api.get<TtnPreview>(`/orders/${orderId}/ttn/preview${acc ? `?np_account_id=${acc}` : ""}`),
  });
  const [p, setP] = useState<(Omit<TtnParams, "seats"> & { seats: Seat[] }) | null>(null);
  useEffect(() => {
    if (!data?.params) return;
    const d = data.params;
    setP({ ...d, seats: d.seats.map((x) => ({ length: String(x.length), width: String(x.width), height: String(x.height), weight: String(x.weight) })) });
    if (!acc && data.np_account_id) setAcc(data.np_account_id);
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (patch: Partial<NonNullable<typeof p>>) => setP((x) => (x ? { ...x, ...patch } : x));
  const seat = (i: number, patch: Partial<Seat>) => p && set({ seats: p.seats.map((x, j) => (j === i ? { ...x, ...patch } : x)) });
  const vol = p ? p.seats.reduce((s, x) => s + (Number(x.length) * Number(x.width) * Number(x.height)) / 4000, 0) : 0;
  const weight = p ? p.seats.reduce((s, x) => s + Number(x.weight || 0), 0) : 0;

  const submit = () => {
    if (!p) return;
    onCreate({
      np_account_id: acc || undefined, payer: p.payer, cargo_type: p.cargo_type, service_type: p.service_type,
      description: p.description, declared_cost: Number(p.declared_cost) || 1, cod_mode: p.cod_mode,
      cod_amount: p.cod_mode === "none" ? 0 : Number(p.cod_amount) || 0, cod_payer: p.cod_payer, additional_info: p.additional_info,
      seats: p.seats.map((x) => ({ length: Number(x.length), width: Number(x.width), height: Number(x.height), weight: Number(x.weight) })),
    });
  };

  return (
    <Modal onClose={onClose} size="md" title="Створення накладної · Нова Пошта">
      {error ? <p className="flash error">{errText(error)}</p> : !p ? <div className="empty"><Spinner /></div> : (
        <form className="form" onSubmit={(e) => { e.preventDefault(); submit(); }}>
          {data && (data.accounts ?? []).length > 0 && (
            <div className="cols">
              <Field label="Ключ (відправник)" hint={data.sender || undefined}>
                <select value={acc} onChange={(e) => setAcc(e.target.value ? Number(e.target.value) : "")}>
                  {(data.accounts ?? []).map((a) => <option key={a.id} value={a.id}>{a.name}{a.is_default ? " · основний" : ""}</option>)}
                </select></Field>
              <Field label="Технологія доставки"><select value={p.service_type} onChange={(e) => set({ service_type: e.target.value as TtnParams["service_type"] })}>
                {Object.entries(SERVICE).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
            </div>
          )}
          <div className="cols c3">
            <Field label="Тип відправлення"><select value={p.cargo_type} onChange={(e) => set({ cargo_type: e.target.value as TtnParams["cargo_type"] })}>
              {Object.entries(CARGO).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
            <Field label="Платник доставки"><select value={p.payer} onChange={(e) => set({ payer: e.target.value as TtnParams["payer"] })}>
              {Object.entries(PAYERS).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
            <Field label="Оголошена вартість, грн"><input value={String(p.declared_cost)} inputMode="numeric" onChange={(e) => set({ declared_cost: Number(e.target.value.replace(/\D/g, "")) || 0 })} /></Field>
          </div>

          <div className="ttn-seats">
            <div className="ttn-seats-h"><span className="lbl">Місця відправлення</span><span className="hint">об'ємна вага {vol.toFixed(2)} кг · фактична {weight.toFixed(2)} кг</span></div>
            {p.seats.map((x, i) => (
              <div className="ttn-seat" key={i}>
                <span className="muted">{i + 1}</span>
                <label><span className="lbl">Довжина, см</span><input value={x.length} inputMode="decimal" onChange={(e) => seat(i, { length: e.target.value })} /></label>
                <label><span className="lbl">Ширина, см</span><input value={x.width} inputMode="decimal" onChange={(e) => seat(i, { width: e.target.value })} /></label>
                <label><span className="lbl">Висота, см</span><input value={x.height} inputMode="decimal" onChange={(e) => seat(i, { height: e.target.value })} /></label>
                <label><span className="lbl">Вага, кг</span><input value={x.weight} inputMode="decimal" onChange={(e) => seat(i, { weight: e.target.value })} /></label>
                <button type="button" className="x" disabled={p.seats.length < 2} title="Прибрати місце" onClick={() => set({ seats: p.seats.filter((_, j) => j !== i) })}>×</button>
              </div>
            ))}
            <button type="button" className="btn sm" onClick={() => set({ seats: [...p.seats, { ...p.seats[p.seats.length - 1] }] })}><Plus size={14} /> Ще місце</button>
          </div>

          <Field label="Опис відправлення"><input value={p.description} maxLength={100} onChange={(e) => set({ description: e.target.value })} /></Field>
          <div className="cols c3">
            <Field label="Післяплата" hint={data?.prepaid ? "Вид оплати замовлення виключає післяплату" : undefined}>
              <select value={p.cod_mode} disabled={!!data?.prepaid} onChange={(e) => set({ cod_mode: e.target.value as TtnParams["cod_mode"] })}>
                <option value="none">Без післяплати</option><option value="backward">Грошовий переказ</option><option value="afterpayment">Контроль оплати</option></select></Field>
            {p.cod_mode !== "none" && <>
              <Field label="Сума, грн"><input value={String(p.cod_amount)} inputMode="decimal" onChange={(e) => set({ cod_amount: Number(e.target.value.replace(",", ".")) || 0 })} /></Field>
              <Field label="Платник переказу"><select value={p.cod_payer} onChange={(e) => set({ cod_payer: e.target.value as TtnParams["payer"] })}>
                <option value="Recipient">Одержувач</option><option value="Sender">Відправник</option></select></Field>
            </>}
          </div>
          <Field label="Додаткова інформація" hint="Друкується на ТТН, до 100 символів"><textarea rows={2} maxLength={100} value={p.additional_info} onChange={(e) => set({ additional_info: e.target.value })} /></Field>
          <div className="form-actions">
            <button className="btn primary" disabled={busy || isFetching}><Send size={14} /> Створити ТТН{p.cod_mode !== "none" ? ` · післяплата ${money(p.cod_amount)} грн` : ""}</button>
            <button type="button" className="btn" onClick={onClose}>Скасувати</button>
          </div>
        </form>
      )}
    </Modal>
  );
}
