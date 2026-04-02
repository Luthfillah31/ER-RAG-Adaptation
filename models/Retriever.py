import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_core.documents import Document
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import numpy as np
import os

class Retriever:
    def __init__(self, device1="cpu", hf_path="models/all-Mini-L6-v2", reranker_path="models/bge-reranker-v2-m3"):
        from langchain.embeddings import HuggingFaceEmbeddings
        self.hf_embeddings = HuggingFaceEmbeddings(model_name=hf_path, model_kwargs={"device": device1})
        self.tokenizer = AutoTokenizer.from_pretrained("NousResearch/Meta-Llama-3-8B-Instruct")
        
        # LOCAL BGE RERANKER
        print(f"[DEBUG] Loading Local Reranker: {reranker_path}")
        try:
            self.rerank_tokenizer = AutoTokenizer.from_pretrained(reranker_path)
            self.rerank_model = AutoModelForSequenceClassification.from_pretrained(reranker_path)
            self.rerank_model.eval()
            self.device_rerank = "cuda" if torch.cuda.is_available() else "cpu"
            self.rerank_model.to(self.device_rerank)
        except Exception as e:
            print(f"[ERROR] Reranker load failed: {e}")
            self.rerank_model = None

        self.parent_text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
        self.child_text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)

    def call_local_reranker(self, query, docs, top_n=5):
        if not self.rerank_model or not docs: return docs[:top_n]
        pairs = [[query, doc.page_content] for doc in docs]
        with torch.no_grad():
            inputs = self.rerank_tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512).to(self.device_rerank)
            scores = self.rerank_model(**inputs).logits.view(-1,).float()
            combined = sorted(zip(docs, scores.cpu().tolist()), key=lambda x: x[1], reverse=True)
            return [x[0] for x in combined[:top_n]]

    def get_text(self, search_results, recall_k=10):
        docs = []
        hashes = set()
        for idx, html in enumerate(search_results):
            content = html.get('page_result', '')
            if not content or hash(content) in hashes: continue
            hashes.add(hash(content))
            soup = BeautifulSoup(content, 'html.parser')
            text = (html.get('page_snippet', '') + '\n\n' + soup.get_text(separator=' ', strip=True)).lower()
            docs.append(Document(page_content=text, metadata={"start_index": idx}))
        
        if not docs: return None
        vectorstore = Chroma(collection_name="parents", embedding_function=self.hf_embeddings)
        retriever = ParentDocumentRetriever(
            vectorstore=vectorstore, docstore=InMemoryStore(),
            child_splitter=self.child_text_splitter, parent_splitter=self.parent_text_splitter,
            search_kwargs={'k': recall_k}
        )
        retriever.add_documents(docs)
        return retriever