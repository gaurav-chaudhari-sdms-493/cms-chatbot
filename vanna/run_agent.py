#!/usr/bin/env python3
"""
Live Vanna 2.0 Agent server configured with OpenRouter LLM and PostgreSQL database.
Configured with Database Schema Prompt Builder for accurate Text-to-SQL generation.
"""

import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(dotenv_path=root_env)
backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
if os.path.exists(backend_env):
    load_dotenv(dotenv_path=backend_env)

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
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.postgres import PostgresRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory

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

# Convert postgresql+asyncpg:// to postgresql:// for psycopg2 compatibility
DATABASE_URL = RAW_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

db_tool = RunSqlTool(
    sql_runner=PostgresRunner(connection_string=DATABASE_URL)
)

# 3. Custom System Prompt Builder with PostgreSQL Schema Context
class PmcSchemaSystemPromptBuilder(SystemPromptBuilder):
    """Provides exact PostgreSQL table schema and context to the LLM."""

    async def build_system_prompt(
        self, user: CoreUser, tools: List[ToolSchema]
    ) -> Optional[str]:
        return """
You are an expert SQL Assistant for Pune Municipal Corporation (PMC) CMS Database (PostgreSQL).
Always use the `run_sql` tool to execute valid PostgreSQL SQL queries. DO NOT guess non-existent table names like 'employees'.

=== DATABASE SCHEMA ===
1. Table `department_master`:
   - Columns: id, department_code, department_name, department_name_mar, hod_user_id, contact_email, contact_phone

2. Table `user_master`:
   - Columns: id, user_type, full_name, full_name_mar, mobile, email, designation, department_id, ward_id, zone_id, prabhag_id

3. Table `role_master`:
   - Columns: id, role_code, role_name (e.g. 'HOD', 'Head of Department')

4. Table `user_role_mapping`:
   - Columns: id, user_id, role_id

5. Table `complaint`:
   - Columns: id, complaint_number, citizen_id, category_id, sub_category_id, title, description, status_id, priority, prabhag_id, created_at

6. Table `category_master`:
   - Columns: id, category_code, category_name, default_department_id

7. Table `status_master`:
   - Columns: id, status_code, status_name (e.g. 'Registered', 'Assigned', 'Resolved', 'Closed - Not Valid'), status_group (OPEN, IN_PROGRESS, PENDING, CLOSED)

8. Table `prabhag_master`:
   - Columns: id, prabhag_name, ward_id

9. Table `sub_category_master`:
   - Columns: id, category_id, sub_category_name, sub_category_name_mar

=== MANDATORY BUSINESS RULES ===
- NEVER search using `complaint.title` or `complaint.description`. Always search standard master table values (`category_master.category_name` or `sub_category_master.sub_category_name`).
- When searching for category and/or sub_category, always use AND operator between them.
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

# 7. Create Agent Instance with System Prompt Builder
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    system_prompt_builder=PmcSchemaSystemPromptBuilder(),
)

# 8. Start FastAPI Server
if __name__ == "__main__":
    print(f"Starting Vanna 2.0 Agent with Schema Context...")
    print(f" - LLM Provider: OpenRouter ({OPENROUTER_MODEL})")
    print(f" - Database: PostgreSQL (pmc_cms_new1 @ 115.160.211.220:2419)")
    print(f" - Server URL: http://localhost:8000")
    
    server_config = {
        "dev_mode": True,
        "static_folder": os.path.join(os.path.dirname(__file__), "frontends/webcomponent/dist"),
    }
    server = VannaFastAPIServer(agent=agent, config=server_config)
    server.run(host="0.0.0.0", port=8000)
