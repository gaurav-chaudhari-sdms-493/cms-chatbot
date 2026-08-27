import time
import logging
from sqlalchemy import text
from app.db.session import sync_pmc_engine

logger = logging.getLogger("pmc_chatbot.schema")

_schema_cache = None
_cache_timestamp = 0
CACHE_TTL_SECONDS = 300

def fetch_live_database_schema() -> str:
    """
    Returns raw table and column names directly from PostgreSQL information_schema.
    Contains ZERO guidelines, ZERO instructions, and ZERO hardcoded rules.
    """
    global _schema_cache, _cache_timestamp
    now = time.time()
    
    if _schema_cache and (now - _cache_timestamp < CACHE_TTL_SECONDS):
        return _schema_cache

    try:
        sql_schema = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        with sync_pmc_engine.connect() as conn:
            rows = conn.execute(sql_schema).fetchall()

        tables = {}
        for t_name, c_name, d_type in rows:
            tables.setdefault(t_name, []).append(f"{c_name} ({d_type})")

        catalog_lines = ["DATABASE TABLES & COLUMNS:"]
        for table_name, cols in tables.items():
            catalog_lines.append(f"\nTable `{table_name}`:")
            for col in cols:
                catalog_lines.append(f"  - {col}")

        _schema_cache = "\n".join(catalog_lines)
        _cache_timestamp = now
        return _schema_cache
    except Exception as e:
        logger.error(f"Failed to fetch schema: {e}")
        if _schema_cache:
            return _schema_cache
        raise e
