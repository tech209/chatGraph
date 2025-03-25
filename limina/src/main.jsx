// spellbook/orin/limina/src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

const root = document.getElementById("root");

if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  document.body.innerHTML =
    "<h1 style='color: white; text-align: center; margin-top: 3rem;'>🧠 Limina UI failed to load. Missing #root.</h1>";
}
