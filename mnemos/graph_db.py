import networkx as nx

G = nx.DiGraph()

def add_node(label, node_type, meta=None):
    if G.has_node(label):
        return False
    G.add_node(label, type=node_type, meta=meta or {})
    return True

def add_edge(source, target, relation):
    G.add_edge(source, target, relation=relation)

def get_all_nodes():
    return [{"id": n, **G.nodes[n]} for n in G.nodes]

def get_all_edges():
    return [{"from": u, "to": v, **G.edges[u, v]} for u, v in G.edges]

def get_graph():
    return {
        "nodes": get_all_nodes(),
        "edges": get_all_edges()
    }

def graph():
    return G
