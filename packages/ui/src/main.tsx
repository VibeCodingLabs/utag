// Hand-written bootstrap — the ONLY non-generated frontend code.
// Everything under src/generated/ and src/styles/ comes from `utag design app`.
import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { routes } from "./generated/routes";
import "./styles/tokens.css";
import "./styles/theme.css";
import "./styles/dark.css";
import "./styles/motion.css";
import "./styles/tailwind.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={createBrowserRouter(routes)} />
  </React.StrictMode>,
);
