import os
import requests

class CRAG(object):
    """
    Client for interacting with your custom FastAPI Data Server.
    """    
    def __init__(self):
        # This points to your locally running FastAPI server
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
        # kwargs akan berisi semua filter tambahan yang dihasilkan LLM
        url = self.server + '/api/mysql/fetch'
        data = {
            'table': table,
            'conditions': kwargs 
        }
        result = requests.post(url, json=data)
        return result.json()
        
    def mongo_search(self, collection: str, column: str, search_term: str):
        url = self.server + '/api/mongo/search'
        data = {
            'collection': collection,
            'column_to_search': column,
            'search_term': search_term
        }
        result = requests.post(url, json=data)
        return result.json()

    def mongo_fetch(self, collection: str, **kwargs):
        url = self.server + '/api/mongo/fetch'
        data = {
            'collection': collection,
            'conditions': kwargs 
        }
        result = requests.post(url, json=data)
        return result.json()
    
    def wikibase_search(self, search_term: str):
        url = self.server + '/api/wikibase/search'
        result = requests.post(url, json={'table': 'wiki', 'column_to_search': '', 'search_term': search_term})
        return result.json()

    def wikibase_fetch(self, **kwargs):
        url = self.server + '/api/wikibase/fetch'
        result = requests.post(url, json={'conditions': kwargs})
        return result.json()

    def faiss_search(self, query: str):
        url = self.server + '/api/faiss/search'
        result = requests.post(url, json={'query': query})
        return result.json()