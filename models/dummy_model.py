import requests
import json
import re

# Import the new client we just built
from models.pycragapi import CRAG 
from models.Parse import execute_api_chain # We will build this in Step 3!
from models.prompt_api import MYSQL_SCHEMA

class RAGModel:
    def __init__(self):
        print("-------------------------Configuring API LLM--------------------------")
        self.ollama_api_url = "http://127.0.0.1:11434/api/generate"
        self.ollama_model = "deepseek-v3.1:671b-cloud" # Ensure this model name is exactly what Ollama expects
        
        # Instantiate your custom FastAPI client
        self.api = CRAG()

    def llm_output(self, messages, maxtoken=512):
        """Standardized function to talk to your Ollama API."""
        prompt = "".join([f"{m['role'].upper()}: {m['content']}\n" for m in messages]) + "ASSISTANT:"
        
        payload = {
            "model": self.ollama_model, 
            "prompt": prompt, 
            "stream": False, 
            "options": {"num_predict": maxtoken, "temperature": 0.0}
        }
        
        try:
            r = requests.post(self.ollama_api_url, json=payload, timeout=120)
            return r.json().get('response', "i don't know").strip()
        except Exception as e: 
            print(f"[ERROR] LLM API: {e}")
            return "i don't know"

    def generate_dsl_command(self, query):
        """
        Step 1: Ask the LLM to translate the user's natural language into 
        your custom Domain Specific Language (DSL).
        """
        # We inject the schema directly into the system instructions
        system_prompt = f"""You are a strict data routing assistant. Convert the user's query into a strict API command chain.
        
        {MYSQL_SCHEMA}
        
        Available commands:
        1. mysql_search(table="<table_name>", column="<col_name>", search_term="<val>")
        2. mysql_fetch(table="<table_name>", <col1>="<val1>", <col2>="<val2>", ...)
        
        Rules:
        - You MUST use ONLY the table and column names provided in the Schema above.
        - If the user provides a fuzzy name, use mysql_search.
        - For mysql_fetch, YOU MUST add as many column arguments as needed to strictly filter the data.
        - For multi-hop queries, output MULTIPLE commands on separate lines.
        - To pass data from Step 1 to Step 2, use {{PREVIOUS_columnName}} (e.g., {{PREVIOUS_id}} or {{PREVIOUS_matakuliahID}}). The columnName MUST exactly match a column returned by the previous table.
        - Respond ONLY with the exact API command string(s). No explanations.
        
        Example Multi-Hop Query with strict filtering and dynamic joins:
        mysql_search(table="dosen", column="nama", search_term="Kemas")
        mysql_fetch(table="projectassignment", idDosen="{{PREVIOUS_id}}")
        mysql_fetch(table="project", id="{{PREVIOUS_matakuliahID}}")
        """
        
        user_prompt = f"Query: {query}\nCommand:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        dsl_command = self.llm_output(messages, maxtoken=200)
        print(f"[DEBUG] Generated DSL: {dsl_command}")
        return dsl_command

    def generate_answer(self, query):
        """
        The Main Pipeline: Route -> Fetch Data -> Answer
        (Notice we removed the KDDCup 'search_results' and 'query_time' arguments)
        """
        # 1. Generate the logical command
        dsl_command = self.generate_dsl_command(query)
        
        # 2. Execute the command using your Parse script and FastAPI wrapper
        # If the LLM generates a bad command, this returns an empty string
        context_str = execute_api_chain(dsl_command, self.api)
        
        # Fallback: If no context was found in the DB, let the LLM know
        if not context_str:
            print("[DEBUG] No DB Result. Proceeding without context...")
            context_str = "No database records found for this query."
            
        # 3. Final Generation: Answer the user based on the real data
        final_system_prompt = "You are a helpful assistant. Answer the user's question accurately using strictly the provided database context. If the context does not contain the answer, say 'I don't know based on the database'."
        final_user_prompt = f"Context:\n<DOC>\n{context_str}\n</DOC>\n\nQuestion: {query}"
        
        messages = [
            {"role": "system", "content": final_system_prompt},
            {"role": "user", "content": final_user_prompt}
        ]
        
        final_answer = self.llm_output(messages, maxtoken=512)
        return final_answer