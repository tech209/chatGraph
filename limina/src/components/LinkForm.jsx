// spellbook/limina/src/components/LinkForm.jsx
import React, { useEffect, useState } from "react";
import { createLink, fetchGraph } from "../api/mnemos";

export default function LinkForm() {
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [relation, setRelation] = useState("");
  const [nodeLabels, setNodeLabels] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchGraph();
        const labels = data.nodes.map((n) => n.id);
        setNodeLabels(labels);
      } catch (err) {
        console.error("Failed to load nodes", err);
      }
    };
    load();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createLink({ source, target, relation });
      alert("Link created");
      setSource("");
      setTarget("");
      setRelation("");
    } catch (err) {
      alert("Failed to create link: " + err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-box">
      <h3>Create Link</h3>
      <select value={source} onChange={(e) => setSource(e.target.value)} required>
        <option value="">Select Source</option>
        {nodeLabels.map((label) => (
          <option key={label} value={label}>{label}</option>
        ))}
      </select>

      <select value={target} onChange={(e) => setTarget(e.target.value)} required>
        <option value="">Select Target</option>
        {nodeLabels.map((label) => (
          <option key={label} value={label}>{label}</option>
        ))}
      </select>

      <input
        type="text"
        value={relation}
        onChange={(e) => setRelation(e.target.value)}
        placeholder="Relation type (e.g., related_to)"
        required
      />
      <button type="submit">🔗 Add Link</button>
    </form>
  );
}
