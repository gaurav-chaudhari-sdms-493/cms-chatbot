import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(dotenv_path=root_env)
backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(backend_env):
    load_dotenv(dotenv_path=backend_env)

# Ensure vanna package is importable from workspace root
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VANNA_SRC = os.path.join(WORKSPACE_DIR, "vanna", "src")
if VANNA_SRC not in sys.path:
    sys.path.insert(0, VANNA_SRC)

from vanna import Agent
from vanna.core.system_prompt import SystemPromptBuilder
from vanna.core.tool.models import ToolSchema
from vanna.core.user.models import User as CoreUser
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool,
)
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.postgres import PostgresRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from app.db.dynamic_schema import fetch_live_database_schema

# 1. Configure OpenRouter LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is missing or not set in .env file.")

OPENROUTER_MODEL = (
    os.getenv("OPENROUTER_MODEL")
    or os.getenv("OPENROUTER_DEFAULT_MODEL")
    or "meta-llama/llama-3.3-70b-instruct"
)

llm = OpenAILlmService(
    model=OPENROUTER_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# 2. Configure Database Connection
RAW_DATABASE_URL = os.getenv("DATABASE_URL")
if not RAW_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing or not set in .env file.")

DATABASE_URL = RAW_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

db_tool = RunSqlTool(
    sql_runner=PostgresRunner(connection_string=DATABASE_URL)
)

# 3. Dynamic System Prompt Builder with PostgreSQL Schema Context
class PmcSchemaSystemPromptBuilder(SystemPromptBuilder):
    """Provides exact live PostgreSQL table schema and context to the LLM."""

    async def build_system_prompt(
        self, user: CoreUser, tools: List[ToolSchema]
    ) -> Optional[str]:
        live_schema = fetch_live_database_schema()
        return f"""
You are an expert SQL Assistant for Pune Municipal Corporation (PMC) CMS Database (PostgreSQL).
Always use the `run_sql` tool to execute valid PostgreSQL SQL queries. DO NOT guess non-existent table names like 'employees'.

=== DATABASE SCHEMA ===
{live_schema}

=== MANDATORY BUSINESS RULES ===
- NEVER search using `complaint.title` or `complaint.description`. Always search standard master table values (`category_master.category_name` or `sub_category_master.sub_category_name`).
- When searching for category and/or sub_category, always use AND operator between them.
- Support queries in both English and Marathi (मराठी).

CRITICAL POSTGRESQL ILIKE PATTERN MATCHING RULES:
1. ALWAYS use `ILIKE '%keyword%'` with `%` wildcards when filtering by ward names (`ward_master.ward_name`), department names (`department_master.department_name`), category names (`category_master.category_name`), or sub-category names (`sub_category_master.sub_category_name`).
   - DO NOT use exact equality `=` for names! E.g., ward names in DB are compound like 'Aundh - Baner', so `ward_name = 'Baner'` returns 0. ALWAYS use `w.ward_name ILIKE '%Baner%'`!
   - E.g., category name for road is 'Roads & Traffic Infrastructure', so `category_name = 'Road'` returns 0. ALWAYS use `cat.category_name ILIKE '%Road%'`!
2. JOIN `complaint` table with `ward_master` (`c.ward_id = w.id`) and `category_master` (`c.category_id = cat.id`) when computing location & category totals.
"""


# 4. Configure Agent Memory
agent_memory = DemoAgentMemory(max_items=1000)

# 5. Configure User Resolver
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie("vanna_email") or "admin@example.com"
        group = "admin" if user_email == "admin@example.com" else "user"
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# 6. Register Tools
tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=["admin", "user"])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=["admin"])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=["admin", "user"])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=["admin", "user"])
tools.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])

# 7. Create Global Agent Instance
vanna_agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    system_prompt_builder=PmcSchemaSystemPromptBuilder(),
)
