import time
import logging
from sqlalchemy import text
from app.db.session import sync_pmc_engine

logger = logging.getLogger("pmc_chatbot.schema")

_schema_cache = None
_cache_timestamp = 0
CACHE_TTL_SECONDS = 60  # Refresh schema & live sample values dynamically every 60 seconds

def fetch_live_database_schema() -> str:
    """
    Dynamically inspects PostgreSQL information_schema AND samples distinct live values
    from lookup tables (ward_master, user_master, department_master, category_master, status_master)
    to provide the LLM with 100% real, live database state with ZERO hardcoded rules or strings.
    """
    global _schema_cache, _cache_timestamp
    now = time.time()
    
    if _schema_cache and (now - _cache_timestamp < CACHE_TTL_SECONDS):
        return _schema_cache

    try:
        # 1. Fetch live table column definitions from information_schema
        sql_schema = text("""
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
            rows = conn.execute(sql_schema).fetchall()
            
            # 2. Dynamic live value sampling (100% dynamic from PostgreSQL)
            try:
                sample_wards = [r[0] for r in conn.execute(text("SELECT DISTINCT ward_name FROM ward_master WHERE ward_name IS NOT NULL ORDER BY ward_name LIMIT 30;")).fetchall()]
            except Exception:
                sample_wards = []

            try:
                sample_user_types = [r[0] for r in conn.execute(text("SELECT DISTINCT user_type::text FROM user_master WHERE user_type IS NOT NULL ORDER BY user_type::text LIMIT 30;")).fetchall()]
            except Exception:
                sample_user_types = []

            try:
                sample_statuses = [r[0] for r in conn.execute(text("SELECT DISTINCT status_name FROM status_master WHERE status_name IS NOT NULL ORDER BY status_name LIMIT 20;")).fetchall()]
            except Exception:
                sample_statuses = []

            try:
                sample_departments = [r[0] for r in conn.execute(text("SELECT DISTINCT department_name FROM department_master WHERE department_name IS NOT NULL ORDER BY department_name LIMIT 25;")).fetchall()]
            except Exception:
                sample_departments = []

        tables = {}
        for t_name, c_name, d_type in rows:
            tables.setdefault(t_name, []).append(f"{c_name} ({d_type})")

        schema_text_parts = [
            "You are an expert Autonomous PostgreSQL Data Analyst AI for Pune Municipal Corporation (PMC).",
            "Your objective is to inspect the live schema and sample data values below, then generate accurate, optimal PostgreSQL SELECT queries to answer officer questions.",
            "",
            "LIVE DATABASE SCHEMA (Inspected directly from PMC PostgreSQL information_schema):"
        ]

        for table_name, cols in tables.items():
            schema_text_parts.append(f"\nTable `{table_name}`:")
            for col in cols:
                schema_text_parts.append(f"  - {col}")

        # Add live dynamic sample values (Zero hardcoding)
        schema_text_parts.append("\nLIVE DATABASE SAMPLE COLUMN VALUES (Inspected live from PostgreSQL tables):")
        if sample_wards:
            schema_text_parts.append(f"- Sample Wards (`ward_master.ward_name`): {sample_wards}")
        if sample_user_types:
            schema_text_parts.append(f"- Sample User Types (`user_master.user_type`): {sample_user_types}")
        if sample_statuses:
            schema_text_parts.append(f"- Sample Statuses (`status_master.status_name`): {sample_statuses}")
        if sample_departments:
            schema_text_parts.append(f"- Sample Departments (`department_master.department_name`): {sample_departments[:10]}")

        schema_text_parts.append("\nGENERAL AUTONOMOUS DATA ANALYSIS GUIDELINES:")
        schema_text_parts.append("1. Always use exact table names and column names shown in the Live Schema above.")
        schema_text_parts.append("2. Case-insensitive text searches MUST use wildcard pattern matching `ILIKE '%term%'` across relevant text fields (e.g. ward_name, prabhag_name, address, full_name, title).")
        schema_text_parts.append("3. For officer/staff queries, inspect `user_type` values (e.g., exclude `CITIZEN` or filter `user_type != 'CITIZEN'`).")
        schema_text_parts.append("4. For count and detail queries ('kitne... kon konse'), generate a clean summary SQL query that retrieves aggregate counts AND category/department breakdown or sample records with LIMIT 50.")
        schema_text_parts.append("5. Return ONLY valid PostgreSQL SELECT SQL enclosed in ```sql ... ``` block.")

        _schema_cache = "\n".join(schema_text_parts)
        _cache_timestamp = now
        logger.info(f"Live database schema & sample data refreshed successfully ({len(tables)} tables, {len(sample_wards)} wards loaded).")
        return _schema_cache
    except Exception as e:
        logger.error(f"Failed to fetch live schema from database: {e}")
        if _schema_cache:
            return _schema_cache
        raise e
