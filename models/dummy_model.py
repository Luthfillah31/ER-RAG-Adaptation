import requests
import json
import re

from models.pycragapi import CRAG 
from models.Parse import execute_api_chain

# ONLY import MySQL and your specific Mongo Partnership Schema
from models.prompt_api import MYSQL_SCHEMA, MONGODB_PARTNERSHIP_SCHEMA, WIKIBASE_SCHEMA

class RAGModel:
    def __init__(self):
        print("-------------------------Configuring API LLM--------------------------")
        self.ollama_api_url = "http://127.0.0.1:11434/api/generate"
        self.ollama_model = "deepseek-v3.1:671b-cloud" 
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
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            print(f"[LLM Error] Failed to reach Ollama: {e}")
            return ""

    def route_query(self, query):
        """
        Stage 1: Source Selection (The Router)
        Determines which internal databases are actually needed based on your specific private domain.
        """
        routing_prompt = f"""You are an elite data routing agent for our university's multi-database system. 
        Analyze the query and determine which internal data sources are required to answer it.
        
        ### Source Schema Overview:
        - MYSQL: Relational structured data. Contains internal records: dosen (lecturers), employee contracts, matakuliah (courses), meeting minutes, and projects.
        - FAISS: Unstructured text vector database. Contains the full-text content of our documents (meeting minutes, employee contracts, research papers).
        - WIKIBASE: Our internal knowledge graph. Contains complex relationships about our lecturers, published papers, patents, and institutional partnerships.
        - MONGO: Semi-structured document data. Contains our partnership news collection (web-scraped articles).
        
        ### Instruction:
        Return ONLY a comma-separated list of the required databases from the exact choices: [MYSQL, MONGO, FAISS, WIKIBASE]. No other text.
        
        Query: {query}
        Databases:"""
        
        response = self.llm_output([{"role": "user", "content": routing_prompt}], maxtoken=50)
        
        # Clean up output: "MYSQL, WIKIBASE" -> ["MYSQL", "WIKIBASE"]
        cleaned_response = response.replace(" ", "").upper()
        print(f"[DEBUG Router] Selected Databases: {cleaned_response}")
        return cleaned_response.split(',')

    def generate_dsl_command(self, query):
        """
        Stage 2: API Generation
        Dynamically builds the schema prompt ONLY for the databases selected by the router.
        """
        selected_dbs = self.route_query(query)
        
        dynamic_schema = ""
        available_commands = []
        
        if "MYSQL" in selected_dbs:
            dynamic_schema += MYSQL_SCHEMA + "\n"
            available_commands.extend([
                'mysql_search(table="<table_name>", column="<col_name>", search_term="<val>")',
                'mysql_fetch(table="<table_name>", <col1>="<val1>", ...)'
            ])
            
        if "MONGO" in selected_dbs:
            # Using the exact variable name from your file
            dynamic_schema += "=== MongoDB Partnership Schema ===\n"
            dynamic_schema += MONGODB_PARTNERSHIP_SCHEMA + "\n"
            available_commands.extend([
                'mongo_search(collection="<collection_name>", column="<col_name>", search_term="<val>")',
                'mongo_fetch(collection="<collection_name>", <col1>="<val1>", ...)'
            ])
            
        # Paper Compliance: NO SCHEMA for Wikibase/FAISS. Just instructions.
        if "WIKIBASE" in selected_dbs:
            dynamic_schema += "=== Wikibase Knowledge Graph ===\nContains global factual knowledge. No explicit schema required. Use natural language properties.\n\n"
            available_commands.extend([
                'wikibase_search(search_term="<val>")',
                'wikibase_fetch(subject="<Q_ID_or_PREVIOUS_id>")'
            ])
            
        if "FAISS" in selected_dbs:
            dynamic_schema += "=== FAISS Vector Database ===\nContains unstructured paragraph text. Semantic search only. No schema.\n\n"
            available_commands.extend([
                'faiss_search(query="<natural_language_sentence>")'
            ])
            
        # Fallback if router gets confused
        if not available_commands:
            available_commands = ['mysql_search', 'mysql_fetch', 'mongo_search', 'mongo_fetch', 'wikibase_search', 'wikibase_fetch', 'faiss_search']

        command_list_str = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(available_commands)])

        system_prompt = f"""You are a strict data routing assistant. Convert the user's query into a strict API command chain.
        
        {dynamic_schema}
        
        Available commands:
        {command_list_str}
        
        Rules:
        - NEVER use wildcards like "*" or "all" in _fetch commands. OMIT the argument entirely to get all records.
        - NEVER put a general noun (like "dosen", "project", "paper") inside a `search_term`. `search_term` MUST be a specific proper noun.
        - If the query asks about "all", "any", or does not mention a specific name (Global Query), DO NOT use _search. Start directly with an empty _fetch.
        - To pass data from a specific previous step, use {{STEP<N>_columnName}} (e.g., {{STEP1_id}} or {{STEP2_projectID}}). DO NOT use PREVIOUS_id anymore.
        - Respond ONLY with the exact API command string(s). No explanations.
        - To find Wikibase data for an entity found in MySQL, you MUST cross-reference their NAME first. Use `wikibase_search(search_term="{{STEP<N>_nama}}")` to get their Wikibase Q-ID, then use `wikibase_fetch(subject="{{STEP<M>_entity_id}}")`.
        
        ### EXAMPLES OF COMMAND CHAINS ###
        
        Query: "Apa saja project yang dikerjakan oleh Kemas?"
        mysql_search(table="dosen", column="nama", search_term="Kemas")
        mysql_fetch(table="projectassignment", idDosen="{{STEP1_id}}")
        mysql_fetch(table="project", id="{{STEP2_projectID}}")
        
        Query: "Apakah ada dosen yang papernya berbeda dengan projectnya?"
        mysql_fetch(table="dosen")
        mysql_fetch(table="projectassignment", idDosen="{{STEP1_id}}")
        mysql_fetch(table="project", id="{{STEP2_projectID}}")
        wikibase_fetch(subject="{{STEP1_id}}")
        
        Query: "Berikan saya semua data kontrak pegawai."
        mysql_fetch(table="employeecontract")
        
        Query: "Apa saja kerjasama Telkom dengan Indosat?"
        faiss_search(query="kerjasama Telkom dengan Indosat")
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}"}
        ]
        
        dsl_command = self.llm_output(messages, maxtoken=150)
        print(f"[DEBUG DSL] Generated commands:\n{dsl_command}")
        return dsl_command

    def post_process_data(self, query, raw_context):
        """
        Stage 3: Post-Processing
        Menggunakan skema langsung dari prompt_api.py sebagai referensi (Data Dictionary).
        """
        pp_prompt = f"""You are a data processing agent.
        Extract and format information from the retrieved JSON data.
        
        ### DATA DICTIONARY / SCHEMAS ###
        Use the following schemas to understand the keys, properties, or codes inside the JSON data (especially for Wikibase P-codes):
        
        {WIKIBASE_SCHEMA}
        
        {MYSQL_SCHEMA}
        
        {MONGODB_PARTNERSHIP_SCHEMA}
        
        CRITICAL RULE:
        If the user query requires SEMANTIC COMPARISON (e.g., comparing if a "Project Title" matches a "Paper Title" in meaning), DO NOT write python code to compare them. Python cannot understand meaning.
        Instead, just use python to GROUP the data neatly by entity. 
        
        Example formatting for semantic queries:
        "Lecturer: Kemas | Projects: [Title 1, Title 2] | Papers: [Paper 1, Paper 2]"
        
        Complete the Return part in this Python template:
        def solve(Data):
            return {{Return}}
            
        Replace {{Return}} with your generated list comprehension or f-string. NO markdown blocks.
        
        Query: {query}
        Data: {raw_context}
        Return: f\""""
        
        script = self.llm_output([{"role": "user", "content": pp_prompt}], maxtoken=300)
        script = script.replace('```python', '').replace('```', '').strip()
        print(f"[DEBUG Post-Process] Generated script: {script}")
        return script

    def generate_answer(self, query):
        """The Main ER-RAG Pipeline"""
        
        # 1. Generate the logical command (Includes Routing internally)
        dsl_command = self.generate_dsl_command(query)
        
        # 2. Execute the command
        context_str = execute_api_chain(dsl_command, self.api)
        
        if not context_str:
            print("[DEBUG] No DB Result. Proceeding without context...")
            return "I don't know based on the database."
            
        # 3. Post-Process (Generate the Python execution script)
        f_string_script = self.post_process_data(query, context_str)
        
        # 4. Final Answer Generation
        # Instead of risking a raw eval() in a prototype, we pass the generated logic 
        # back to the LLM to safely "execute" it in text.
        final_system_prompt = "You are a helpful assistant. Execute the logic described in the python f-string against the context to answer the user's question accurately."
        final_user_prompt = f"Context:\n{context_str}\n\nF-String Logic:\n{f_string_script}\n\nQuestion: {query}"
        
        messages = [
            {"role": "system", "content": final_system_prompt},
            {"role": "user", "content": final_user_prompt}
        ]
        
        final_answer = self.llm_output(messages, maxtoken=300)
        return final_answer