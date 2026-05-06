# api_server/wikibase_connector.py
import os
import requests
import re
import difflib
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
    try:
        wb = get_wb_client()
        
        # 1. PECAH STRING BERDASARKAN KOMA (Batch Processing)
        names_to_search = [name.strip() for name in search_term.split(',') if name.strip()]
        final_batch_results = []
        
        # Fungsi pembantu untuk mengambil data API
        def fetch_api(keyword, limit=20):
            results = []
            for lang in ['id', 'en']:
                r = requests.get(wb.api_url, params={
                    "action": "wbsearchentities",
                    "search": keyword, 
                    "language": lang,
                    "format": "json",
                    "limit": limit
                })
                results.extend(r.json().get('search', []))
            return results

        # 2. PROSES SETIAP NAMA SATU PER SATU
        for name in names_to_search:
            clean_name = re.sub(r'^(Dr\.|Prof\.|Bapak\s|Ibu\s|Pak\s|Bu\s)\s*', '', name, flags=re.IGNORECASE).strip()
            base_keyword = clean_name
            
            api_data = fetch_api(base_keyword)
            
            # Fallback jika tidak ketemu utuh
            if not api_data:
                words = clean_name.split()
                if len(words) > 1:
                    api_data = fetch_api(words[0], limit=30)
                    
            if not api_data:
                continue # Lewati nama ini jika memang tidak ada di Wikibase
                
            # Fuzzy Matching lokal KHUSUS untuk nama ini
            person_results = []
            for item in api_data:
                label = item.get('label', '')
                if not any(res['entity_id'] == item['id'] for res in person_results):
                    similarity_score = difflib.SequenceMatcher(None, clean_name.lower(), label.lower()).ratio()
                    person_results.append({
                        "entity_id": item['id'],
                        "label": label,
                        "mysql_name": name, 
                        "score": similarity_score
                    })
                    
            # Urutkan dari skor tertinggi
            person_results = sorted(person_results, key=lambda x: x["score"], reverse=True)
            
            if person_results:
                # --- PERBAIKAN LOGIKA DISINI ---
                if len(names_to_search) > 1:
                    # MODE DOSEN (Batch): Jika ada banyak nama dipisah koma, ambil 1 TERBAIK per orang
                    final_batch_results.append({
                        "entity_id": person_results[0]["entity_id"],
                        "label": person_results[0]["label"],
                        "mysql_name": person_results[0]["mysql_name"]
                    })
                else:
                    # MODE TOPIK/PAPER (Single Query): Jika mencari 1 kata kunci, ambil TOP 10
                    # Anda bisa menaikkan angka 10 menjadi 20 jika ingin data lebih banyak
                    for res in person_results[:10]:
                        final_batch_results.append({
                            "entity_id": res["entity_id"],
                            "label": res["label"],
                            "mysql_name": res["mysql_name"]
                        })
                
        return final_batch_results

    except Exception as e:
        print(f"Wikibase Search Error: {e}")
        return []

# api_server/wikibase_connector.py

def fetch_wikibase(conditions: dict):
    try:
        wb = get_wb_client()
        target_entities = conditions.get("subject", "")
        
        if not target_entities:
            return []
            
        id_list = target_entities.split(',')
        # Menghasilkan "wd:Q54 wd:Q56" dst
        values_clause = " ".join([f"wd:{qid}" for qid in id_list])
        
        # WAJIB: Menambahkan PREFIX agar SPARQL mengenali wd: dan wdt:
        query = f"""
        PREFIX wd: <http://38.147.122.59/entity/>
        PREFIX wdt: <http://38.147.122.59/prop/direct/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX bd: <http://www.bigdata.com/rdf#>

        SELECT ?subject ?subjectLabel ?predicate ?object ?objectLabel WHERE {{
          VALUES ?subject {{ {values_clause} }}
          
          # Mengambil properti direct (wdt:)
          ?subject ?predicate ?object .
          
          # Filter agar hanya mengambil properti substantif (P1, P2, dst)
          FILTER(STRSTARTS(STR(?predicate), STR(wdt:)))
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "id,en". }}
        }} LIMIT 15000
        """
        
        raw_data = wb.sparql_query(query)
        bindings = raw_data.get("results", {}).get("bindings", [])
        
        clean_results = []
        for b in bindings:
            clean_results.append({
                "subject_id": b.get("subject", {}).get("value", "").split("/")[-1],
                "subject_label": b.get("subjectLabel", {}).get("value", ""),
                # Memastikan property_url hanya berisi kode (contoh: "P1")
                "property_url": b.get("predicate", {}).get("value", "").split("/")[-1],
                "object_value": b.get("objectLabel", {}).get("value", b.get("object", {}).get("value", ""))
            })
            
        return clean_results
    except Exception as e:
        print(f"Wikibase Fetch Error: {e}")
        return []