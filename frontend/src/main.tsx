
// Renderizado principal de React

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ModelStatusProvider } from "./contexts/ModelStatusContext";

const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <ThemeProvider>
        <ModelStatusProvider>
          <App />
        </ModelStatusProvider>
      </ThemeProvider>
    </React.StrictMode>
  );
}
