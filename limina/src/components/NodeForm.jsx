// spellbook/limina/src/components/NodeForm.jsx
import React, { useEffect, useState } from "react";
import { createNode, fetchGraph } from "../api/mnemos";
// No need for additional CSS import as we're using the existing index.css styles

export default function NodeForm() {
  const [label, setLabel] = useState("");
  const [type, setType] = useState("");
  const [metaFields, setMetaFields] = useState([{ key: "", value: "" }]);
  const [typeOptions, setTypeOptions] = useState([]);
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [rawMetaJSON, setRawMetaJSON] = useState("{}");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchGraph();
        const types = Array.from(new Set(data.nodes.map((n) => n.type)));
        setTypeOptions(types);
      } catch (err) {
        console.error("Failed to load types", err);
      }
    };
    load();
  }, []);

  // Convert meta fields to JSON object
  const getMetaObject = () => {
    if (isAdvancedMode) {
      try {
        return JSON.parse(rawMetaJSON);
      } catch (err) {
        throw new Error("Invalid JSON in advanced mode");
      }
    } else {
      const metaObj = {};
      metaFields.forEach(field => {
        if (field.key.trim() !== "") {
          try {
            // Try to parse the value as JSON if it looks like a JSON structure
            if (field.value.trim().startsWith('{') || 
                field.value.trim().startsWith('[') || 
                field.value.trim() === "true" || 
                field.value.trim() === "false" ||
                !isNaN(field.value.trim())) {
              metaObj[field.key] = JSON.parse(field.value);
            } else {
              metaObj[field.key] = field.value;
            }
          } catch (err) {
            // If parsing fails, store as string
            metaObj[field.key] = field.value;
          }
        }
      });
      return metaObj;
    }
  };

  // Update raw JSON when fields change (for sync between modes)
  useEffect(() => {
    if (!isAdvancedMode) {
      try {
        const metaObj = {};
        metaFields.forEach(field => {
          if (field.key.trim() !== "") {
            metaObj[field.key] = field.value;
          }
        });
        setRawMetaJSON(JSON.stringify(metaObj, null, 2));
      } catch (err) {
        // Ignore errors during conversion
      }
    }
  }, [metaFields, isAdvancedMode]);

  // Update fields when switching from advanced mode
  useEffect(() => {
    if (!isAdvancedMode && rawMetaJSON !== "{}") {
      try {
        const metaObj = JSON.parse(rawMetaJSON);
        const newFields = Object.entries(metaObj).map(([key, value]) => ({
          key,
          value: typeof value === 'object' ? JSON.stringify(value) : String(value)
        }));
        
        if (newFields.length > 0) {
          setMetaFields(newFields);
        }
      } catch (err) {
        // If parsing fails, keep current fields
      }
    }
  }, [isAdvancedMode, rawMetaJSON]);

  const handleAddField = () => {
    setMetaFields([...metaFields, { key: "", value: "" }]);
  };

  const handleRemoveField = (index) => {
    const newFields = [...metaFields];
    newFields.splice(index, 1);
    setMetaFields(newFields);
  };

  const handleFieldChange = (index, field, value) => {
    const newFields = [...metaFields];
    newFields[index][field] = value;
    setMetaFields(newFields);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const metaObj = getMetaObject();
      await createNode({ label, type, meta: metaObj });
      alert("Node created");
      setLabel("");
      setType("");
      
      if (isAdvancedMode) {
        setRawMetaJSON("{}");
      } else {
        setMetaFields([{ key: "", value: "" }]);
      }
    } catch (err) {
      alert("Failed to create node: " + err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-box">
      <h3>Create Node</h3>
      
      <div className="form-row">
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Label"
          required
          className="form-input"
        />
      </div>
      
      <div className="form-row">
        <input
          list="node-types"
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="Type (project, task...)"
          required
          className="form-input"
        />
        <datalist id="node-types">
          {typeOptions.map((t) => (
            <option key={t} value={t} />
          ))}
        </datalist>
      </div>
      
      <div className="form-section">
        <div className="form-header">
          <h4>Metadata</h4>
          <button
            type="button"
            onClick={() => setIsAdvancedMode(!isAdvancedMode)}
            className="toggle-button"
          >
            {isAdvancedMode ? "Simple Mode" : "Advanced Mode"}
          </button>
        </div>
        
        {isAdvancedMode ? (
          <textarea
            value={rawMetaJSON}
            onChange={(e) => setRawMetaJSON(e.target.value)}
            placeholder="Metadata JSON"
            rows="6"
            className="json-textarea"
          />
        ) : (
          <div className="meta-fields">
            {metaFields.map((field, index) => (
              <div key={index} className="meta-field-row">
                <input
                  type="text"
                  placeholder="Key"
                  value={field.key}
                  onChange={(e) => handleFieldChange(index, "key", e.target.value)}
                  className="meta-key"
                />
                <input
                  type="text"
                  placeholder="Value"
                  value={field.value}
                  onChange={(e) => handleFieldChange(index, "value", e.target.value)}
                  className="meta-value"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveField(index)}
                  className="remove-field-btn"
                >
                  −
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={handleAddField}
              className="add-field-btn"
            >
              + Add Field
            </button>
          </div>
        )}
      </div>
      
      <button type="submit" className="submit-btn">➕ Add Node</button>
    </form>
  );
}
