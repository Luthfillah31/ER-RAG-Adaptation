# api_server/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import the database functions we just wrote
from mysql_connector import search_mysql, fetch_mysql_record

app = FastAPI(title="ER-RAG Unified Data API")

# --- Define Request Schemas ---
class SearchRequest(BaseModel):
    table: str
    column_to_search: str
    search_term: str

class FetchRequest(BaseModel):
    table: str
    record_id: str

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

# --- Step 2: The Fetch Endpoint ---
@app.post("/api/mysql/get_record")
def api_get_mysql_record(request: FetchRequest):
    """Endpoint for fetching the full JSON data of a specific entity using its ID."""
    
    record = fetch_mysql_record(
        table=request.table, 
        record_id=request.record_id
    )
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    return {"result": record}

# --- Future Endpoints (Placeholders for your other DBs) ---
@app.post("/api/mongo/get_document")
def api_get_mongo_document():
    pass 
    # You will create mongo_connector.py later and plug it in here!