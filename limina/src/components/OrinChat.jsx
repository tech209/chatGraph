// spellbook/limina/src/components/OrinChat.jsx
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

const MNEMOS_API = import.meta.env.VITE_MNEMOS_API || "http://localhost:8000";

export default function OrinChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [sources, setSources] = useState([]);
  
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  
  // Send query to the backend
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user message to the chat
    setMessages(prev => [...prev, {
      role: "user",
      content: input
    }]);
    
    // Clear input and set loading state
    setInput("");
    setIsLoading(true);
    setSources([]);
    
    try {
      const response = await axios.post(`${MNEMOS_API}/api/query`, {
        query: input,
        max_results: 5
      });
      
      // Add assistant message to the chat
      setMessages(prev => [...prev, {
        role: "assistant",
        content: response.data.answer
      }]);
      
      // Store sources for potential display
      if (response.data.sources && response.data.sources.length > 0) {
        setSources(response.data.sources);
      } else {
        setSources([]);
      }
      
    } catch (error) {
      console.error("Error querying Orin:", error);
      
      // Add error message to the chat
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I encountered an error processing your request. Please try again."
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Toggle sources display
  const toggleSources = () => {
    setShowSources(prev => !prev);
  };
  
  return (
    <div className="form-box chat-container">
      <div className="form-header">
        <h3>💬 Chat with Orin</h3>
        {sources.length > 0 && (
          <button 
            type="button" 
            className="toggle-button"
            onClick={toggleSources}
          >
            {showSources ? "Hide Sources" : "Show Sources"}
          </button>
        )}
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <p>Hello! I'm Orin, your memory assistant. Ask me about anything in your knowledge graph.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div 
              key={index} 
              className={`chat-message ${message.role === "user" ? "user-message" : "assistant-message"}`}
            >
              <div className="message-bubble">
                {message.content}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="chat-message assistant-message">
            <div className="message-bubble loading-bubble">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {showSources && sources.length > 0 && (
        <div className="sources-container">
          <h4>Sources:</h4>
          <div className="sources-list">
            {sources.map((source, index) => (
              <div key={index} className="source-item">
                <span className="source-label">{source.label}</span>
                <span className="source-type">{source.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Orin a question..."
          disabled={isLoading}
          className="chat-input"
        />
        <button 
          type="submit" 
          className="send-button"
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
