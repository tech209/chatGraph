from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
from storage import save_graph, load_graph
import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the graph
G = nx.DiGraph()

# OpenAI client initialized after loading environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables!")
    
openai_client = OpenAI(api_key=api_key)

# ---------------------
# Models
# ---------------------
class NodeCreate(BaseModel):
    label: str
    type: str
    meta: dict = {}

class LinkCreate(BaseModel):
    source: str
    target: str
    relation: str

# Add these models for the ChatGPT import feature
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

# Add this model for the query system
class QueryRequest(BaseModel):
    query: str
    max_results: int = 5

# Add a global variable to track import status
# In a production app, you'd use Redis or a database
import_status = ImportStatus()

# ---------------------
# Graph Operations
# ---------------------
@app.post("/node")
def create_node(data: NodeCreate):
    if data.label in G.nodes:
        raise HTTPException(status_code=400, detail="Node already exists")
    G.add_node(data.label, type=data.type, meta=data.meta)
    return {"message": "Node created", "id": data.label, "node": data.label}

@app.post("/link")
def create_link(data: LinkCreate):
    if not G.has_node(data.source) or not G.has_node(data.target):
        raise HTTPException(status_code=404, detail="One or both nodes not found")
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

# ---------------------
# ChatGPT Import Functions
# ---------------------
@app.post("/api/process-chatgpt-message")
async def process_chatgpt_message(data: ChatGPTMessage):
    """Process a single message from ChatGPT and extract entities"""
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Call OpenAI API to extract entities
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an entity extraction assistant.
Given a message from a conversation, identify key concepts, projects, tasks, or ideas.
For each entity, output a JSON object with:
1. label: The name of the entity
2. type: The type (project, task, concept, idea, person, technology, etc.)
3. meta: Any additional details as key-value pairs

Return your response as a JSON array of these objects.
If no entities are found, return an empty array.
Example output:
[
  {"label": "Project X", "type": "project", "meta": {"description": "A machine learning initiative"}},
  {"label": "Research paper review", "type": "task", "meta": {"deadline": "next week"}}
]
                    """
                },
                {
                    "role": "user",
                    "content": data.content
                }
            ]
        )
        
        extracted_content = response.choices[0].message.content
        
        try:
            entities = json.loads(extracted_content.strip())
            return {"entities": entities}
        except json.JSONDecodeError:
            return {"error": "Failed to parse GPT response", "raw_response": extracted_content}
            
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/batch-process-chatgpt")
async def batch_process_chatgpt(data: ConversationImport):
    """Process a batch of ChatGPT conversations"""
    global import_status
    
    # Reset import status
    import_status = ImportStatus(total=len(data.conversations))
    
    # Start processing in background task
    asyncio.create_task(process_conversations(data.conversations))
    
    return {"message": "Processing started", "total": len(data.conversations)}


@app.get("/api/chatgpt-import-status")
async def get_import_status():
    """Get the current status of the import process"""
    return import_status


async def process_conversations(conversations):
    """Process conversations in the background"""
    global import_status
    
    for conversation in conversations:
        try:
            # Extract title and conversation content
            title = conversation.get("title", "Unnamed Conversation")
            mapping = conversation.get("mapping", {})
            
            # Convert the mapping object to an array and sort by timestamp
            messages = []
            for key, msg in mapping.items():
                if (msg.get("message") and 
                    msg["message"].get("content") and 
                    msg["message"]["content"].get("parts")):
                    messages.append(msg)
            
            # Sort by timestamp
            messages.sort(key=lambda x: x.get("create_time", ""))
            
            # Skip empty conversations
            if not messages:
                import_status.processed += 1
                continue
            
            # Create conversation node
            date_str = ""
            if messages and messages[0].get("create_time"):
                date_parts = messages[0]["create_time"].split("T")
                if date_parts:
                    date_str = date_parts[0]
            
            # Create the conversation node
            try:
                conversation_node = NodeCreate(
                    label=title,
                    type="conversation",
                    meta={
                        "source": "ChatGPT",
                        "date": date_str,
                        "messageCount": len(messages)
                    }
                )
                result = create_node(conversation_node)
                conversation_label = title
                import_status.created_nodes += 1
            except HTTPException:
                # Node might already exist
                conversation_label = title
            
            # Process each message to extract entities
            for msg in messages:
                if (msg.get("message", {}).get("author", {}).get("role") == "user"):
                    # Get content
                    content_parts = msg.get("message", {}).get("content", {}).get("parts", [])
                    content = "\n".join(content_parts)
                    
                    # Skip very short messages
                    if len(content) < 10:
                        continue
                    
                    # Extract entities using OpenAI
                    try:
                        response = openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system",
                                    "content": """
