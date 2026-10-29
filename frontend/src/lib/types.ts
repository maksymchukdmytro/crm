export interface User {
  id: number; username: string; name: string; full_name: string; role: "admin" | "manager" | "warehouse";
  role_name: string; is_active: boolean; last_login_at: string | null;
}

export interface Status {
  id: number; code: string; name: string; color: string; sort: number; stock_action: string;
  approved: boolean; final: boolean; system: boolean; active: boolean;
}

export interface Product {
  id: number; sku: string; name: string; price: number; cost: number; weight: number; stock: number;
  reserved: number; available: number; min_stock: number; upsell: boolean; active: boolean;
}

export interface Carrier { name: string; beta: boolean; configured: boolean }

export interface Meta {
  user: User; company: string; nav: string[]; statuses: Status[]; managers: User[]; products: Product[];
  delivery_methods: Record<string, string>; delivery_states: Record<string, string>;
  payment_types: Record<string, string>; payment_kinds: Record<string, string>;
  payment_statuses: Record<string, string>; stock_actions: Record<string, string>; roles: Record<string, string>;
  carriers: Record<string, Carrier>; sms_ready: boolean; managers_see_own_only: boolean; realtime: boolean; root: string;
}

export interface OrderRow {
  id: number; status_id: number; manager_id: number | null; customer_name: string; phone: string;
  items: { name: string; qty: number; upsell: boolean }[]; total: number; cod_amount: number; payment_type: string;
  delivery_method: string; city_name: string; ttn: string; delivery_state: string; delivery_status: string;
  utm_source: string; utm_campaign: string; site: string; duplicate_of_id: number | null; created_at: string;
  status_changed_at: string;
}

export interface OrderItem {
  id?: number; product_id: number | null; name: string; price: number | string; qty: number; upsell: boolean;
  sku?: string; available?: number | null; key?: string;
}

export interface Payment {
  id: number; order_id: number; kind: string; kind_name: string; amount: number; status: string; status_name: string;
  method: string; reference: string; received_amount: number | null; created_at: string;
  collected_at: string | null; received_at: string | null; ttn?: string; customer?: string;
}

export interface Order {
  id: number; status_id: number; manager_id: number | null; manager: User | null;
  customer_name: string; phone: string; email: string; comment: string;
  delivery_method: string; city_name: string; city_ref: string; warehouse_name: string; warehouse_ref: string;
  address: string; postcode: string; ttn: string; carrier_ref: string; delivery_state: string; delivery_status: string;
  payment_type: string; site: string; utm_source: string; utm_medium: string; utm_campaign: string;
  utm_content: string; utm_term: string; ip: string;
  delivery_cost: number; prepayment: number; discount: number; total: number; cod_amount: number;
  duplicate_of_id: number | null; stock_reserved: boolean; stock_shipped: boolean;
  created_at: string; updated_at: string; delivery_checked_at: string | null; version: string;
  items: OrderItem[]; payments: Payment[];
  comments: { id: number; text: string; user: string; created_at: string }[];
  history: { id: number; user: string; action: string; details: string; created_at: string }[];
  sms: { id: number; text: string; channel: string; status: string; error: string; created_at: string }[];
  others: OrderRow[];
}

export interface OrderList { items: OrderRow[]; next: number | null; total?: number; counts?: Record<string, number>; all?: number }

export interface Move {
  id: number; product_id: number; product: string; kind: string; kind_name: string; stock_delta: number;
  reserved_delta: number; order_id: number | null; purchase_id: number | null; user: string; comment: string; created_at: string;
}

export interface Purchase {
  id: number; supplier_id: number | null; supplier: string; status: string; comment: string; total: number;
  created_at: string; received_at: string | null;
  items: { id?: number; product_id: number; name: string; qty: number; cost: number }[];
}

export interface Supplier { id: number; name: string; phone: string; comment: string }
