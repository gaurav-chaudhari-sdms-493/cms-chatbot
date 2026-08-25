import os
import uuid
import time
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
from dotenv import load_dotenv

from app.db.session import get_metadata_db, sync_pmc_engine
from app.db.models import ChatSession, ChatMessage
from app.db.dynamic_schema import fetch_live_database_schema
from app.execution.validator import SQLSafetyValidator, SQLValidationError
from app.api.agent import extract_sql_from_response, execute_sql_query, DB_SCHEMA_CONTEXT

load_dotenv()

logger = logging.getLogger("pmc_chatbot.chat")

router = APIRouter(prefix="/chat", tags=["Chat History & Multi-Chat"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
    mode: Optional[str] = "agent"

class ChatMessageRequest(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    content: str
    sql_used: Optional[str] = None
    execution_time_ms: Optional[float] = None
    created_at: str

class ChatSessionDetailResponse(BaseModel):
    id: str
    title: str
    mode: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageResponse]

@router.get("/sessions", response_model=List[ChatSessionDetailResponse])
def get_chat_sessions(db: Session = Depends(get_metadata_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    res = []
    for s in sessions:
        msgs = [
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                sender=m.sender,
                content=m.content,
                sql_used=m.sql_used,
                execution_time_ms=m.execution_time_ms,
                created_at=m.created_at.isoformat()
            )
            for m in s.messages
        ]
        res.append(ChatSessionDetailResponse(
            id=s.id,
            title=s.title,
            mode=s.mode,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            messages=msgs
        ))
    return res

@router.post("/sessions", response_model=ChatSessionDetailResponse)
def create_chat_session(payload: ChatSessionCreate, db: Session = Depends(get_metadata_db)):
    session_id = f"chat_{uuid.uuid4().hex[:12]}"
    session = ChatSession(
        id=session_id,
        title=payload.title or "New Chat",
        mode=payload.mode or "agent"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ChatSessionDetailResponse(
        id=session.id,
        title=session.title,
        mode=session.mode,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        messages=[]
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_chat_session_by_id(session_id: str, db: Session = Depends(get_metadata_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    msgs = [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            sender=m.sender,
            content=m.content,
            sql_used=m.sql_used,
            execution_time_ms=m.execution_time_ms,
            created_at=m.created_at.isoformat()
        )
        for m in session.messages
    ]
    return ChatSessionDetailResponse(
        id=session.id,
        title=session.title,
        mode=session.mode,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        messages=msgs
    )

@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_metadata_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    db.delete(session)
    db.commit()
    return {"status": "SUCCESS", "message": f"Chat session '{session_id}' deleted."}

from app.api.llm_client import call_gemini_with_key_rotation

@router.post("/sessions/{session_id}/message")
def post_chat_message(session_id: str, payload: ChatMessageRequest, db: Session = Depends(get_metadata_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Save User message to DB
    user_msg = ChatMessage(
        session_id=session.id,
        sender="user",
        content=payload.content
    )
    db.add(user_msg)
    
    # Auto-title session if still "New Chat"
    if session.title == "New Chat" or not session.title:
        session.title = payload.content[:40] + ("..." if len(payload.content) > 40 else "")
    
    db.commit()

    # Build multi-turn conversation context for Gemini with LIVE DYNAMIC SCHEMA
    history_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
    live_schema_context = fetch_live_database_schema()
    prompt_context = [live_schema_context, "\n--- CONVERSATION HISTORY ---"]
    for m in history_msgs[:-1]:  # previous turns
        prompt_context.append(f"{'Officer' if m.sender == 'user' else 'Assistant'}: {m.content}")
        if m.sql_used:
            prompt_context.append(f"SQL Used: {m.sql_used}")

    
    prompt_context.append(f"\nOfficer (Current Question): {payload.content}\n\nGenerate the PostgreSQL SQL query enclosed in ```sql ... ``` to retrieve data for this question.")


    start_time = time.time()
    sql_used = ""
    columns = []
    rows = []
    retry_count = 0
    execution_success = False
    last_error = ""
    is_quota_error = False

    # Self-Correction ReAct Loop (Up to 3 retries)
    for attempt in range(1, 4):
        try:
            raw_text, _ = call_gemini_with_key_rotation("\n".join(prompt_context))
            extracted_sql = extract_sql_from_response(raw_text)
            if not extracted_sql:
                raise ValueError("Could not find a valid SQL block in response.")
            
            sql_used = extracted_sql
            columns, rows = execute_sql_query(sql_used)
            execution_success = True
            retry_count = attempt - 1
            break
        except Exception as err:
            last_error = str(err)
            if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                is_quota_error = True
            prompt_context.append(f"\nSQL execution attempt {attempt} failed: {last_error}. Please correct table/column names and regenerate ```sql ... ```.")

    execution_time_ms = round((time.time() - start_time) * 1000, 2)

    # Synthesis Stage
    if execution_success:
        synthesis_prompt = f"""
You are the PMC Officer Query Assistant. Format a clear, detailed, executive-ready Markdown report to answer the officer's question based on the verified database output and conversation history.

Officer Question: {payload.content}
SQL Executed:
```sql
{sql_used}
```

Database Output (Columns: {columns}):
{rows[:100]} (Total Rows Returned: {len(rows)})

FORMATTING RULES:
1. Provide a clear Header (# Title) and Executive Summary.
2. Use GitHub-style markdown tables for data presentation.
3. Highlight key statistics.
"""
        try:
            markdown_report, _ = call_gemini_with_key_rotation(synthesis_prompt)
        except Exception:
            markdown_report = f"# Analytics Results\n\n**Total Records:** {len(rows)}\n\n```json\n{rows[:20]}\n```"
    else:
        if is_quota_error or "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
            markdown_report = (
                "# ⚠️ Gemini AI Rate Limit Reached (429 Quota Exceeded)\n\n"
                "The Gemini API rate limit / free tier daily quota has been temporarily reached.\n\n"
                "> 💡 **Recommended Quick Action:**\n"
                "> Switch to **⚡ Structural Template Mode** at the top of the screen for **instant 10ms query execution** backed by PMC database indexes.\n\n"
                "```text\nError Details: 429 RESOURCE_EXHAUSTED - API Rate Limit\n```"
            )
        else:
            markdown_report = f"# ⚠️ Query Resolution Notice\n\nThe AI Agent was unable to resolve the query after 3 verification attempts.\n\n```text\n{last_error}\n```"



    # Save Agent message to DB
    agent_msg = ChatMessage(
        session_id=session.id,
        sender="agent",
        content=markdown_report,
        sql_used=sql_used,
        execution_time_ms=execution_time_ms
    )
    db.add(agent_msg)
    db.commit()

    return {
        "user_message": ChatMessageResponse(
            id=user_msg.id,
            session_id=user_msg.session_id,
            sender=user_msg.sender,
            content=user_msg.content,
            created_at=user_msg.created_at.isoformat()
        ),
        "agent_message": ChatMessageResponse(
            id=agent_msg.id,
            session_id=agent_msg.session_id,
            sender=agent_msg.sender,
            content=agent_msg.content,
            sql_used=agent_msg.sql_used,
            execution_time_ms=agent_msg.execution_time_ms,
            created_at=agent_msg.created_at.isoformat()
        ),
        "sql_used": sql_used,
        "execution_time_ms": execution_time_ms,
        "retry_count": retry_count,
        "status": "SUCCESS" if execution_success else "FAILED"
    }
