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
    The Fuzzy Search.
    Finds up to 10 matching records based on a text search.
    """
    # Note: Table and column names cannot be parameterized normally in PyMySQL.
    # In production, validate that 'table' and 'column' are strictly alphanumeric to prevent injection.
    
    query = f"SELECT * FROM {table} WHERE {column} LIKE %s LIMIT 10"
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

def fetch_mysql(table: str, conditions: dict):
    """Multi-Condition Fetch applying the Logical OR (IN clause) from the paper."""
    if not conditions:
        query = f"SELECT * FROM {table} LIMIT 50"
        values = ()
    else:
        where_clauses = []
        values = []
        for k, v in conditions.items():
            # If the value contains commas, it's a Set from the previous GET. Use Logical OR (IN)
            if "," in str(v):
                id_list = str(v).split(",")
                # Creates placeholders like: idDosen IN (%s, %s)
                placeholders = ", ".join(["%s"] * len(id_list))
                where_clauses.append(f"{k} IN ({placeholders})")
                values.extend(id_list)
            else:
                # Standard Exact Match
                where_clauses.append(f"{k} = %s")
                values.append(v)
                
        where_string = " AND ".join(where_clauses)
        query = f"SELECT * FROM {table} WHERE {where_string}"
        values = tuple(values)
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, values)
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"MySQL Fetch Error: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()