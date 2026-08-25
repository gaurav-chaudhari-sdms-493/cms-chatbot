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

DB_SCHEMA_CONTEXT = """
You are an expert PostgreSQL Data Analyst AI for the Pune Municipal Corporation (PMC) Grievance & Officer Query System.
Your job is to generate accurate, optimal PostgreSQL SELECT queries to answer officer questions.

DATABASE SCHEMA:
1. `complaint`: Main complaint table
   - id (INT, Primary Key)
   - complaint_no (VARCHAR)
   - created_at (TIMESTAMP)
   - closed_at (TIMESTAMP, NULL if pending/open)
   - department_id (INT, FK -> department_master.id)
   - ward_id (INT, FK -> ward_master.id)
   - prabhag_id (INT, FK -> prabhag_master.id)
   - category_id (INT, FK -> category_master.id)
   - status_id (INT, FK -> status_master.id)
   - assigned_to_id (INT, FK -> user_master.id)
   - location_address (TEXT)
   - description (TEXT)
   - citizen_feedback_rating (INT)

2. `department_master`:
   - id (INT, PK)
   - department_name (VARCHAR, e.g. 'Drainage', 'Road', 'Water Supply', 'Health', 'Solid Waste Management', 'Electricity')
   - department_name_mar (VARCHAR, Marathi name e.g. 'मलनिःसारण', 'पथ विभाग')
   - department_code (VARCHAR)

3. `ward_master`:
   - id (INT, PK)
   - ward_name (VARCHAR, e.g. 'Aundh - Baner', 'Kothrud - Bawdhan', 'Bibwewadi', 'Hadapsar', 'Kasba - Vishrambaugwada')
   - ward_name_mar (VARCHAR)
   - ward_code (VARCHAR)
   - ward_number (INT)

4. `prabhag_master`:
   - id (INT, PK)
   - prabhag_name (VARCHAR, e.g. '9 Baner - Balewadi - Pashan', 'Sus - Baner - Pashan')
   - ward_id (INT)

5. `status_master`:
   - id (INT, PK)
   - status_name (VARCHAR: 'Registered', 'Assigned', 'Resolved', 'Closed - Not Valid', 'Closed', 'Pending Info', 'Transferred', 'Reopened', 'Escalated')
   - status_name_mar (VARCHAR)

6. `category_master`:
   - id (INT, PK)
   - category_name (VARCHAR)
   - category_name_mar (VARCHAR)
   - department_id (INT)
   - default_sla_days (INT)

7. `user_master`:
   - id (INT, PK)
   - full_name (VARCHAR, e.g. 'SUSHIL CHANDRAKANT MOHITE', 'Dept Drainage L1 Officer')
   - full_name_mar (VARCHAR)
   - employee_code (VARCHAR)
   - designation (VARCHAR)
   - user_type (VARCHAR: 'DEPT_L1', 'DEPT_L2', 'DEPT_L3', 'HOD', 'RECEPTION', 'CITIZEN')
   - department_id (INT)
   - ward_id (INT)

8. `vw_dd_late_complaints`: View of complaints that breached SLA
   - id (INT)
   - complaint_no (VARCHAR)
   - department_id (INT)
   - ward_id (INT)
   - assigned_to_id (INT)
   - created_at (TIMESTAMP)

IMPORTANT GUIDELINES:
- Output ONLY valid PostgreSQL SELECT queries enclosed within ```sql ... ``` code blocks during query generation.
- Never use non-SELECT statements (no INSERT, UPDATE, DELETE, DROP, ALTER).
- When searching names/locations, use case-insensitive ILIKE pattern matching e.g. `u.full_name ILIKE '%MOHITE%'` or `w.ward_name ILIKE '%baner%'`.
- "Pending" complaints are defined as `closed_at IS NULL AND status_id NOT IN (3, 4)` (where status 3 is Resolved and 4 is Closed - Not Valid) OR `closed_at IS NULL`.
- Always aggregate data (`COUNT(*)`, `AVG()`, `GROUP BY`) when answering summary/count questions.
"""

def extract_sql_from_response(text: str) -> Optional[str]:
    match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback search for SELECT statements
    select_match = re.search(r"(SELECT\s+.*?;)", text, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()
    return None

def execute_sql_query(sql: str) -> tuple[List[str], List[dict]]:
    SQLSafetyValidator.validate_sql(sql)
    
    with sync_pmc_engine.connect() as conn:
        # Enforce 30s statement timeout
        conn.execute(text("SET statement_timeout = 30000;"))
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchmany(20000)]
        return columns, rows

from app.api.llm_client import call_gemini_with_key_rotation

@router.post("/agent", response_model=AgentQueryResponse)
def execute_agent_query(req: AgentQueryRequest):
    start_time = time.time()
    
    conversation_history = [
        {"role": "user", "parts": [f"{DB_SCHEMA_CONTEXT}\n\nOfficer Question: {req.question}\n\nGenerate the PostgreSQL SQL query enclosed in ```sql ... ``` to retrieve the necessary data for this question."]}
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
You are the PMC Officer Query Assistant. Format a clear, detailed, executive-ready Markdown report to answer the officer's question based on the verified database output.

Officer Question: {req.question}
SQL Executed:
```sql
{sql_used}
```

Database Output (Columns: {columns}):
{rows[:100]} (Total Rows Returned: {len(rows)})

FORMATTING RULES:
1. Provide a clear Header (# Title) and Executive Summary.
2. Use GitHub-style markdown tables for data presentation.
3. Highlight key statistics in blockquotes or badges.
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

