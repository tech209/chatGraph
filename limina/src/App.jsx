// spellbook/orin/limina/src/App.jsx
import React, { useState } from "react";
import GraphCanvas from "./components/GraphCanvas";
import NodeForm from "./components/NodeForm";
import LinkForm from "./components/LinkForm";
import PromptBar from "./components/PromptBar";
import ChatGPTImport from "./components/ChatGPTImport";
import OrinChat from "./components/OrinChat";
import "./index.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("forms"); // "forms", "chat", or "import"

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>🧠 Orin</h2>
          <div className="tab-selector">
            <button 
              className={`tab-button ${activeTab === "forms" ? "active" : ""}`}
              onClick={() => setActiveTab("forms")}
            >
              Create
            </button>
            <button 
              className={`tab-button ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => setActiveTab("chat")}
            >
              Chat
            </button>
            <button 
              className={`tab-button ${activeTab === "import" ? "active" : ""}`}
              onClick={() => setActiveTab("import")}
            >
              Import
            </button>
          </div>
        </div>

        {activeTab === "forms" && (
          <>
            <NodeForm />
            <LinkForm />
            <PromptBar />
          </>
        )}
        
        {activeTab === "chat" && (
          <OrinChat />
        )}
        
        {activeTab === "import" && (
          <ChatGPTImport />
        )}
      </aside>
      <main className="graph-area">
        <GraphCanvas />
      </main>
    </div>
  );
}
