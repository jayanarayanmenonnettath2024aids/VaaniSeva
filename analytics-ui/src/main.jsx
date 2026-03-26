import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { AnalyticsProvider } from "./context/AnalyticsContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AnalyticsProvider>
        <App />
      </AnalyticsProvider>
    </BrowserRouter>
  </React.StrictMode>
);
