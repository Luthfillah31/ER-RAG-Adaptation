# api_server/wikibase_connector.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WikibaseClient:
    """Your provided Wikibase Authentication Client"""
    def __init__(self, api_url, sparql_url, username, password):
        self.session = requests.Session()
        self.api_url = api_url
        self.sparql_url = sparql_url
        self.username = username
        self.password = password
        self.token = None
        self.login()
        self.csrf = self.get_csrf_token()
    
    def get_csrf_token(self):
        r = self.session.get(self.api_url, params={"action": "query", "meta": "tokens", "format": "json"})
        return r.json()["query"]["tokens"]["csrftoken"]

    def login(self):
        r1 = self.session.get(self.api_url, params={"action": "query", "meta": "tokens", "type": "login", "format": "json"})
        login_token = r1.json()["query"]["tokens"]["logintoken"]
        self.session.post(self.api_url, data={"action": "login", "lgname": self.username, "lgpassword": self.password, "lgtoken": login_token, "format": "json"})
        r3 = self.session.get(self.api_url, params={"action": "query", "meta": "tokens", "format": "json"})
        self.token = r3.json()["query"]["tokens"]["csrftoken"]

    def sparql_query(self, query):
        r = requests.get(self.sparql_url, params={"query": query, "format": "json"})
        return r.json()

# --- ER-RAG Unified API Implementation ---

def get_wb_client():
    return WikibaseClient(
        api_url=os.getenv("WIKIBASE_API_URL"),
        sparql_url=os.getenv("WIKIBASE_SPARQL_URL"),
        username=os.getenv("WIKIBASE_USERNAME"),
        password=os.getenv("WIKIBASE_PASSWORD")
    )

def search_wikibase(search_term: str):
    """
    Entity Resolution (Fuzzy Search): Uses MediaWiki API for lightning-fast label matching.
    """
    try:
        wb = get_wb_client()
        r = requests.get(wb.api_url, params={
            "action": "wbsearchentities",
            "search": search_term,
            "language": "en",
            "format": "json"
        })
        results = []
        for item in r.json().get('search', []):
            results.append({
                "id": item['id'], # e.g., Q123
                "label": item.get('label', ''),
                "description": item.get('description', '')
            })
        return results
    except Exception as e:
        print(f"Wikibase Search Error: {e}")
        return []

def fetch_wikibase(conditions: dict):
    """
    Exact Match / Multi-Hop Fetch: Dynamically builds SPARQL queries and supports Logical OR.
    """
    try:
        wb = get_wb_client()
        
        # If the LLM is fetching properties for specific entities (e.g., subject="Q1,Q2")
        target_entities = conditions.get("subject", "")
        
        if not target_entities:
            return []
            
        # ER-RAG Logical OR Support (Translates "Q1,Q2" into SPARQL VALUES)
        id_list = target_entities.split(',')
        values_clause = " ".join([f"wd:{qid}" for qid in id_list])
        
        # Dynamic SPARQL query to get all properties for the requested entities
        query = f"""
        SELECT ?subject ?subjectLabel ?predicate ?object ?objectLabel WHERE {{
          VALUES ?subject {{ {values_clause} }}
          ?subject ?predicate ?object .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,id". }}
        }} LIMIT 50
        """
        
        raw_data = wb.sparql_query(query)
        bindings = raw_data.get("results", {}).get("bindings", [])
        
        # Flatten the complex SPARQL JSON into a clean list of dictionaries for the LLM
        clean_results = []
        for b in bindings:
            clean_results.append({
                "subject_id": b.get("subject", {}).get("value", "").split("/")[-1],
                "subject_label": b.get("subjectLabel", {}).get("value", ""),
                "property_url": b.get("predicate", {}).get("value", ""),
                "object_value": b.get("objectLabel", {}).get("value", b.get("object", {}).get("value", ""))
            })
            
        return clean_results
    except Exception as e:
        print(f"Wikibase Fetch Error: {e}")
        return []