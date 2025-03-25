from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import networkx as nx
import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from meta_sorter import sort_for_commit

from storage import save_graph, load_graph

# Load environment
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)

# Init app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory graph
G = nx.DiGraph()

# ------------------
# Models
# ------------------
class NodeCreate(BaseModel):
    label: str
    type: str
    meta: dict = {}

class LinkCreate(BaseModel):
    source: str
    target: str
    relation: str

class ChatGPTMessage(BaseModel):
    content: str

class ConversationImport(BaseModel):
    conversations: List[Dict[str, Any]]

class ImportStatus(BaseModel):
    total: int = 0
    processed: int = 0
    created_nodes: int = 0
    created_links: int = 0
    errors: int = 0
    complete: bool = False

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5

import_status = ImportStatus()

# ------------------
# Core Routes
# ------------------
@app.post("/node")
def create_node(data: NodeCreate):
    if data.label in G.nodes:
        raise HTTPException(status_code=400, detail="Node already exists")
    G.add_node(data.label, type=data.type, meta=data.meta)
    return {"message": "Node created", "id": data.label}

@app.post("/link")
def create_link(data: LinkCreate):
    if not G.has_node(data.source) or not G.has_node(data.target):
        raise HTTPException(status_code=404, detail="Missing node(s)" )
    G.add_edge(data.source, data.target, relation=data.relation)
    return {"message": "Link created", "from": data.source, "to": data.target}

@app.get("/graph")
def get_graph():
    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    edges = [{"from": u, "to": v, **G.edges[u, v]} for u, v in G.edges]
    return {"nodes": nodes, "edges": edges}

@app.post("/save")
def save():
    return save_graph(G)

@app.get("/load")
def load():
    global G
    G = load_graph()
    return {"message": "Graph loaded"}

@app.post("verify-then-save")
def verify_then_save():
    sort_for_commit(G)
    save_graph(G)
    return {"message": "Graph sorted and saved."}

# ------------------
# Entity Extraction
# ------------------
@app.post("/api/process-chatgpt-message")
async def process_chatgpt_message(data: ChatGPTMessage):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": entity_prompt()},
                {"role": "user", "content": data.content}
            ]
        )
        raw = response.choices[0].message.content
        try:
            entities = json.loads(raw.strip())
            return {"entities": entities}
        except json.JSONDecodeError:
            return {"error": "JSON parse failed", "raw": raw}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/batch-process-chatgpt")
async def batch_process_chatgpt(data: ConversationImport):
    global import_status
    import_status = ImportStatus(total=len(data.conversations))
    asyncio.create_task(process_conversations(data.conversations))
    return {"message": "Started", "total": len(data.conversations)}

@app.get("/api/chatgpt-import-status")
async def get_import_status():
    return import_status

# ------------------
# Query & GPT Answer
# ------------------
@app.post("/api/query")
async def query_knowledge_graph(data: QueryRequest):
    try:
        nodes = search_graph(data.query, data.max_results)
        context = format_knowledge_for_gpt(nodes)
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"""You are Orin, a memory assistant. Use this graph context:

{context}

Answer the user’s question below using the knowledge above. If uncertain, say so."""},
                {"role": "user", "content": data.query}
            ]
        )
        answer = response.choices[0].message.content
        return {
            "answer": answer,
            "sources": [{"id": n["id"], "label": n["label"], "type": n["type"]} for n in nodes]
        }
    except Exception as e:
        return {"error": str(e)}

# ------------------
# Internals
# ------------------
def entity_prompt():
    return """
You are an entity extraction assistant. Given a message, identify projects, tasks, concepts, or technologies. 
Respond with an array of objects like:
[
  {"label": "Project X", "type": "project", "meta": {"desc": "machine learning pipeline"}},
  {"label": "Setup GitHub CI", "type": "task", "meta": {"priority": "high"}}
]
If no entities are found, return an empty array.
"""

async def process_conversations(conversations):
    global import_status
    for convo in conversations:
        try:
            title = convo.get("title", "Unnamed Conversation")
            mapping = convo.get("mapping", {})
            messages = [
                m for k, m in mapping.items()
                if m.get("message", {}).get("content", {}).get("parts")
            ]
            messages.sort(key=lambda x: x.get("create_time", ""))
            if not messages:
                import_status.processed += 1
                continue

            date = messages[0].get("create_time", "").split("T")[0] if messages else ""

            try:
                create_node(NodeCreate(
                    label=title,
                    type="conversation",
                    meta={"source": "ChatGPT", "date": date, "messageCount": len(messages)}
                ))
                import_status.created_nodes += 1
            except HTTPException:
                pass

            for msg in messages:
                if msg["message"]["author"]["role"] != "user":
                    continue
                content = "\n".join(msg["message"]["content"]["parts"])
                if len(content) < 10:
                    continue

                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": entity_prompt()},
                            {"role": "user", "content": content}
                        ]
                    )
                    raw = response.choices[0].message.content
                    try:
                        entities = json.loads(raw.strip())
                        for e in entities:
                            try:
                                create_node(NodeCreate(
                                    label=e.get("label", "Unnamed"),
                                    type=e.get("type", "concept"),
                                    meta=e.get("meta", {})
                                ))
                                import_status.created_nodes += 1
                            except HTTPException:
                                pass
                            try:
                                create_link(LinkCreate(
                                    source=title,
                                    target=e.get("label", "Unnamed"),
                                    relation="contains_entity"
                                ))
                                import_status.created_links += 1
                            except:
                                import_status.errors += 1
                    except:
                        import_status.errors += 1
                except:
                    import_status.errors += 1

            import_status.processed += 1
        except:
            import_status.errors += 1
            import_status.processed += 1
    import_status.complete = True
    save()

def search_graph(query, max_results=5):
    terms = query.lower().split()
    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    scored = []
    for node in nodes:
        blob = f"{node['label']} {node['type']} " + " ".join(
            f"{k} {v}" for k, v in node.get("meta", {}).items()
        )
        score = sum(1 for t in terms if t in blob.lower())
        scored.append((node, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [n for n, s in scored[:max_results] if s > 0]

def format_knowledge_for_gpt(nodes):
    if not nodes:
        return "No relevant nodes found."
    lines = []
    for n in nodes:
        lines.append(f"Node: {n['label']} ({n['type']})")
        if n.get("meta"):
            lines.extend([f"- {k}: {v}" for k, v in n["meta"].items()])
    return "\n".join(lines)

# ------------------
# Launch
# ------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
