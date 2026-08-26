import os
import re
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from google import genai
from dotenv import load_dotenv

from app.db.session import sync_pmc_engine
from app.execution.validator import SQLSafetyValidator, SQLValidationError
from app.mcp.tools import execute_sql_query as mcp_execute_sql_query

load_dotenv()


logger = logging.getLogger("pmc_chatbot.agent")

router = APIRouter(prefix="/query", tags=["Agent Query"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class AgentQueryRequest(BaseModel):
    question: str = Field(..., description="Open-ended natural language question from the officer")
    max_retries: Optional[int] = Field(3, ge=1, le=5, description="Maximum self-correction attempts")

class AgentQueryResponse(BaseModel):
    question: str
    markdown_report: str
    sql_used: str
    execution_time_ms: float
    retry_count: int
    status: str

from app.db.dynamic_schema import fetch_live_database_schema

# Continuous Dynamic Schema Alteration Inspector (Refreshes live from PostgreSQL information_schema)
def get_db_schema_context() -> str:
    return fetch_live_database_schema()

# Backward compatibility alias
DB_SCHEMA_CONTEXT = property(lambda self: fetch_live_database_schema())


def extract_sql_from_response(text: str) -> Optional[str]:
    match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback search for SELECT statements
    select_match = re.search(r"(SELECT\s+.*?;)", text, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()
    return None

def execute_sql_query(sql_query: str):
    res = mcp_execute_sql_query(sql_query)
    if res["status"] == "ERROR":
        raise SQLValidationError(res["error"])
    return res["columns"], res["rows"]


from app.db.dynamic_schema import fetch_live_database_schema
from app.api.llm_client import call_gemini_with_key_rotation

@router.post("/agent", response_model=AgentQueryResponse)
def execute_agent_query(req: AgentQueryRequest):
    start_time = time.time()
    
    live_schema_context = fetch_live_database_schema()
    
    conversation_history = [
        {"role": "user", "parts": [f"{live_schema_context}\n\nOfficer Question: {req.question}\n\nGenerate the PostgreSQL SQL query enclosed in ```sql ... ``` to retrieve the necessary data for this question."]}
    ]


    sql_used = ""
    columns = []
    rows = []
    retry_count = 0
    execution_success = False
    last_error_msg = ""
    is_quota_error = False

    for attempt in range(1, req.max_retries + 1):
        try:
            prompt_str = "\n".join([p["parts"][0] for p in conversation_history])
            raw_text, _ = call_gemini_with_key_rotation(prompt_str)
            
            extracted_sql = extract_sql_from_response(raw_text)
            if not extracted_sql:
                raise ValueError("Could not find a valid SQL block in the response.")

            sql_used = extracted_sql
            logger.info(f"Attempt {attempt}: Executing SQL:\n{sql_used}")

            # Execute SQL
            columns, rows = execute_sql_query(sql_used)
            execution_success = True
            retry_count = attempt - 1
            break

        except (SQLValidationError, Exception) as err:
            last_error_msg = str(err)
            if "429" in last_error_msg or "RESOURCE_EXHAUSTED" in last_error_msg:
                is_quota_error = True
            logger.warning(f"Attempt {attempt} failed with error: {last_error_msg}")
            
            # Feed error back for self-correction
            conversation_history.append({
                "role": "user",
                "parts": [
                    f"Your SQL query execution failed with the following error:\n```\n{last_error_msg}\n```\n"
                    f"Please correct the table/column names or SQL syntax based on the schema and generate the revised SQL query inside ```sql ... ```."
                ]
            })

    execution_time_ms = round((time.time() - start_time) * 1000, 2)

    # Synthesis Stage: Generate formatted Markdown Report
    if execution_success:
        synthesis_prompt = f"""
You are the PMC Grievance Intelligence AI Assistant for Pune Municipal Corporation.
Format a beautiful, highly polished, executive-ready Markdown report card to answer the officer's question based on the verified database output.

Officer Question: {req.question}
SQL Executed:
```sql
{sql_used}
```

Database Output (Columns: {columns}):
{rows[:100]} (Total Rows Returned: {len(rows)})

CRITICAL EXECUTIVE FORMATTING RULES:
1. Provide a clean Header (# Title) and Executive Summary section.
2. ALL TABLES MUST BE STRICTLY FORMATTED AS GITHUB-FLAVORED MARKDOWN TABLES WITH PIPES '|' AND HEADER DIVIDER BARS '| --- | --- |'.
   Example Table Syntax:
   | Status Name | Complaint Count | Percentage (%) |
   | :--- | :---: | :---: |
   | ✅ Resolved | **21,736** | **78.9%** |
   | ❌ Closed - Not Valid | **4,557** | **16.5%** |

3. Format all numbers with commas (e.g. `21,736` instead of `21736`, `4,557` instead of `4557`).
4. Highlight key totals, summary metrics, and insights in blockquotes `>` or bold badges (e.g. **`21,736`**).
5. Include relevant emoji indicators (📊, 🟢, 🔴, 🏆, 🏛️, 🛣️, 🦟, 🚰, 💡) to make the report visually engaging and executive-ready.
"""

        try:
            markdown_report, _ = call_gemini_with_key_rotation(synthesis_prompt)
        except Exception:
            markdown_report = f"# Query Analysis Report\n\n**Question:** {req.question}\n\n**Total Records Found:** {len(rows)}\n"

        return AgentQueryResponse(
            question=req.question,
            markdown_report=markdown_report,
            sql_used=sql_used,
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
            status="SUCCESS"
        )

    else:
        if is_quota_error or "429" in last_error_msg or "RESOURCE_EXHAUSTED" in last_error_msg:
            fallback_report = (
                "# ⚠️ Gemini AI Rate Limit Reached (429 Quota Exceeded)\n\n"
                "The Gemini API rate limit / free tier daily quota has been temporarily reached.\n\n"
                "> 💡 **Recommended Quick Action:**\n"
                "> Switch to **⚡ Structural Template Mode** at the top of the screen for **instant 10ms query execution** backed by PMC database indexes.\n\n"
                "```text\nError Details: 429 RESOURCE_EXHAUSTED - API Rate Limit\n```"
            )
        else:
            fallback_report = f"""# ⚠️ Query Resolution Notice

The AI Data Agent was unable to resolve the database query after {req.max_retries} verification attempts.

### Last Execution Error:
```text
{last_error_msg}
```

### Suggestions for Officer:
1. Rephrase your question with specific terms (e.g. *"Show complaints in Aundh ward for July 2026"*).
2. Switch to **⚡ Structural Template Mode** for canonical queries.
"""
        return AgentQueryResponse(
            question=req.question,
            markdown_report=fallback_report,
            sql_used=sql_used or "-- No valid SQL generated",
            execution_time_ms=execution_time_ms,
            retry_count=req.max_retries,
            status="FAILED"
        )

