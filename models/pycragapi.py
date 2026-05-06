import os
import requests

class CRAG(object):
    """
    Client for interacting with your custom FastAPI Data Server.
    """    
    def __init__(self):
        # Konsisten menggunakan satu variabel dasar
        self.server = os.getenv("CRAG_MOCK_API_URL", "http://127.0.0.1:8000")
    
    def mysql_search(self, table: str, column: str, search_term: str):
        url = self.server + '/api/mysql/search'
        data = {
            'table': table,
            'column_to_search': column,
            'search_term': search_term
        }
        result = requests.post(url, json=data)
        return result.json()

    def mysql_fetch(self, table: str, **kwargs):
        url = self.server + '/api/mysql/fetch'
        data = {
            'table': table,
            'conditions': kwargs 
        }
        result = requests.post(url, json=data)
        return result.json()
        
    def mongo_search(self, collection: str, column: str, search_term: str):
        url = self.server + '/api/mongo/search'
        # PERBAIKAN: Gunakan key 'table' agar sesuai dengan SearchRequest di main.py
        data = {
            'table': collection, 
            'column_to_search': column,
            'search_term': search_term
        }
        result = requests.post(url, json=data)
        return result.json()

    def mongo_fetch(self, collection: str, **kwargs):
        url = self.server + '/api/mongo/fetch'
        # PERBAIKAN: Gunakan key 'table' agar sesuai dengan FetchRequest di main.py
        data = {
            'table': collection, 
            'conditions': kwargs 
        }
        result = requests.post(url, json=data)
        return result.json()
    
    def wikibase_search(self, search_term: str):
        url = self.server + '/api/wikibase/search'
        # Menggunakan format SearchRequest standar
        result = requests.post(url, json={'table': 'wiki', 'column_to_search': '', 'search_term': search_term})
        return result.json()

    def wikibase_fetch(self, **kwargs):
        url = self.server + '/api/wikibase/fetch'
        # Sesuai dengan WikibaseFetchRequest di main.py
        result = requests.post(url, json={'conditions': kwargs})
        return result.json()

    def faiss_search(self, query: str):
        url = self.server + '/api/faiss/search'
        result = requests.post(url, json={'query': query})
        return result.json()
    
    def faiss_fetch(self, faiss_id: str):
        """
        Pencarian Eksak berdasarkan ID (Identity Mapping).
        Menghubungkan faiss_id dari MySQL ke dokumen di FAISS.
        """
        # PERBAIKAN URL: Gunakan self.server dan tambahkan /api/
        url = self.server + '/api/faiss/fetch'
        payload = {
            "table": "faiss", 
            "conditions": {"faiss_id": faiss_id}
        }
        r = requests.post(url, json=payload)
        return r.json()