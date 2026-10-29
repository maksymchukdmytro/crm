// Типи даних беруться зі схеми API (src/lib/api-schema.d.ts генерується з OpenAPI бекенду:
//   python scripts/export_openapi.py && npm run gen:api).
// Якщо бекенд змінить відповідь, збірка фронтенду (tsc) покаже, де код треба оновити.
import type { components } from "./api-schema";

type S = components["schemas"];

export type User = S["UserOut"];
export type Status = S["StatusOut"];
export type Product = S["ProductOut"];
export type Carrier = S["CarrierOut"];
export type Meta = S["MetaOut"];
export type OrderRow = S["OrderRowOut"];
export type OrderList = S["OrderListOut"];
export type Order = S["OrderOut"];
export type Payment = S["PaymentOut"];
export type Move = S["MoveOut"];
export type Purchase = S["PurchaseOut"];
export type Supplier = S["SupplierOut"];
export type ProductDetail = S["ProductDetailOut"];
export type Warehouse = S["WarehouseOut"];
export type Payments = S["PaymentsOut"];
export type Registry = S["RegistryOut"];
export type Report = S["ReportOut"];
export type Audit = S["AuditOut"];
export type Settings = S["SettingsOut"];
export type SystemStatus = S["SystemOut"];
export type BulkResult = S["BulkOut"];

// Тіла запитів
export type OrderInput = S["OrderIn"];

// Рядок товару у формі картки: ціна редагується як текст, key — для React
export type OrderItem = Omit<S["OrderItemOut"], "price" | "sku" | "available" | "upsell_for_name" | "base_price"> & {
  price: number | string; sku?: string; available?: number | null; key?: string; upsell_for_name?: string; base_price?: number | null;
};