You are an entity extraction assistant.
Given a message from a conversation, identify key concepts, projects, tasks, or ideas.
For each entity, output a JSON object with:
1. label: The name of the entity
2. type: The type (project, task, concept, idea, person, technology, etc.)
3. meta: Any additional details as key-value pairs

Return your response as a JSON array of these objects.
If no entities are found, return an empty array.
Example output:
[
  {"label": "Project X", "type": "project", "meta": {"description": "A machine learning initiative"}},
  {"label": "Research paper review", "type": "task", "meta": {"deadline": "next week"}}
]
                                    """
                                },
                                {
                                    "role": "user",
                                    "content": content
                                }
                            ]
                        )
                        
                        extracted_content = response.choices[0].message.content
                        
                        try:
                            entities = json.loads(extracted_content.strip())
                            
                            # Create nodes for each entity and link to conversation
                            for entity in entities:
                                try:
                                    # Create entity node
                                    entity_node = NodeCreate(
                                        label=entity.get("label", "Unnamed Entity"),
                                        type=entity.get("type", "concept"),
                                        meta=entity.get("meta", {})
                                    )
                                    
                                    try:
                                        create_node(entity_node)
                                        import_status.created_nodes += 1
                                    except HTTPException:
                                        # Node might already exist
                                        pass
                                    
                                    # Link entity to conversation
                                    link_data = LinkCreate(
                                        source=conversation_label,
                                        target=entity.get("label", "Unnamed Entity"),
                                        relation="contains_entity"
                                    )
                                    
                                    try:
                                        create_link(link_data)
                                        import_status.created_links += 1
                                    except HTTPException:
                                        # Link might already exist or nodes not found
                                        import_status.errors += 1
                                        
                                except Exception as entity_err:
                                    print(f"Error creating entity: {entity_err}")
                                    import_status.errors += 1
                        except json.JSONDecodeError:
                            print(f"Error parsing GPT response: {extracted_content}")
                            import_status.errors += 1
                            
                    except Exception as extraction_err:
                        print(f"Error in extraction: {extraction_err}")
                        import_status.errors += 1
            
            import_status.processed += 1
            
        except Exception as e:
            print(f"Error processing conversation: {e}")
            import_status.errors += 1
            import_status.processed += 1
    
    # Mark as complete
    import_status.complete = True
    
    # Save the graph
    save()

# ---------------------
# Chat Query System
# ---------------------
@app.post("/api/query")
async def query_knowledge_graph(query_data: QueryRequest):
    """
    Query the knowledge graph and return relevant information using GPT
    """
    try:
        # Step 1: Perform a search in the graph to find relevant nodes
        relevant_nodes = search_graph(query_data.query, max_results=query_data.max_results)
        
        # Step 2: Format the retrieved knowledge for GPT
        knowledge_context = format_knowledge_for_gpt(relevant_nodes)
        
        # Step 3: Generate a response with GPT using the retrieved knowledge
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Orin, a memory assistant. 
You have access to a knowledge graph that contains information the user has stored.
Answer the user's question based on the following retrieved information.
If the information is insufficient to answer, acknowledge what you know and what you don't.

RETRIEVED KNOWLEDGE:
{knowledge_context}

Respond conversationally and in first person as Orin. Reference specific pieces of knowledge
when they are directly relevant to the query."""
                },
                {
                    "role": "user",
                    "content": query_data.query
                }
            ]
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": [{"id": node["id"], "label": node["label"], "type": node["type"]} 
                       for node in relevant_nodes]
        }
        
    except Exception as e:
        print(f"Error querying knowledge graph: {e}")
        return {"error": str(e)}

