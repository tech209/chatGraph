// spellbook/limina/src/components/PromptBar.jsx
import React, { useState } from "react";
import axios from "axios";

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;
const MNEMOS_API = import.meta.env.VITE_MNEMOS_API || "http://localhost:8000";

export default function PromptBar() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [responsePreview, setResponsePreview] = useState(null);

  const promptExamples = [
    "Remember Project X is a new initiative to improve search speed",
    "Link Project X to Task Y with relation 'contains'",
    "Remember that Task Z is a critical dependency with deadline next Friday"
  ];

  const handleExample = (example) => {
    setPrompt(example);
    setShowExamples(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    setLoading(true);
    setResponsePreview(null);
    
    try {
      const response = await axios.post(
        "https://api.openai.com/v1/chat/completions",
        {
          model: "gpt-4",
          messages: [
            {
              role: "system",
              content: `
You are Orin, a memory archivist.
You only output valid minified JSON.
Respond using one of the two following forms:
{ "intent": "remember", "label": "ProjectX", "type": "project", "meta": { "notes": "..." } }
{ "intent": "link", "source": "ProjectX", "target": "IdeaY", "relation": "related_to" }
Do NOT include any other explanation. Do not include markdown.
              `,
            },
            {
              role: "user",
              content: prompt,
            },
          ],
        },
        {
          headers: {
            Authorization: `Bearer ${OPENAI_API_KEY}`,
            "Content-Type": "application/json",
          },
        }
      );
      
      const content = response.data.choices[0].message.content;
      console.log("🔍 GPT response:", content);
      
      let parsed;
      try {
        parsed = JSON.parse(content.trim());
        
        // Show preview of what's about to happen
        setResponsePreview(parsed);
        
      } catch (jsonErr) {
        console.error("❌ Failed to parse GPT output:", content);
        alert("GPT did not return valid JSON. Try simplifying your prompt.");
        return;
      }
    } catch (err) {
      console.error("❌ Error during GPT call:", err);
      alert("Something went wrong with the AI request. Check the console for details.");
    } finally {
      setLoading(false);
    }
  };

  const confirmAction = async () => {
    if (!responsePreview) return;
    
    try {
      if (responsePreview.intent === "remember") {
        await axios.post(`${MNEMOS_API}/node`, {
          label: responsePreview.label,
          type: responsePreview.type,
          meta: responsePreview.meta || {},
        });
        
      } else if (responsePreview.intent === "link") {
        await axios.post(`${MNEMOS_API}/link`, {
          source: responsePreview.source,
          target: responsePreview.target,
          relation: responsePreview.relation,
        });
        
      } else {
        alert(`Unknown intent '${responsePreview.intent}'`);
        return;
      }
      
      // Success - clear everything
      setResponsePreview(null);
      setPrompt("");
      window.location.reload(); // simple refresh for now
      
    } catch (err) {
      console.error("❌ Error during memory operation:", err);
      alert("Failed to update memory. Check the console for details.");
    }
  };

  const cancelAction = () => {
    setResponsePreview(null);
  };

  return (
    <div className="form-box">
      <div className="form-header">
        <h3>💬 Orin Assistant</h3>
        <button 
          type="button"
          className="toggle-button"
          onClick={() => setShowExamples(!showExamples)}
        >
          {showExamples ? "Hide Examples" : "Show Examples"}
        </button>
      </div>
      
      {showExamples && (
        <div className="examples-container">
          <p className="examples-title">Try these:</p>
          <div className="examples-list">
            {promptExamples.map((example, index) => (
              <div key={index} className="example-item" onClick={() => handleExample(example)}>
                {example}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {!responsePreview ? (
        <form onSubmit={handleSubmit}>
          <textarea
            placeholder="Ask Orin to remember information or create links..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            className="form-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading || !prompt.trim()}
          >
            {loading ? "🌀 Processing..." : "Send to Orin"}
          </button>
        </form>
      ) : (
        <div className="preview-container">
          <div className="preview-header">
            {responsePreview.intent === "remember" ? (
              <h4>Creating New Node</h4>
            ) : (
              <h4>Creating New Link</h4>
            )}
          </div>
          
          <div className="preview-content">
            {responsePreview.intent === "remember" && (
              <>
                <div className="preview-item">
                  <span className="preview-label">Label:</span>
                  <span className="preview-value">{responsePreview.label}</span>
                </div>
                <div className="preview-item">
                  <span className="preview-label">Type:</span>
                  <span className="preview-value">{responsePreview.type}</span>
                </div>
                {responsePreview.meta && Object.keys(responsePreview.meta).length > 0 && (
                  <div className="preview-item">
                    <span className="preview-label">Metadata:</span>
                    <pre className="preview-json">
                      {JSON.stringify(responsePreview.meta, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            )}
            
            {responsePreview.intent === "link" && (
              <>
                <div className="preview-item">
                  <span className="preview-label">From:</span>
                  <span className="preview-value">{responsePreview.source}</span>
                </div>
                <div className="preview-item">
                  <span className="preview-label">Relation:</span>
                  <span className="preview-value">{responsePreview.relation}</span>
                </div>
                <div className="preview-item">
                  <span className="preview-label">To:</span>
                  <span className="preview-value">{responsePreview.target}</span>
                </div>
              </>
            )}
          </div>
          
          <div className="preview-actions">
            <button 
              className="cancel-btn" 
              onClick={cancelAction}
            >
              Cancel
            </button>
            <button 
              className="confirm-btn" 
              onClick={confirmAction}
            >
              Confirm
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
