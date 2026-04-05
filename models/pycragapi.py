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
        
    # Later, you will add mongo_fetch, faiss_search, etc. here!