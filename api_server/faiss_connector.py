# api_server/faiss_connector.py
import json
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
# ER-RAG Configuration
# Add the 'r' before the quotes, and ensure consistent backslashes!
EMBEDDING_MODEL_NAME = r"D:\project\ER-RAG-Adaptation\models\all-Mini-L6-v2" 
RERANKER_MODEL_NAME = r"D:\project\ER-RAG-Adaptation\models\bge-reranker-v2-m3"
FAISS_INDEX_PATH = "../vector_database.index"
JSON_DATA_PATH = "../faiss_document.json"

print("[FAISS] Initializing Vector Models...")
try:
    # 1. Explicitly check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[FAISS] Loading models onto: {device.upper()}")

    # 2. Force the models onto the detected device
    print("[DEBUG] About to load Embedder...")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("[DEBUG] About to load Reranker...")
    reranker = CrossEncoder(RERANKER_MODEL_NAME)

    print("[DEBUG] About to load FAISS Index...")
   
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open(JSON_DATA_PATH, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    print(f"[FAISS] Ready. Loaded {index.ntotal} vectors.")
except Exception as e:
    print(f"[FAISS] Warning: Models/Data failed to load. {e}")
    index, documents = None, []

def vector_search(query: str, top_k: int = 20):
    """ER-RAG Two-Stage Dense Retrieval for Unstructured Text."""
    if not index or not documents:
        return [{"error": "FAISS database offline."}]

    try:
        query_embedding = embedder.encode([query]).astype('float32')
        fetch_k = min(50, len(documents))
        _, indices = index.search(query_embedding, fetch_k)

        candidates = [documents[idx] for idx in indices[0] if idx != -1 and idx < len(documents)]
        if not candidates: return []

        # Stage 2: Cross-Encoder Reranking
        # Adjust "clean_text" to match whatever key holds your text in faiss_document.json
        cross_inp = [[query, doc.get("document_content", str(doc))] for doc in candidates]
        cross_scores = reranker.predict(cross_inp)

        for i in range(len(candidates)):
            candidates[i]["rerank_score"] = float(cross_scores[i])

        candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_k]
    except Exception as e:
        print(f"FAISS Error: {e}")
        return []
    
def fetch_faiss_by_id(faiss_id: str):
    """Mengambil dokumen spesifik berdasarkan faiss_id (Direct Lookup)."""
    if not documents:
        return []
    
    # Mencari dokumen di dalam list documents yang dimuat dari JSON
    results = [doc for doc in documents if str(doc.get("faiss_id")) == str(faiss_id)]
    return results    