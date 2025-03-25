// spellbook/limina/src/components/ChatGPTImport.jsx
import React, { useState } from "react";
import axios from "axios";

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;
const MNEMOS_API = import.meta.env.VITE_MNEMOS_API || "http://localhost:8000";

export default function ChatGPTImport() {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [importStatus, setImportStatus] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setImportStatus(null);
    }
  };

  const processConversation = async (conversation) => {
    // Extract title and conversation content
    const { title, mapping } = conversation;
    
    // Convert the mapping object to an array and sort by timestamp
    const messages = Object.values(mapping)
      .filter(msg => msg.message && msg.message.content && msg.message.content.parts)
      .sort((a, b) => new Date(a.create_time) - new Date(b.create_time));
    
    // Skip empty conversations
    if (messages.length === 0) return null;
    
    // Create conversation node
    const conversationNode = {
      label: title || "Unnamed Conversation",
      type: "conversation",
      meta: {
        source: "ChatGPT",
        date: new Date(messages[0].create_time).toISOString().split('T')[0],
        messageCount: messages.length
      }
    };
    
    try {
      // Create the conversation node
      const convResponse = await axios.post(`${MNEMOS_API}/node`, conversationNode);
      const conversationId = convResponse.data.id;
      
      // Process each message to extract entities
      let messageCounter = 0;
      for (const msg of messages) {
        // Only process user messages for entity extraction
        if (msg.message.author.role === "user") {
          messageCounter++;
          setProgress(prev => ({ ...prev, current: messageCounter }));
          
          // Use GPT to extract entities from the message
          const content = msg.message.content.parts.join("\n");
          
          // Skip very short messages
          if (content.length < 10) continue;
          
          try {
            const gptResponse = await axios.post(
              "https://api.openai.com/v1/chat/completions",
              {
                model: "gpt-4",
                messages: [
                  {
                    role: "system",
                    content: `
You are an entity extraction assistant.
Given a message from a conversation, identify key concepts, projects, tasks, or ideas.
For each entity, output a JSON object with:
1. label: The name of the entity
2. type: The type (project, task, concept, idea, person, technology, etc.)
3. meta: Any additional details as key-value pairs

Return your response as a JSON array of these objects.
If no entities are found, return an empty array.
Example output:
[
  {"label": "Project X", "type": "project", "meta": {"description": "A machine learning initiative"}},
  {"label": "Research paper review", "type": "task", "meta": {"deadline": "next week"}}
]
                    `,
                  },
                  {
                    role: "user",
                    content,
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
            
            // Parse the extracted entities
            const extractedContent = gptResponse.data.choices[0].message.content;
            let entities = [];
            try {
              entities = JSON.parse(extractedContent.trim());
            } catch (jsonErr) {
              console.error("Failed to parse GPT entity extraction:", extractedContent);
              continue;
            }
            
            // Create nodes for each entity and link to conversation
            for (const entity of entities) {
              try {
                // Create entity node
                const nodeResponse = await axios.post(`${MNEMOS_API}/node`, {
                  label: entity.label,
                  type: entity.type,
                  meta: entity.meta || {},
                });
                
                // Link entity to conversation
                await axios.post(`${MNEMOS_API}/link`, {
                  source: conversationId,
                  target: nodeResponse.data.id,
                  relation: "contains_entity",
                });
              } catch (entityErr) {
                console.error("Error creating entity:", entityErr);
              }
            }
          } catch (gptErr) {
            console.error("Error in GPT entity extraction:", gptErr);
          }
        }
      }
      
      return conversationId;
    } catch (err) {
      console.error("Error processing conversation:", err);
      return null;
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    
    if (!file) {
      alert("Please select a ChatGPT export file");
      return;
    }
    
    setIsProcessing(true);
    setImportStatus({ status: "starting", message: "Reading file..." });
    
    try {
      // Read the JSON file
      const fileReader = new FileReader();
      
      fileReader.onload = async (event) => {
        try {
          const content = JSON.parse(event.target.result);
          
          if (!content || !content.conversations || !Array.isArray(content.conversations)) {
            throw new Error("Invalid ChatGPT export format");
          }
          
          // Update total conversation count
          setProgress({ current: 0, total: content.conversations.length });
          setImportStatus({ 
            status: "processing", 
            message: `Processing ${content.conversations.length} conversations...` 
          });
          
          // Process each conversation
          const results = [];
          for (let i = 0; i < content.conversations.length; i++) {
            setProgress(prev => ({ ...prev, current: i }));
            
            // Process conversation one by one
            const conversationId = await processConversation(content.conversations[i]);
            if (conversationId) {
              results.push(conversationId);
            }
          }
          
          setImportStatus({ 
            status: "complete", 
            message: `Import complete. Processed ${results.length} conversations.` 
          });
          
          // Optional: refresh the graph
          window.location.reload();
          
        } catch (parseErr) {
          setImportStatus({ 
            status: "error", 
            message: `Error parsing file: ${parseErr.message}` 
          });
          console.error("Error parsing JSON:", parseErr);
        }
      };
      
      fileReader.onerror = () => {
        setImportStatus({ 
          status: "error", 
          message: "Failed to read file" 
        });
      };
      
      fileReader.readAsText(file);
      
    } catch (err) {
      setImportStatus({ 
        status: "error", 
        message: `Import failed: ${err.message}` 
      });
      console.error("Import error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="form-box">
      <div className="form-header">
        <h3>📥 Import ChatGPT History</h3>
      </div>
      
      <form onSubmit={handleImport}>
        <div className="import-instructions">
          <p>Upload your ChatGPT data export file to extract conversations and entities:</p>
          <ol>
            <li>Request your data from OpenAI (Account Settings → Data Controls → Export)</li>
            <li>Download and extract the ZIP file</li>
            <li>Upload the <code>conversations.json</code> file</li>
          </ol>
        </div>
        
        <div className="file-input-container">
          <input
            type="file"
            id="chatgpt-file"
            accept=".json"
            onChange={handleFileChange}
            disabled={isProcessing}
            className="form-input"
          />
          <label htmlFor="chatgpt-file" className="file-input-label">
            {file ? file.name : "Select conversations.json file"}
          </label>
        </div>
        
        {isProcessing && progress.total > 0 && (
          <div className="progress-container">
            <div className="progress-label">
              Processing conversation {progress.current} of {progress.total}
            </div>
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
          </div>
        )}
        
        {importStatus && (
          <div className={`import-status import-status-${importStatus.status}`}>
            {importStatus.message}
          </div>
        )}
        
        <button 
          type="submit" 
          className="submit-btn" 
          disabled={!file || isProcessing}
        >
          {isProcessing ? "Importing..." : "Import Conversations"}
        </button>
      </form>
    </div>
  );
}
