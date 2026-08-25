import time
import logging
from sqlalchemy import text
from app.db.session import sync_pmc_engine

logger = logging.getLogger("pmc_chatbot.schema")

_schema_cache = None
_cache_timestamp = 0
CACHE_TTL_SECONDS = 60  # Refresh schema dynamically every 60 seconds

CORE_TABLE_PATTERNS = [
    "complaint", "department", "ward", "prabhag", "category",
    "status", "user", "zone", "sub_category", "officer", "sla"
]

def fetch_live_database_schema() -> str:
    global _schema_cache, _cache_timestamp
    now = time.time()
    
    if _schema_cache and (now - _cache_timestamp < CACHE_TTL_SECONDS):
        return _schema_cache

    try:
        sql = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (
                table_name IN (
                  'complaint', 'department_master', 'ward_master', 'prabhag_master',
                  'category_master', 'sub_category_master', 'status_master', 'user_master',
                  'zone_master', 'sla_master', 'escalation_log'
                )
                OR table_name ILIKE '%master%'
                OR table_name ILIKE '%complaint%'
              )
            ORDER BY table_name, ordinal_position;
        """)

        with sync_pmc_engine.connect() as conn:
            rows = conn.execute(sql).fetchall()

        tables = {}
        for t_name, c_name, d_type in rows:
            tables.setdefault(t_name, []).append(f"{c_name} ({d_type})")

        schema_text_parts = [
            "You are an expert PostgreSQL Data Analyst AI for the Pune Municipal Corporation (PMC) Grievance & Officer Query System.",
            "Your job is to generate accurate, optimal PostgreSQL SELECT queries to answer officer questions.",
            "",
            "LIVE DATABASE SCHEMA (Inspected directly from PMC PostgreSQL information_schema):"
        ]

        for table_name, cols in tables.items():
            schema_text_parts.append(f"\nTable `{table_name}`:")
            for col in cols:
                schema_text_parts.append(f"  - {col}")

        schema_text_parts.append("\nRULES FOR QUERY GENERATION:")
        schema_text_parts.append("1. Always use exact table names and column names shown in the Live Schema above.")
        schema_text_parts.append("2. Case-insensitive searches on text fields should use ILIKE.")
        schema_text_parts.append("3. For pending complaints, check closed_at IS NULL or status_name ILIKE '%pending%'.")
        schema_text_parts.append("4. Return ONLY valid PostgreSQL SQL inside ```sql ... ``` code block.")

        _schema_cache = "\n".join(schema_text_parts)
        _cache_timestamp = now
        logger.info(f"Live database schema refreshed successfully ({len(tables)} tables loaded).")
        return _schema_cache
    except Exception as e:
        logger.error(f"Failed to fetch live schema from database: {e}")
        if _schema_cache:
            return _schema_cache
        raise e
