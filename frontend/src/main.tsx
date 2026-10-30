import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { initMonitoring } from "./lib/monitoring";
import "@fontsource-variable/onest";
import "@fontsource-variable/jetbrains-mono";
import "./base.css";
import "./app.css";
import "./theme.css";
import "./ui.css";
import "./shell.css";
import "./list.css";
import "./leads.css";
import "./card.css";
import "./catalog.css";

initMonitoring();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
