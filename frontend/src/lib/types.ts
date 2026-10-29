// Типи даних беруться зі схеми API (src/lib/api-schema.d.ts генерується з OpenAPI бекенду:
//   python scripts/export_openapi.py && npm run gen:api).
// Якщо бекенд змінить відповідь, збірка фронтенду (tsc) покаже, де код треба оновити.
import type { components } from "./api-schema";

type S = components["schemas"];

export type User = S["UserOut"];
export type Status = S["StatusOut"];
export type Product = S["ProductOut"];
export type Carrier = S["CarrierOut"];
// Сервер завжди повертає довідники повністю — у типах вони обовʼязкові
export type Reason = Required<S["ReasonOut"]>;
export type Meta = Omit<Required<S["MetaOut"]>, "reasons"> & { reasons: Reason[] };
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
export type PaymentMethod = S["PaymentMethodOut"];
export type NpAccount = S["NpAccountOut"];
export type Shop = S["ShopOut"];
export type Cashier = S["CashierOut"];
export type Stats = S["StatsOut"];
export type StatsSummary = S["StatsSummary"];
export type StatsProduct = S["StatsProduct"];
export type StatsBreakdown = S["StatsBreakdownOut"];
export type StatsBreakdownRow = S["StatsBreakdownRow"];
export type StatsSegments = S["StatsSegmentsOut"];
export type StatsOrders = S["StatsOrdersOut"];
export type StatsOrderRow = S["StatsOrderRow"];
export type StatsOptions = S["StatsOptionsOut"];
export type TestData = S["TestDataOut"];
export type Receipt = S["ReceiptOut"];
export type ShopCheck = S["ShopCheckOut"];
export type ShopSync = S["ShopSyncOut"];
export type NpRule = S["NpRuleOut"];
export type TtnPreview = S["TtnPreviewOut"];
export type TtnParams = S["TtnParams"];
export type DirItem = S["SourceOut"];
export type Settings = Omit<Required<S["SettingsOut"]>, "reasons" | "message"> & { reasons: Reason[]; message?: string | null };
export type SystemStatus = S["SystemOut"];
export type BulkResult = S["BulkOut"];

// Тіла запитів
export type OrderInput = S["OrderIn"];

// Рядок товару у формі картки: ціна редагується як текст, key — для React
export type OrderItem = Omit<S["OrderItemOut"], "price" | "sku" | "available" | "upsell_for_name" | "base_price"> & {
  price: number | string; sku?: string; available?: number | null; key?: string; upsell_for_name?: string; base_price?: number | null;
};
