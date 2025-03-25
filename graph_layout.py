import networkx as nx
from collections import deque

def assign_node_groups(graph: nx.DiGraph):
    """Tag each node with its 'group' based on type"""
    for node_id in graph.nodes:
        node_type = graph.nodes[node_id].get("type", "unknown")
        graph.nodes[node_id]["group"] = node_type
    return graph

def assign_depth_from_seed(graph: nx.DiGraph, seed: str, max_depth: int = 3):
    """Tag each node with its distance (depth) from a given node"""
    if seed not in graph.nodes:
        return graph

    # Reset existing depths
    nx.set_node_attributes(graph, -1, "depth")
    graph.nodes[seed]["depth"] = 0

    visited = set()
    queue = deque([(seed, 0)])

    while queue:
        current, depth = queue.popleft()
        if current in visited or depth >= max_depth:
            continue
        visited.add(current)

        for neighbor in graph.successors(current):
            if graph.nodes[neighbor].get("depth", -1) == -1:
                graph.nodes[neighbor]["depth"] = depth + 1
                queue.append((neighbor, depth + 1))

        for neighbor in graph.predecessors(current):
            if graph.nodes[neighbor].get("depth", -1) == -1:
                graph.nodes[neighbor]["depth"] = depth + 1
                queue.append((neighbor, depth + 1))

    return graph

def get_layout_view(graph: nx.DiGraph, seed: str = None, max_depth: int = 3):
    """Return nodes/edges with layout metadata (group, depth)"""
    graph = assign_node_groups(graph)

    if seed:
        graph = assign_depth_from_seed(graph, seed, max_depth)

    nodes = []
    for node_id in graph.nodes:
        data = graph.nodes[node_id].copy()
        data["id"] = node_id
        nodes.append(data)

    edges = [{"from": u, "to": v, **graph.edges[u, v]} for u, v in graph.edges]

    return {
        "nodes": nodes,
        "edges": edges
    }
