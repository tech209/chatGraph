# spellbook/mnemos/storage.py

import os
import json
import networkx as nx

SAVE_PATH = "../db/orin_memory.json"

def save_graph(graph, path=SAVE_PATH):
    """Save a NetworkX graph to a JSON file."""
    data = nx.node_link_data(graph)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return {"message": f"Graph saved to {path}"}

def load_graph(path=SAVE_PATH):
    """Load a graph from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved graph at {path}")
    with open(path, "r") as f:
        data = json.load(f)
    return nx.node_link_graph(data)
