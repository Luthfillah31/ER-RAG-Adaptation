import torch
import requests
import json
from transformers import AutoTokenizer
import models.Retriever as Retriever
from models.Parse import parse_answer
from models.prompt_api import template_map

class RAGModel:
    def __init__(self):
        self.Task = 3
        print("-------------------------Configuring Ollama Local--------------------------")
        self.ollama_api_url = "http://127.0.0.1:11434/api/generate"
        self.ollama_model = "deepseek-v3.1:671b-cloud"
        
        self.tokenizer = AutoTokenizer.from_pretrained("NousResearch/Meta-Llama-3-8B-Instruct")
        self.used1 = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load Retriever & Reranker Lokal (HAPUS device2)
        self.r = Retriever.Retriever(
            device1=self.used1, 
            reranker_path="models/bge-reranker-v2-m3"
        )

    def llam3_output(self, messages, maxtoken=512):
        prompt = "".join([f"{m['role'].upper()}: {m['content']}\n" for m in messages]) + "ASSISTANT:"
        payload = {
            "model": self.ollama_model, 
            "prompt": prompt, 
            "stream": False, 
            "options": {"num_predict": maxtoken, "temperature": 0.0}
        }
        try:
            r = requests.post(self.ollama_api_url, json=payload, timeout=120)
            return r.json()['response'], 0, 0
        except Exception as e: 
            print(f"[ERROR] Ollama: {e}")
            return "i don't know", 0, 0

    def generate_answer(self, query, search_results, query_time):
        # 1. Tentukan Domain Terlebih Dahulu
        judge_prompt = template_map['judge_domain'].format(query_str=query)
        domain, _, _ = self.llam3_output([{"role": "user", "content": judge_prompt}])
        
        context_str = ""
        
        # Jika BUKAN Open Domain, coba cari di Database Lokal (CSV/NPY)
        if "open" not in domain.lower():
            api_prompt = template_map['api_prompt'].format(query_str=query)
            api_call, _, _ = self.llam3_output([{"role": "user", "content": api_prompt}])
            _, context_from_db = parse_answer(api_call)
            
            # Jika API Hallucination atau DB kosong
            if not context_from_db or "None" in str(context_from_db):
                print("[DEBUG] API Hallucination Detected or No DB Result. Switching to Web RAG...")
                context_str = "" 
            else:
                context_str = "\n".join(context_from_db)

        # 2. Local Retrieval (Reranker Web) 
        # Berjalan jika kueri adalah "Open Domain" ATAU jika Database Lokal kosong/gagal
        if not context_str:
            print("[DEBUG] Calling Local RAG Pipeline...")
            # Panggil fungsi Reranker web snippets (Sesuaikan nama fungsi get_text atau get_result dengan Retriever Anda)
            retriever = self.r.get_text(search_results)
            if retriever:
                docs = retriever.get_relevant_documents(query)
                reranked_docs = self.r.call_local_reranker(query, docs)
                context_str = "".join([f"<DOC>\n{d.page_content}\n</DOC>\n" for d in reranked_docs])
        
        # 3. Hasilkan Jawaban Akhir (Final Generation)
        filled = template_map['output_answer_nofalse'].format(context_str=context_str, query_str=query)
        return self.llam3_output([{"role": "user", "content": filled}])[0]