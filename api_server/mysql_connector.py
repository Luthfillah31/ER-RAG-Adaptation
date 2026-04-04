# api_server/mysql_connector.py
import pymysql
from dotenv import load_dotenv
import os
load_dotenv()
# 1. Setup your database connection parameters
DB_CONFIG = {
    'host': os.getenv("MYSQL_CONFIG_HOST"),
    'port': int(os.getenv("MYSQL_CONFIG_PORT")),
    'user': os.getenv("MYSQL_CONFIG_USER"),
    'password': os.getenv("MYSQL_CONFIG_PASSWORD"),
    'database': os.getenv("MYSQL_CONFIG_DB"),
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    return pymysql.connect(**DB_CONFIG)

def search_mysql(table: str, column: str, search_term: str):
    """
    Step 1: The Fuzzy Search.
    Finds up to 5 matching records based on a text search.
    """
    # Note: Table and column names cannot be parameterized normally in PyMySQL.
    # In production, validate that 'table' and 'column' are strictly alphanumeric to prevent injection.
    
    query = f"SELECT id, {column} FROM {table} WHERE {column} LIKE %s LIMIT 10"
    fuzzy_term = f"%{search_term}%"
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, (fuzzy_term,))
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"MySQL Search Error: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

def fetch_mysql_record(table: str, record_id: str):
    """
    Step 2: The Exact Fetch.
    Retrieves the entire row of data for a specific ID.
    """
    query = f"SELECT * FROM {table} WHERE id = %s"
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, (record_id,))
            result = cursor.fetchone() # Get the single matching row
            return result
    except Exception as e:
        print(f"MySQL Fetch Error: {e}")
        return None
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()