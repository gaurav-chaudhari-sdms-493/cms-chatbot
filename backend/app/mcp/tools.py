"""
MCP Tools module for PMC Grievance Intelligence System.
Exposes standardized database execution, introspection, and sampling tools.
"""
import re
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.db.session import sync_pmc_engine

logger = logging.getLogger("pmc_chatbot.mcp_tools")

# SQL Safety Validator
FORBIDDEN_SQL_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b",
    r"\bTRUNCATE\b", r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b", r"\bEXEC\b"
]

def execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Executes a read-only PostgreSQL SELECT query against PMC database.
    
    Args:
        sql_query: The PostgreSQL SELECT query string to execute.
        
    Returns:
        Dictionary containing columns, rows, row_count, and execution status.
    """
    cleaned_sql = sql_query.strip().rstrip(";")
    
    # 1. Safety validation
    for pattern in FORBIDDEN_SQL_KEYWORDS:
        if re.search(pattern, cleaned_sql, re.IGNORECASE):
            return {
                "status": "ERROR",
                "error": f"Security Error: Non-SELECT or mutating statement detected: {cleaned_sql}",
                "columns": [],
                "rows": []
            }
            
    if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
        return {
            "status": "ERROR",
            "error": "Security Error: Query must begin with SELECT or WITH.",
            "columns": [],
            "rows": []
        }

    # 2. Append LIMIT 50 if missing
    if "LIMIT" not in cleaned_sql.upper():
        cleaned_sql += " LIMIT 50"

    # 3. Enforce 8s statement timeout
    timeout_sql = f"SET statement_timeout = 8000; {cleaned_sql};"

    try:
        with sync_pmc_engine.connect() as conn:
            result = conn.execute(text(timeout_sql))
            columns = list(result.keys()) if result.returns_rows else []
            raw_rows = result.fetchall() if result.returns_rows else []
            
            # Format rows as lists of stringified values
            rows = [[str(val) if val is not None else "" for val in row] for row in raw_rows]
            
            return {
                "status": "SUCCESS",
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "sql_executed": cleaned_sql
            }
    except Exception as e:
        logger.error(f"MCP SQL Execution Error: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "columns": [],
            "rows": []
        }


def sample_column_values(table_name: str, column_name: str, limit: int = 20) -> List[str]:
    """
    Samples distinct non-null values for a specific table column live from PostgreSQL.
    
    Args:
        table_name: PostgreSQL table name (e.g. 'ward_master', 'user_master').
        column_name: Target column name (e.g. 'ward_name', 'user_type').
        limit: Max distinct values to return (default 20).
        
    Returns:
        List of distinct string values.
    """
    # Sanitize identifier names
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name) or not re.match(r"^[a-zA-Z0-9_]+$", column_name):
        return []

    sql = text(f"SELECT DISTINCT {column_name}::text FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY 1 LIMIT {limit};")
    try:
        with sync_pmc_engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [str(r[0]) for r in rows if r[0] is not None]
    except Exception as e:
        logger.error(f"Error sampling {table_name}.{column_name}: {e}")
        return []


def inspect_table_columns(table_name: str) -> List[Dict[str, str]]:
    """
    Returns data types and column names for a specified table from information_schema.
    
    Args:
        table_name: Target PostgreSQL table name.
        
    Returns:
        List of dictionaries with column_name and data_type.
    """
    sql = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :table_name
        ORDER BY ordinal_position;
    """)
    try:
        with sync_pmc_engine.connect() as conn:
            rows = conn.execute(sql, {"table_name": table_name}).fetchall()
            return [{"column_name": r[0], "data_type": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"Error inspecting table {table_name}: {e}")
        return []
