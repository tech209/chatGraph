# spellbook/orin/orin_proxy.py
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from orin_client import remember, link

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("GPT_MODEL", "gpt-4")

print("🔮 Orin Proxy active. Type a memory, link, or idea. Type 'exit' to quit.")

while True:
    try:
        user_input = input("🗣️ > ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("🧠 Orin session closed.")
            break

        messages = [
            {"role": "system", "content": "You are Orin, a memory archivist. When a user gives you input, extract the intent as either 'remember' or 'link'. Respond ONLY with a JSON object like: {'intent': 'remember', 'label': '...', 'type': '...', 'meta': {...}} or {'intent': 'link', 'source': '...', 'target': '...', 'relation': '...'}. Do not add any commentary."},
            {"role": "user", "content": user_input}
        ]

        res = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        content = res.choices[0].message.content
        print("🧾 GPT →", content)
        parsed = json.loads(content.replace("'", '"'))

        if parsed["intent"] == "remember":
            result = remember(parsed["label"], parsed["type"], parsed.get("meta", {}))
            print("✅ Memory saved:", result)
        elif parsed["intent"] == "link":
            result = link(parsed["source"], parsed["target"], parsed["relation"])
            print("🔗 Link saved:", result)
        else:
            print("⚠️ Unknown intent type.")

    except KeyboardInterrupt:
        print("\n🧠 Orin session closed.")
        break
    except Exception as e:
        print("❌ Error:", e)
