import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, ROOT } from "./lib/api";
import { report } from "./lib/monitoring";
import { RealtimeProvider, ToastProvider } from "./lib/app";
import type { Meta } from "./lib/types";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import OrdersPage from "./pages/Orders";
import LeadsPage from "./pages/Leads";
import InvoicesPage from "./pages/Invoices";
import BoardPage from "./pages/Board";
import { PurchasesPage, WarehousePage } from "./pages/Catalog";
import ProductsPage from "./pages/Products";
import { AuditPage, PaymentsPage, ReportsPage } from "./pages/Finance";
import SettingsPage from "./pages/Settings";
import { LoginPage, ProfilePage } from "./pages/Auth";
import SystemPage from "./pages/System";
import StatsPage from "./pages/Stats";
import HomePage from "./pages/Home";
import CustomersPage from "./pages/Customers";
import { ErrorBoundary } from "./lib/monitoring";

const qc = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 15_000, refetchOnWindowFocus: true, retry: (n, e) => !(e instanceof ApiError && e.status < 500) && n < 2 },
    mutations: { onError: (e) => { if (!(e instanceof ApiError) || e.status >= 500) report(e); } },
  },
});

function Gate() {
  const client = useQueryClient();
  const { data, error, isLoading } = useQuery({ queryKey: ["meta"], queryFn: () => api.get<Meta>("/meta"), staleTime: 60_000 });
  useEffect(() => {
    const h = () => client.setQueryData(["meta"], undefined);
    window.addEventListener("crm:unauthorized", h);
    return () => window.removeEventListener("crm:unauthorized", h);
  }, [client]);

  if (isLoading) return <div className="empty big"><Spinner /></div>;
  if (error instanceof ApiError && error.status === 401) return <LoginPage />;
  if (error) return <div className="empty big"><h1>Немає з'єднання</h1><p>{String((error as Error).message)}</p><button className="btn" onClick={() => location.reload()}>Спробувати ще</button></div>;
  if (!data) return <LoginPage />;
  const can = (k: string) => data.nav.includes(k);

  return (
    <RealtimeProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to={can("home") ? "/home" : "/orders"} replace />} />
          {can("home") && <Route path="home" element={<HomePage />} />}
          {can("leads") && data.leads_enabled && <Route path="leads" element={<LeadsPage />} />}
          {can("leads") && data.leads_enabled && <Route path="leads/:id" element={<LeadsPage />} />}
          <Route path="orders" element={<OrdersPage key="order" />} />
          <Route path="orders/:id" element={<OrdersPage key="order" />} />
          {can("invoices") && <Route path="invoices" element={<InvoicesPage />} />}
          {can("customers") && <Route path="customers" element={<CustomersPage />} />}
          {can("customers") && <Route path="customers/:id" element={<CustomersPage />} />}
          <Route path="board" element={<BoardPage />} />
          <Route path="board/:id" element={<BoardPage />} />
          <Route path="products" element={<ProductsPage />} />
          {can("warehouse") && <Route path="warehouse" element={<WarehousePage />} />}
          {can("purchases") && <Route path="purchases" element={<PurchasesPage />} />}
          {can("payments") && <Route path="payments" element={<PaymentsPage />} />}
          {can("stats") && <Route path="stats" element={<StatsPage />} />}
          {can("reports") && <Route path="reports" element={<ReportsPage />} />}
          {can("audit") && <Route path="audit" element={<AuditPage />} />}
          {can("settings") && <Route path="settings" element={<SettingsPage />} />}
          {can("system") && <Route path="system" element={<SystemPage />} />}
          <Route path="profile" element={<ProfilePage />} />
          <Route path="*" element={<div className="empty big"><h1>Сторінку не знайдено</h1></div>} />
        </Route>
      </Routes>
    </RealtimeProvider>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <BrowserRouter basename={ROOT || "/"}>
          <ErrorBoundary area="app"><Gate /></ErrorBoundary>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
