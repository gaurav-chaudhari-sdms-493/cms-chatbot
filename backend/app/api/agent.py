import os
import re
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
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
from app.db.session import get_metadata_db
from app.agents import MasterOrchestratorAgent

@router.post("/agent", response_model=AgentQueryResponse)
def execute_agent_query(req: AgentQueryRequest, db: Session = Depends(get_metadata_db)):
    res = MasterOrchestratorAgent.process_query(
        query_text=req.question,
        metadata_session=db,
        max_retries=req.max_retries or 3
    )

    return AgentQueryResponse(
        question=req.question,
        markdown_report=res.get("content", ""),
        sql_used=res.get("sql_used") or "-- No SQL used",
        execution_time_ms=res.get("execution_time_ms", 0.0),
        retry_count=res.get("retry_count", 0),
        status="SUCCESS" if res.get("status") in ["SUCCESS", "REFUSED", "FOLLOW_UP"] else "FAILED"
    )


