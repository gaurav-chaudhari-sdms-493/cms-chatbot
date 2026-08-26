"""
MCP Resources module for PMC Grievance Intelligence System.
Exposes dynamic PostgreSQL database schema and metadata as standard MCP Resources.
"""
from app.db.dynamic_schema import fetch_live_database_schema

def get_live_db_schema_resource() -> str:
    """
    Returns live PostgreSQL information_schema definitions and sampled distinct column values.
    URI: pmc://database/schema
    """
    return fetch_live_database_schema()
