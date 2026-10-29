import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { initMonitoring } from "./lib/monitoring";
import "./base.css";
import "./app.css";
import "./theme.css";

initMonitoring();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
