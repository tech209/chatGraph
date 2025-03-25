import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=api_key)

def get_embedding(text: str) -> list:
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536

def cosine_similarity(vec1: list, vec2: list) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    if magnitude1 * magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

def fallback_keyword_search(query: str, nodes: list, max_results=5) -> list:
    terms = query.lower().split()
    scored = []
    for node in nodes:
        text = f"{node['label'].lower()} {node['type'].lower()}"
        if node.get("meta"):
            text += " " + " ".join(f"{k} {str(v)}".lower() for k, v in node["meta"].items())
        score = sum(1 for term in terms if term in text)
        scored.append((node, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [n for n, s in scored[:max_results] if s > 0]

def search_graph(query: str, graph, max_results=5) -> list:
    all_nodes = [{"id": n, **graph.nodes[n]} for n in graph.nodes]
    if not all_nodes:
        return []
    try:
        query_embedding = get_embedding(query)
        scored = []
        for node in all_nodes:
            text = f"{node['label']} ({node['type']})"
            if node.get("meta"):
                meta_str = "; ".join(f"{k}: {v}" for k, v in node["meta"].items())
                text += f" | {meta_str}"
            node_embedding = get_embedding(text)
            similarity = cosine_similarity(query_embedding, node_embedding)
            scored.append((node, similarity))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in scored[:max_results]]
    except Exception as e:
        print(f"Semantic search error: {e}")
        return fallback_keyword_search(query, all_nodes, max_results)

def format_knowledge_for_gpt(nodes: list, graph) -> str:
    if not nodes:
        return "No relevant information found in your memory."
    parts = []
    for node in nodes:
        entry = f"Node: {node['label']} (Type: {node['type']})\n"
        if node.get("meta"):
            entry += "Metadata:\n" + "\n".join(f"- {k}: {v}" for k, v in node["meta"].items()) + "\n"
        connections = []
        for u, v, data in graph.out_edges(node['id'], data=True):
            t_node = graph.nodes[v]
            connections.append(f"- Related to {v} ({t_node.get('type', 'unknown')}) via {data.get('relation', 'link')}")
        for u, v, data in graph.in_edges(node['id'], data=True):
            s_node = graph.nodes[u]
            connections.append(f"- {u} ({s_node.get('type', 'unknown')}) is related via {data.get('relation', 'link')}")
        if connections:
            entry += "Connections:\n" + "\n".join(connections) + "\n"
        parts.append(entry)
    return "\n\n".join(parts)
