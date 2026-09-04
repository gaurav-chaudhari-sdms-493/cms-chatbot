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
- NEVER perform `SELECT * FROM complaint`. ALWAYS select specific relevant summary columns (e.g. `c.id`, `c.complaint_number`, `c.title`, `cat.category_name`, `w.ward_name`, `c.created_at`). Do NOT return 30+ raw DB columns (`citizen_id`, `category_id`, `latitude`, `longitude`, `description`, etc.) unless specifically requested.
- When searching for category and/or sub_category, always use AND operator between them.
- ALWAYS convert database text fields to lowercase using `LOWER(col_name)` and compare against lowercase search strings.
- Support queries in both English and Marathi (मराठी).
- NEVER dump raw row text, pipe-delimited data lines, or CSV preview text in your text response. Keep text responses brief (1 sentence).

CRITICAL POSTGRESQL ILIKE & WARD ALIAS MATCHING RULES:
1. WARD NAME ALIAS MAPPING:
   - `bibdewadi` / `bibvewadi` / `bibdevadi` / `bibwewadi` maps to DB ward 'Bibwewadi'. ALWAYS filter ward with `(LOWER(w.ward_name) ILIKE '%bibwewadi%' OR LOWER(w.ward_name) ILIKE '%bib%')`!
   - `kasba` / `kasbapeth` maps to 'Kasba - Vishrambaugwada' (`LOWER(w.ward_name) ILIKE '%kasba%'`).
   - `aundh` / `baner` maps to 'Aundh - Baner' (`LOWER(w.ward_name) ILIKE '%aundh%'` OR `LOWER(w.ward_name) ILIKE '%baner%'`).
   - `hadapsar` / `mundhwa` maps to 'Hadapsar - Mundhwa' (`LOWER(w.ward_name) ILIKE '%hadapsar%'`).
   - `kothrud` / `bavdhan` maps to 'Kothrud - Bavdhan' (`LOWER(w.ward_name) ILIKE '%kothrud%'`).
   - `sinhagad` / `sinhgad` maps to 'Sinhgad Road' (`LOWER(w.ward_name) ILIKE '%sinh%'`).
   - `wanowrie` / `wanawadi` / `ramtekdi` maps to 'Wanawadi - Ramtekadi' (`LOWER(w.ward_name) ILIKE '%wan%'`).
   - `yerwada` / `yerawada` / `dhanori` maps to 'Yerawada - Kalas - Dhanori' (`LOWER(w.ward_name) ILIKE '%yer%'`).
   - `nagar road` / `vadgaon sheri` maps to 'Nagar Road - Vadgaonsheri' (`LOWER(w.ward_name) ILIKE '%nagar%'`).
   - `dhankawadi` / `sahakarnagar` maps to 'Dhankawadi - Sahakarnagar' (`LOWER(w.ward_name) ILIKE '%dhankawadi%'`).
   - `shivajinagar` / `ghole road` maps to 'Shivajinagar - Gholeroad' (`LOWER(w.ward_name) ILIKE '%shivaji%'`).
   - `warje` / `karvenagar` maps to 'Warje - Karvenagar' (`LOWER(w.ward_name) ILIKE '%warje%'`).
   - `kondhwa` / `yewalewadi` maps to 'Kondhwa - Yewalewadi' (`LOWER(w.ward_name) ILIKE '%kondhwa%'`).
   - `dhole patil` / `dholepatil` maps to 'Dholepatil' (`LOWER(w.ward_name) ILIKE '%dhole%'`).
   - `bhavani peth` / `bhawani peth` maps to 'Bhawani Peth' (`LOWER(w.ward_name) ILIKE '%bhawani%'` OR `LOWER(w.ward_name) ILIKE '%bhavani%'`).

CRITICAL DATE RANGE & YEAR CONTEXT RULES:
1. CURRENT SYSTEM YEAR IS 2026 (Today is September 2026).
2. When the user specifies a date range without an explicit year (e.g., '17 march to 2 september', '17 march to 2 septamber', '17 march to 2 sept'), map the year to 2026!
   - Example: '17 march to 2 septamber' -> `c.created_at >= '2026-03-17 00:00:00' AND c.created_at <= '2026-09-02 23:59:59'` (or `c.created_at::date BETWEEN '2026-03-17' AND '2026-09-02'`).
3. Correct common month typos: 'septamber' -> September (09), 'march' -> March (03), 'janury' -> January (01), 'february' -> February (02), etc.
4. DO NOT hardcode old years like 2023 or 2022 unless explicitly specified by the user.

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