# Helper function to search the graph for relevant nodes
def search_graph(query, max_results=5):
    """Find nodes in the graph relevant to the query"""
    # Get all nodes from the graph
    all_nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    
    if not all_nodes:
        return []
    
    try:
        # Use OpenAI embeddings to find semantically relevant nodes
        query_embedding = get_embedding(query)
        
        # Calculate scores for each node based on similarity to query
        scored_nodes = []
        for node in all_nodes:
            # Create a text representation of this node
            node_text = f"{node['label']} ({node['type']})"
            
            # Add metadata if available
            if 'meta' in node and node['meta']:
                # Flatten metadata to string
                meta_str = "; ".join([f"{k}: {v}" for k, v in node['meta'].items()])
                node_text += f" | {meta_str}"
            
            # Get embedding for node text
            node_embedding = get_embedding(node_text)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, node_embedding)
            
            scored_nodes.append((node, similarity))
        
        # Sort nodes by similarity score (descending)
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        # Return top nodes
        return [node for node, score in scored_nodes[:max_results]]
        
    except Exception as e:
        print(f"Error in semantic search: {e}")
        
        # Fallback to keyword matching if embedding fails
        query_terms = query.lower().split()
        scored_nodes = []
        
        for node in all_nodes:
            # Create a text representation of this node
            node_text = f"{node['label'].lower()} {node['type'].lower()}"
            
            # Add metadata if available
            if 'meta' in node and node['meta']:
                meta_str = " ".join([f"{k} {v}".lower() for k, v in node['meta'].items()])
                node_text += f" {meta_str}"
            
            # Simple keyword matching score
            score = sum(1 for term in query_terms if term in node_text)
            scored_nodes.append((node, score))
        
        # Sort nodes by score (descending)
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        # Return top nodes
        return [node for node, score in scored_nodes[:max_results] if score > 0]

# Get embeddings for semantic search
def get_embedding(text):
    try:
        response = openai_client.embeddings.create(
            input=text, 
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        # Return a dummy embedding in case of error
        return [0] * 1536  # Ada embeddings are 1536 dimensions

# Calculate cosine similarity between two vectors
def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 * magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)

# Format the retrieved knowledge for GPT
def format_knowledge_for_gpt(nodes):
    """Format the retrieved nodes into a context string for GPT"""
    if not nodes:
        return "No relevant information found in your memory."
    
    context_parts = []
    
    for node in nodes:
        context_part = f"Node: {node['label']} (Type: {node['type']})\n"
        
        # Add metadata if available
        if 'meta' in node and node['meta']:
            meta_str = "\n".join([f"- {k}: {v}" for k, v in node['meta'].items()])
            context_part += f"Metadata:\n{meta_str}\n"
        
        # Get connected nodes
        connected_nodes = []
        
        # Check outgoing connections
        for u, v, data in G.out_edges(node['id'], data=True):
            target_node = G.nodes[v]
            connected_nodes.append(f"- Related to {v} ({target_node.get('type', 'unknown')}) via {data.get('relation', 'link')}")
        
        # Check incoming connections
        for u, v, data in G.in_edges(node['id'], data=True):
            source_node = G.nodes[u]
            connected_nodes.append(f"- {u} ({source_node.get('type', 'unknown')}) is related via {data.get('relation', 'link')}")
        
        if connected_nodes:
            context_part += "Connections:\n" + "\n".join(connected_nodes) + "\n"
        
        context_parts.append(context_part)
    
    return "\n\n".join(context_parts)

# ---------------------
# Run the app
# ---------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    