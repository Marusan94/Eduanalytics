import json
import os
import uuid
from datetime import datetime

DISCOVERIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "discoveries.jsonl")
LIBRARY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "library.jsonl")

def _ensure_dir(path):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def save_discovery(title: str, finding: str, variables: list, source_csv: str = "", context: dict = None) -> str:
    _ensure_dir(DISCOVERIES_PATH)
    _ensure_dir(LIBRARY_PATH)
    did = f"disc-{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    doc = {
        "id": did,
        "title": title,
        "finding": finding,
        "variables": variables,
        "source_csv": source_csv,
        "date": now,
        "context": context or {},
        "type": "discovery",
        "category": "Descubrimientos",
        "text": f"{title}. {finding} Variables: {', '.join(variables)}"
    }
    # discoveries
    with open(DISCOVERIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    # library (heterogénea)
    lib_doc = {**doc, "topic": title}
    with open(LIBRARY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(lib_doc, ensure_ascii=False) + "\n")
    # actualizar embeddings si hay provider
    try:
        from modules.knowledge.vector_store import add_document
        add_document(lib_doc)
    except Exception:
        pass
    return did

def load_discoveries() -> list:
    if not os.path.exists(DISCOVERIES_PATH):
        return []
    out = []
    with open(DISCOVERIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out
