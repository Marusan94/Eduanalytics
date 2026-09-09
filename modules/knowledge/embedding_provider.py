"""
EmbeddingProvider abstraction — prioridad local/gratuito, remoto solo si configurado.
"""

import os

class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
    def is_available(self) -> bool:
        return False

class LocalHashEmbedding(EmbeddingProvider):
    """Fallback local gratuito, determinista, NO semántico real. Hash bag-of-words → vector 64 dim normalizado. Útil para que la Biblioteca funcione sin API key/costo, pero no es RAG semántico verdadero (dos textos relacionados no necesariamente quedan cerca)."""
    def __init__(self, dim=64):
        self.dim = dim
    def is_available(self):
        return True
    def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        import math
        out = []
        for t in texts:
            v = [0.0]*self.dim
            for word in t.lower().split():
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                v[h % self.dim] += 1.0
            # normalize
            norm = math.sqrt(sum(x*x for x in v)) or 1.0
            v = [x/norm for x in v]
            out.append(v)
        return out

class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, model="text-embedding-3-small"):
        self.model = model
        self._client = None
    def is_available(self):
        try:
            from modules.common import get_client
            c = get_client()
            return c is not None
        except Exception:
            return False
    def embed(self, texts: list[str]) -> list[list[float]]:
        from modules.common import get_client
        client = get_client()
        if client is None:
            raise RuntimeError("No API key")
        # OpenRouter same API as OpenAI embeddings
        resp = client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

def get_provider() -> EmbeddingProvider:
    # prioridad: si hay API key, usar OpenAI, sino local
    try:
        p = OpenAIEmbedding()
        if p.is_available():
            return p
    except Exception:
        pass
    return LocalHashEmbedding()
