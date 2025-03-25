# spellbook/orin/orin_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("MNEMOS_API", "http://localhost:8000")

def remember(label, type_, meta=None):
    meta = meta or {}
    data = {"label": label, "type": type_, "meta": meta}
    res = requests.post(f"{BASE}/node", json=data)
    return res.json()

def link(source, target, relation):
    data = {"source": source, "target": target, "relation": relation}
    res = requests.post(f"{BASE}/link", json=data)
    return res.json()

def recall():
    res = requests.get(f"{BASE}/graph")
    return res.json()

def save():
    return requests.post(f"{BASE}/save").json()

def load():
    return requests.get(f"{BASE}/load").json()
