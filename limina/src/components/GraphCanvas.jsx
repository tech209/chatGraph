import React, { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
} from "reactflow";
import "reactflow/dist/style.css";
import { fetchGraph } from "../api/mnemos";

export default function GraphCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  const loadGraph = useCallback(async () => {
    try {
      const data = await fetchGraph();
      console.log("📡 Loaded graph:", data);

      const formattedNodes = data.nodes.map((n) => ({
        id: n.id,
        data: {
          label: [
            `🧠 ${n.label || n.id || "Unnamed"}`,
            n.type ? `📦 Type: ${n.type}` : null,
            n.meta?.notes ? `📝 ${n.meta.notes}` : null,
          ]
            .filter(Boolean)
            .join("\n"),
        },
        position: {
          x: Math.random() * 400,
          y: Math.random() * 400,
        },
        style: {
          borderRadius: "8px",
          padding: "8px",
          background: "#1e1e25",
          color: "#f0f0f0",
          fontSize: "12px",
          fontFamily: "monospace",
          whiteSpace: "pre-line",
        },
      }));

      const formattedEdges = data.edges.map((e) => ({
        id: `${e.from}->${e.to}`,
        source: e.from,
        target: e.to,
        label: e.relation,
        type: "default",
        animated: true,
      }));

      setNodes(formattedNodes);
      setEdges(formattedEdges);
    } catch (err) {
      console.error("❌ Failed to load graph:", err);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  return (
    <div style={{ width: "100%", height: "100vh" }}>
      {loading ? (
        <p style={{ color: "white", padding: "1rem" }}>⏳ Loading graph...</p>
      ) : nodes.length === 0 ? (
        <p style={{ color: "white", padding: "1rem" }}>🕳 No nodes to display.</p>
      ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Background />
          <MiniMap />
          <Controls />
        </ReactFlow>
      )}
    </div>
  );
}
