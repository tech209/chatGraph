# spellbook/orin/orinctl.py

import argparse
from orin_client import remember, link, recall, save, load

parser = argparse.ArgumentParser(description="🧠 Orin Memory CLI")
subparsers = parser.add_subparsers(dest="command")

# Add node
node_parser = subparsers.add_parser("add-node", help="Create a new memory node")
node_parser.add_argument("label", help="Node label")
node_parser.add_argument("type", help="Node type (project, task, idea...)")
node_parser.add_argument("--meta", help="Metadata JSON string", default="{}")

# Add link
link_parser = subparsers.add_parser("add-link", help="Link two nodes")
link_parser.add_argument("source", help="Source node label")
link_parser.add_argument("target", help="Target node label")
link_parser.add_argument("relation", help="Type of relation (e.g., related_to)")

# View graph
subparsers.add_parser("view", help="View full graph JSON")
subparsers.add_parser("save", help="Save graph to file")
subparsers.add_parser("load", help="Load graph from file")

args = parser.parse_args()

if args.command == "add-node":
    import json
    try:
        meta_obj = json.loads(args.meta)
        result = remember(args.label, args.type, meta_obj)
        print("✅ Node created:", result)
    except Exception as e:
        print("❌ Failed to add node:", e)

elif args.command == "add-link":
    try:
        result = link(args.source, args.target, args.relation)
        print("🔗 Link created:", result)
    except Exception as e:
        print("❌ Failed to add link:", e)

elif args.command == "view":
    graph = recall()
    print("📡 Memory Graph:")
    print(graph)

elif args.command == "save":
    print(save())

elif args.command == "load":
    print(load())

else:
    parser.print_help()
    