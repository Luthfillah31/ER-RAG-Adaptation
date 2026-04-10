# api_server/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import the database functions we just wrote
from mysql_connector import search_mysql, fetch_mysql
from mongo_connector import search_mongo, fetch_mongo
# Add to imports
from wikibase_connector import search_wikibase, fetch_wikibase
from faiss_connector import vector_search

app = FastAPI(title="ER-RAG Unified Data API")

# --- Define Request Schemas ---
class SearchRequest(BaseModel):
    table: str
    column_to_search: str
    search_term: str

# Ubah FetchRequest menjadi seperti ini:
class FetchRequest(BaseModel):
    table: str
    conditions: dict

class WikibaseFetchRequest(BaseModel):
    conditions: dict

class VectorRequest(BaseModel):
    query: str

# --- Step 1: The Search Endpoint ---
@app.post("/api/mysql/search")
def api_search_mysql(request: SearchRequest):
    """Endpoint for fuzzy searching entities (e.g., finding a user by name)."""
    
    results = search_mysql(
        table=request.table, 
        column=request.column_to_search, 
        search_term=request.search_term
    )
    
    if not results:
        return {"results": [], "message": "No matching entities found."}
        
    return {"results": results}

# Ubah endpoint fetch menjadi seperti ini:
@app.post("/api/mysql/fetch")
def api_fetch_mysql_records(request: FetchRequest):
    """Universal endpoint to fetch records based on multiple conditions."""
    records = fetch_mysql(table=request.table, conditions=request.conditions)
    
    if not records:
        return {"results": [], "message": "No records found."}
    return {"results": records}

# Add these endpoints at the bottom of the file
@app.post("/api/mongo/search")
def api_search_mongo(request: SearchRequest):
    """Universal endpoint to search MongoDB collections."""
    results = search_mongo(
        collection=request.table, 
        column=request.column_to_search, 
        search_term=request.search_term
    )
    if not results:
        return {"results": [], "message": "No matching documents found in Mongo."}
    return {"results": results}

@app.post("/api/mongo/fetch")
def api_fetch_mongo(request: FetchRequest):
    """Universal endpoint to fetch records based on multiple conditions."""
    records = fetch_mongo(collection=request.table, conditions=request.conditions)
    if not records:
        return {"results": [], "message": "No records found in Mongo."}
    return {"results": records}

# --- Wikibase Endpoints ---
@app.post("/api/wikibase/search")
def api_search_wikibase(request: SearchRequest):
    results = search_wikibase(search_term=request.search_term)
    return {"results": results}

@app.post("/api/wikibase/fetch")
def api_fetch_wikibase(request: WikibaseFetchRequest):
    records = fetch_wikibase(conditions=request.conditions)
    return {"results": records}

# --- FAISS Endpoint ---
@app.post("/api/faiss/search")
def api_vector_search(request: VectorRequest):
    records = vector_search(query=request.query)
    return {"results": records}