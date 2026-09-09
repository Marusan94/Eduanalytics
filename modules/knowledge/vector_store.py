import json
import os
import numpy as np

LIBRARY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "library.jsonl")
EMBED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge", "embeddings.npy")
META_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge", "meta.jsonl")

def _ensure_dir(p):
    d=os.path.dirname(p)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def add_document(doc: dict):
    # doc debe tener id, title, text
    text = doc.get("text") or f"{doc.get('title','')} {doc.get('finding','')}"
    try:
        from modules.knowledge.embedding_provider import get_provider
        provider = get_provider()
        if not provider.is_available():
            return
        emb = provider.embed([text])[0]
        _ensure_dir(EMBED_PATH)
        _ensure_dir(META_PATH)
        # append embedding
        if os.path.exists(EMBED_PATH):
            arr = np.load(EMBED_PATH)
            arr = np.vstack([arr, np.array(emb)])
        else:
            arr = np.array([emb])
        np.save(EMBED_PATH, arr)
        with open(META_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": doc.get("id"), "title": doc.get("title")}, ensure_ascii=False)+"\n")
    except Exception:
        pass

def search(query: str, k=5):
    # si hay embeddings, usar cosine, sino fallback textual
    if os.path.exists(EMBED_PATH) and os.path.exists(META_PATH):
        try:
            from modules.knowledge.embedding_provider import get_provider
            provider = get_provider()
            q_emb = provider.embed([query])[0]
            arr = np.load(EMBED_PATH)
            # cosine
            import numpy as np2
            q = np.array(q_emb)
            # normalize q (provider already normalized)
            dots = arr @ q
            idx = np.argsort(-dots)[:k]
            # load meta
            metas = []
            with open(META_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        metas.append(json.loads(line))
                    except Exception:
                        continue
            results = []
            # load library docs for text
            lib_docs = []
            if os.path.exists(LIBRARY_PATH):
                with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            lib_docs.append(json.loads(line))
                        except Exception:
                            continue
            id_to_doc = {d.get("id"): d for d in lib_docs}
            for i in idx:
                if i < len(metas):
                    mid = metas[i].get("id")
                    doc = id_to_doc.get(mid, metas[i])
                    doc = dict(doc)
                    doc["score"] = float(dots[i])
                    # fragment
                    txt = doc.get("text") or doc.get("finding") or doc.get("title","")
                    doc["fragment"] = txt[:200]
                    results.append(doc)
            return results
        except Exception:
            pass
    # fallback textual
    if not os.path.exists(LIBRARY_PATH):
        return []
    out=[]
    qlow=query.lower()
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d=json.loads(line)
                txt=(d.get("text") or d.get("title","")).lower()
                if qlow in txt or any(w in txt for w in qlow.split()):
                    d["score"]=0.5
                    d["fragment"]=(d.get("text") or d.get("title",""))[:200]
                    out.append(d)
                    if len(out)>=k:
                        break
            except Exception:
                continue
    return out

def list_library(category="Todos"):
    if not os.path.exists(LIBRARY_PATH):
        return []
    out=[]
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d=json.loads(line)
                if category=="Todos" or d.get("category")==category or d.get("category","Otros")==category:
                    out.append(d)
            except Exception:
                continue
    return out
