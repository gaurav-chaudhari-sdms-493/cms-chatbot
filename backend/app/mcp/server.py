"""
Official Standard FastMCP Protocol Server for PMC Grievance Intelligence System.
Exposes MCP Tools and Resources over stdio and SSE transport.
"""
import logging
from fastmcp import FastMCP
from app.mcp.resources import get_live_db_schema_resource
from app.mcp.tools import execute_sql_query, sample_column_values, inspect_table_columns

logger = logging.getLogger("pmc_chatbot.mcp_server")

# Construct FastMCP instance
mcp_server = FastMCP(
    name="PMC Grievance Intelligence MCP",
    instructions="Official PMC Municipal Grievance & Officer Query System MCP Server. Provides read-only PostgreSQL data execution, live schema introspection, and value sampling tools."
)

# Register Resources
@mcp_server.resource("pmc://database/schema")
def live_database_schema() -> str:
    """Returns live PMC PostgreSQL information_schema definitions and sampled distinct column values."""
    return get_live_db_schema_resource()

# Register Tools
@mcp_server.tool()
def execute_sql(sql_query: str) -> dict:
    """
    Executes a read-only PostgreSQL SELECT query against the PMC Grievance Database.
    Automatically enforces LIMIT 50 and 8-second statement timeout safety controls.
    """
    return execute_sql_query(sql_query)

@mcp_server.tool()
def sample_values(table_name: str, column_name: str, limit: int = 20) -> list:
    """
    Samples distinct non-null values for any PostgreSQL column (e.g. ward_name, user_type, status_name).
    Use this tool to inspect real values before filtering queries.
    """
    return sample_column_values(table_name, column_name, limit)

@mcp_server.tool()
def inspect_columns(table_name: str) -> list:
    """
    Returns column names and data types for any PostgreSQL table in the PMC database.
    """
    return inspect_table_columns(table_name)


if __name__ == "__main__":
    logger.info("Starting PMC FastMCP Server on stdio transport...")
    mcp_server.run()
