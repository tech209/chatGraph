def prune_disconnected_nodes(graph):
    to_remove = [n for n in graph.nodes if graph.degree(n) == 0]
    graph.remove_nodes_from(to_remove)

def remove_empty_nodes(graph):
    to_remove = []
    for node in graph.nodes:
        meta = graph.nodes[node].get("meta", {})
        if not meta or all(v in ["", None] for v in meta.values()):
            to_remove.append(node)
    graph.remove_nodes_from(to_remove)

def deduplicate_nodes(graph):
    seen = {}
    to_remove = []
    for node in list(graph.nodes):
        label = graph.nodes[node].get("label", node).lower()
        if label in seen:
            to_remove.append(node)
        else:
            seen[label] = node
    graph.remove_nodes_from(to_remove)

def sort_for_commit(graph):
    prune_disconnected_nodes(graph)
    remove_empty_nodes(graph)
    deduplicate_nodes(graph)
    return graph
