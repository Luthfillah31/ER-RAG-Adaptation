# api_server/wikibase_connector.py
import os
import requests
import re
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


def get_wb_client():
    return WikibaseClient(
        api_url=os.getenv("WIKIBASE_API_URL"),
        sparql_url=os.getenv("WIKIBASE_SPARQL_URL"),
        username=os.getenv("WIKIBASE_USERNAME"),
        password=os.getenv("WIKIBASE_PASSWORD")
    )

def search_wikibase(search_term: str):
    """
    Mendukung Batch Search dengan pembersihan gelar akademik.
    """
    try:
        wb = get_wb_client()
        names_to_search = [name.strip() for name in search_term.split(',') if name.strip()]
        all_results = []
        
        for name in names_to_search:
            clean_name = re.sub(r'^(Dr\.|Prof\.|Bapak\s|Ibu\s|Pak\s|Bu\s)\s*', '', name, flags=re.IGNORECASE)
            clean_name = re.sub(r',?\s*(Ph\.D\.|M\.Kom\.|S\.T\.|M\.T\.|S\.Si\.|M\.Si\.).*$', '', clean_name, flags=re.IGNORECASE)
            clean_name = clean_name.strip()
            
            r = requests.get(wb.api_url, params={
                "action": "wbsearchentities",
                "search": clean_name,
                "language": "en", 
                "format": "json",
                "limit": 1 
            })
            
            for item in r.json().get('search', []):
                all_results.append({
                    "entity_id": item['id'],             
                    "label": item.get('label', ''),      
                    "mysql_name": name                   
                })
                
        # PERBAIKAN: Return List langsung, jangan di-wrap dictionary!
        return all_results 

    except Exception as e:
        print(f"Wikibase Search Error: {e}")
        return []

def fetch_wikibase(conditions: dict):
    """
    Exact Match / Multi-Hop Fetch: Dynamically builds SPARQL queries and supports Logical OR.
    """
    try:
        wb = get_wb_client()
        target_entities = conditions.get("subject", "")
        
        if not target_entities:
            return []
            
        id_list = target_entities.split(',')
        values_clause = " ".join([f"wd:{qid}" for qid in id_list])
        
        query = f"""
        SELECT ?subject ?subjectLabel ?predicate ?object ?objectLabel WHERE {{
          VALUES ?subject {{ {values_clause} }}
          
          # Hanya ambil properti direct (wdt:) yang diawali dengan P
          ?subject ?predicate ?object .
          FILTER(STRSTARTS(STR(?predicate), "http://38.147.122.59/prop/direct/P"))
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,id". }}
        }} LIMIT 1000
        """
        
        raw_data = wb.sparql_query(query)
        bindings = raw_data.get("results", {}).get("bindings", [])
        
        clean_results = []
        for b in bindings:
            clean_results.append({
                "subject_id": b.get("subject", {}).get("value", "").split("/")[-1],
                "subject_label": b.get("subjectLabel", {}).get("value", ""),
                "property_url": b.get("predicate", {}).get("value", "").split("/")[-1],
                "object_value": b.get("objectLabel", {}).get("value", b.get("object", {}).get("value", ""))
            })
            
        # PERBAIKAN: Return List langsung!
        return clean_results
    except Exception as e:
        print(f"Wikibase Fetch Error: {e}")
        return []