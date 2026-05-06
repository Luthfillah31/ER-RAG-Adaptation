import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

def get_mongo_collection(collection_name: str):
    """Connects to the remote MongoDB server."""
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DB_NAME")]
    return db[collection_name]

def search_mongo(collection: str, column: str, search_term: str):
    """The Fuzzy Search (Entity Resolution) for MongoDB."""
    try:
        col = get_mongo_collection(collection)
        # $regex provides fuzzy matching, $options: 'i' makes it case-insensitive
        query = {column: {"$regex": search_term, "$options": "i"}}
        
        # We exclude the MongoDB '_id' because it's a complex object that breaks JSON serialization
        results = list(col.find(query, {"_id": 0}).limit(10)) 
        return results
    except Exception as e:
        print(f"MongoDB Search Error: {e}")
        return []

def fetch_mongo(collection: str, conditions: dict):
    """Multi-Condition Fetch applying the Logical OR ($in clause) from the ER-RAG paper."""
    try:
        col = get_mongo_collection(collection)
        query = {}
        
        if conditions:
            for k, v in conditions.items():
                if "," in str(v):
                    # It's a set from a previous GET step. Use Logical OR ($in)
                    query[k] = {"$in": str(v).split(",")}
                else:
                    # Standard Exact Match
                    query[k] = v
                    
        # --- PERBAIKAN: Inclusive Projection (Hanya ambil partner_name) ---
        # 1 artinya "ambil ini", 0 artinya "jangan ambil ini"
        projection = {"_id": 0, "partner_name": 1}
        
        results = list(col.find(query, projection).limit(1000))
        return results
    except Exception as e:
        print(f"MongoDB Fetch Error: {e}")
        return []