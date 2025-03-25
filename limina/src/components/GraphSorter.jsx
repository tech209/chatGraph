// spellbook/limina/src/components/GraphSorter.jsx
import React, { useMemo } from "react";

/**
 * GraphSorter takes a raw graph (nodes + edges) and returns a filtered and grouped version.
 * - You can filter by group (type)
 * - You can highlight by depth (if available)
 */
export default function GraphSorter({ nodes, edges, activeGroup = null, maxDepth = null }) {
  const sorted = useMemo(() => {
    let filteredNodes = nodes;

    if (activeGroup) {
      filteredNodes = filteredNodes.filter((node) => node.group === activeGroup);
    }

    if (maxDepth !== null) {
      filteredNodes = filteredNodes.filter((node) =>
        node.depth === undefined ? true : node.depth <= maxDepth
      );
    }

    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = edges.filter(
      (edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to)
    );

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [nodes, edges, activeGroup, maxDepth]);

  return sorted;
}
