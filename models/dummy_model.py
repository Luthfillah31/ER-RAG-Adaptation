import os
import requests
import json
import re

from models.pycragapi import CRAG 
from models.Parse import execute_api_chain
from dotenv import load_dotenv 

load_dotenv()

from models.prompt_api import MYSQL_SCHEMA, MONGODB_PARTNERSHIP_SCHEMA, WIKIBASE_SCHEMA, FAISS_SCHEMA

class RAGModel:
    def __init__(self, platform="ollama", model=None):
        """
        Initializes the RAG Model with support for Ollama (Local) or OpenRouter (Cloud).
        :param platform: 'ollama' or 'openrouter'
        :param model: Optional specific model string
        """
        print(f"-------------------------Configuring {platform.upper()} LLM--------------------------")
        self.platform = platform.lower()
        self.api = CRAG()
        
        # Platform Settings
        if self.platform == "ollama":
            self.api_url = "http://127.0.0.1:11434/api/generate"
            self.model = model if model else "cogito-2.1:671b-cloud"
        elif self.platform == "openrouter":
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.api_key = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY")
            self.model = model if model else "qwen/qwen3.5-9b"
            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment!")
        else:
            raise ValueError("Platform must be 'ollama' or 'openrouter'")

    def llm_output(self, messages, maxtoken=512):
        """Standardized function to talk to Ollama or OpenRouter."""
        try:
            if self.platform == "ollama":
                # Ollama /api/generate protocol
                prompt = "".join([f"{m['role'].upper()}: {m['content']}\n" for m in messages]) + "ASSISTANT:"
                payload = {
                    "model": self.model, 
                    "prompt": prompt, 
                    "stream": False, 
                    "options": {"num_predict": maxtoken, "temperature": 0.0}
                }
                r = requests.post(self.api_url, json=payload, timeout=120)
                r.raise_for_status()
                return r.json().get("response", "")

            elif self.platform == "openrouter":
                # OpenRouter / OpenAI chat protocol
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": maxtoken,
                    "temperature": 0.0
                }
                r = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
                r.raise_for_status()
                return r.json()['choices'][0]['message']['content']

        except Exception as e:
            print(f"[LLM Error] Failed to reach {self.platform.upper()}: {e}")
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
        - FAISS: Unstructured text vector database. Contains the full-text content of our documents (meeting minutes, employee contracts,partnership news).
        - WIKIBASE: Our internal knowledge graph. Contains complex relationships about our lecturers, published papers, patents.
        - MONGO: Semi-structured document data. Contains our partnership news collection (web-scraped articles).
        
        ### Instruction:
        Return ONLY a comma-separated list of the required databases from the exact choices: [MYSQL, MONGO, FAISS, WIKIBASE]. No other text.
        
        Query: {query}
        Databases:"""
        
        response = self.llm_output([{"role": "user", "content": routing_prompt}], maxtoken=100)
        
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
            dynamic_schema += "=== MongoDB Partnership Schema ===\n"
            dynamic_schema += MONGODB_PARTNERSHIP_SCHEMA + "\n"
            available_commands.extend([
                'mongo_search(collection="<collection_name>", column="<col_name>", search_term="<val>")',
                'mongo_fetch(collection="<collection_name>", <col1>="<val1>", ...)'
            ])
            
        if "WIKIBASE" in selected_dbs:
            dynamic_schema += "=== Wikibase Knowledge Graph ===\nContains global factual knowledge. No explicit schema required. Use natural language properties.\n\n"
            available_commands.extend([
                'wikibase_search(search_term="<val>")',
                'wikibase_fetch(subject="<Q_ID_or_PREVIOUS_id>")'
            ])
            
        if "FAISS" in selected_dbs:
            dynamic_schema += "=== FAISS Vector Database ===\nUse faiss_search for semantic queries or faiss_fetch(faiss_id=\"...\") for specific IDs.\n\n"
            available_commands.extend([
                'faiss_search(query="<natural_language_sentence>")',
                'faiss_fetch(faiss_id="<id_from_previous_step>")'
            ])
            
        if not available_commands:
            available_commands = ['mysql_search', 'mysql_fetch', 'mongo_search', 'mongo_fetch', 'wikibase_search', 'wikibase_fetch', 'faiss_search']

        command_list_str = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(available_commands)])

        system_prompt = f"""You are a strict data routing assistant. Convert the user's query into a strict API command chain.
        
        {dynamic_schema}
        
        Available commands:
        {command_list_str}
        
        RULES & LOGIC:
        1. NO WILDCARDS: NEVER use "*" or "all" in _fetch. OMIT arguments entirely to fetch all rows (e.g., mysql_fetch(table="dosen")).
        2. NO GENERAL NOUNS: `search_term` MUST be a specific proper noun (e.g., "Kemas", NOT "dosen").
        3. DATA PASSING: Use {{STEP<N>_columnName}} to pass results (e.g., {{STEP1_id}}).
        4. FAISS USAGE: 
           - Use `faiss_search` for semantic topic/content discovery.
           - Use `faiss_fetch` for identity mapping when you already have a `faiss_id` from MySQL or Mongo.
        5. MONGODB PARTNERSHIPS: 
           - The collection name is STRICTLY `news`.
           - ALL records in MongoDB are ALREADY partners of Telkom University. DO NOT filter by `partner_name="Telkom University"`.
           - To get ALL partners, use exactly: `mongo_fetch(collection="news")` with NO other arguments.
        6. STRICT FORMATTING: You MUST output ONLY the API commands wrapped inside a ```python ... ``` code block. NO conversational text, NO explanations.
        BRIDGE PRINCIPLES (Multi-Hop Linkage):
        You must navigate the schema using these bridges:
        - [Dosen Bridge]: `dosen.id` <-> `employeecontract.IdDosen`, `mengajar.idDosen`, `projectassignment.idDosen`.
        - [Project Bridge]: `project.id` <-> `projectassignment.projectID`, `meetingminutes.projectID`.
        - [Document Bridge]: `faiss_id` (found in MySQL or Mongo) <-> FAISS `document_content`.
        - [Knowledge Bridge]: `dosen.nama` <-> `wikibase_search` to find `entity_id` (Q-ID) for papers/patents.

        ENTITY RESOLUTION PROTOCOL:
        - To answer questions about "Person A's paper vs project":
          1. Get Project data from MySQL (mysql_search -> mysql_fetch assignment -> mysql_fetch project).
          2. Resolve Person A in Wikibase (wikibase_search(term="{{STEP1_nama}}") -> wikibase_fetch(subject="{{STEP4_entity_id}}")).
          3. This allows Stage 4 to compare the retrieved metadata.

        STRICT RULES:
        1. ONLY USE commands listed in the "Available commands" section above.
        2. IF a command is not in the list, it is FORBIDDEN to use it, even if you see it in examples.
        3. DO NOT hallucinate commands from other databases that were not selected by the router.

        ### EXAMPLES OF COMMAND CHAINS (For Syntax Reference Only) ###
        
        Query: "What is the content of Kemas Rahmat's contract?"
        mysql_search(table="dosen", column="nama", search_term="Kemas Rahmat")
        mysql_fetch(table="employeecontract", IdDosen="{{STEP1_id}}")
        faiss_fetch(faiss_id="{{STEP2_faiss_id}}")

        Query: "Is Adiwijaya's project field aligned with their paper?"
        mysql_search(table="dosen", column="nama", search_term="Adiwijaya")
        mysql_fetch(table="projectassignment", idDosen="{{STEP1_id}}")
        mysql_fetch(table="project", id="{{STEP2_projectID}}")
        wikibase_search(search_term="{{STEP1_nama}}")
        wikibase_fetch(subject="{{STEP4_entity_id}}")

        Query: "Which lecturer has written a paper about Semantic?"
        faiss_search(query="paper about semantic")
        wikibase_search(search_term="semantic")
        wikibase_fetch(subject="{{STEP2_entity_id}}")
        mysql_search(table="dosen", column="nama", search_term="{{STEP3_subject_label}}")

        Query: "Who are the partners of Telkom University who have positive news?"
        mongo_fetch(collection="news")
        faiss_fetch(faiss_id="{{STEP1_faiss_id}}")
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}"}
        ]
        
        dsl_command = self.llm_output(messages, maxtoken=1000)
        print(f"[DEBUG DSL] Generated commands:\n{dsl_command}")
        return dsl_command

    def post_process_data(self, query, raw_context):
        """
        Stage 3: Post-Processing
        Diperkuat dengan FAISS Schema dan logika Identity Linking untuk data heterogen.
        """
        pp_prompt = f"""You are a data synthesis agent.
        Your goal is to write a Python f-string or list comprehension that organizes the retrieved data into a clear, readable format.
        
        ### DATA DICTIONARY / SCHEMAS ###
        Use these schemas to understand the keys and relationships across different databases:
        
        {WIKIBASE_SCHEMA}
        {MYSQL_SCHEMA}
        {MONGODB_PARTNERSHIP_SCHEMA}
        {FAISS_SCHEMA}
        
        ### CORE EXTRACTION RULES ###
        1. IDENTITY LINKING: Connect entities across different steps using their Names or IDs.
        2. DATA MAPPING: Translate P-codes (P1, P2, etc.) and technical keys into human-readable labels.
        3. UNSTRUCTURED CONTENT: If `document_content` from FAISS is present, extract the most relevant part or summarize its essence.
        4. GROUPING: Neatly group all information by the primary entity (usually the Lecturer/Dosen).
        5. NO SEMANTIC REASONING: Do not write python code to compare meanings. Simply list the attributes.
        
        Complete the Return part in this Python template:
        def solve(Data):
            return {{Return}}
            
        Replace {{Return}} with your generated logic. NO markdown blocks.
        
        Query: {query}
        Context Data: {raw_context}
        Return: f\""""
        
        script = self.llm_output([{"role": "user", "content": pp_prompt}], maxtoken=1000)
        script = script.replace('```python', '').replace('```', '').strip()
        print(f"[DEBUG Post-Process] Generated script: {script}")
        return script

    def generate_answer(self, query):
        """The Main ER-RAG Pipeline"""
        dsl_command = self.generate_dsl_command(query)
        context_str = execute_api_chain(dsl_command, self.api)
        
        if not context_str:
            print("[DEBUG] No DB Result. Proceeding without context...")
            return "I don't know based on the database."
            
        f_string_script = self.post_process_data(query, context_str)
        
        final_system_prompt = "You are a helpful assistant. Execute the logic described in the python f-string against the context to answer the user's question accurately."
        final_user_prompt = f"Context:\n{context_str}\n\nF-String Logic:\n{f_string_script}\n\nQuestion: {query}"
        
        messages = [
            {"role": "system", "content": final_system_prompt},
            {"role": "user", "content": final_user_prompt}
        ]
        
        return self.llm_output(messages, maxtoken=2000)