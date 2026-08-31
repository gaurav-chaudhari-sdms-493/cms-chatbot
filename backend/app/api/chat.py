import os
import uuid
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
import requests
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
    template_id: Optional[str] = None
    candidate_templates: Optional[List[Dict[str, Any]]] = None
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
                template_id=getattr(m, 'template_id', None),
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

    
    from app.api.llm_client import execute_fastmcp_agent_loop
    
    start_time = time.time()
    execution_time_ms = 0.0
    sql_used = ""
    template_id = None
    candidate_templates = None
    columns = []
    rows = []
    retry_count = 0
    execution_success = False
    last_error = ""
    markdown_report = ""

    # 1. Try Scope-based Template Engine (Categories A-P & Out-of-Scope Detection)
    from app.execution.scope_engine import ScopeAnswerEngine
    from app.db.session import sync_pmc_engine
    from sqlalchemy.orm import sessionmaker

    PMC_SessionMaker = sessionmaker(bind=sync_pmc_engine)
    pmc_session = PMC_SessionMaker()

    try:
        history_dicts = [{"sender": m.sender, "content": m.content} for m in history_msgs]
        scope_res = ScopeAnswerEngine.answer_scope_query(
            query_text=payload.content,
            metadata_session=db,
            pmc_session=pmc_session,
            session_history=history_dicts
        )
        if scope_res:
            markdown_report = scope_res["content"]
            sql_used = scope_res.get("sql_used") or ""
            template_id = scope_res.get("template_id") or None
            candidate_templates = scope_res.get("candidate_templates") or None
            execution_success = True
            logger.info(f"Successfully answered query via Scope Template Engine (Template: {template_id})")
    except Exception as scope_err:
        logger.warning(f"Scope Answer Engine attempt encountered error: {scope_err}")
    finally:
        pmc_session.close()

    # 2. Try n8n AI Agent Webhook if not answered by Scope Engine
    if not markdown_report:
        n8n_urls = [
            "http://localhost:5678/webhook/pmc-chat-agent-webhook",
            "http://localhost:5678/webhook-test/pmc-chat-agent-webhook"
        ]
        
        n8n_success = False

        for url in n8n_urls:
            try:
                n8n_resp = requests.post(url, json={
                    "chatInput": payload.content,
                    "sessionId": session.id
                }, timeout=45)
                if n8n_resp.status_code == 200:
                    n8n_data = n8n_resp.json()
                    if isinstance(n8n_data, list) and len(n8n_data) > 0:
                        n8n_data = n8n_data[0]
                    
                    markdown_report = n8n_data.get("output") or n8n_data.get("text") or n8n_data.get("markdown_report") or ""
                    sql_used = n8n_data.get("sql_used") or ""
                    if markdown_report.strip():
                        n8n_success = True
                        execution_success = True
                        logger.info("Successfully received report card from n8n AI Agent Workflow.")
                        break
            except Exception as n8n_err:
                logger.warning(f"n8n webhook attempt failed on '{url}': {n8n_err}")

    # 3. Fallback to native FastMCP Agent loop if n8n and Scope Engine are not active
    if not markdown_report:
        history_str = "\n".join(prompt_context[1:])
        try:
            sql_used, columns, rows, steps_taken = execute_fastmcp_agent_loop(
                live_schema_context, 
                payload.content, 
                max_steps=5, 
                history_context=history_str
            )
            if sql_used and len(rows) > 0:
                execution_success = True
                retry_count = steps_taken - 1
        except Exception as e:
            logger.error(f"FastMCP Agent Execution Error: {e}")
            last_error = str(e)

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        if execution_success and not markdown_report:
            synthesis_prompt = f"""
You are the PMC Grievance Intelligence AI Assistant for Pune Municipal Corporation.
Format a beautiful, highly polished, executive-ready Markdown report card to answer the officer's question based on the verified database output and conversation history.

Officer Question: {payload.content}
SQL Executed:
```sql
{sql_used}
```

Database Output (Columns: {columns}):
{rows[:100]} (Total Rows Returned: {len(rows)})

CRITICAL EXECUTIVE FORMATTING RULES:
1. Provide a clean Header (# Title) and Executive Summary section.
2. ALL TABLES MUST BE STRICTLY FORMATTED AS GITHUB-FLAVORED MARKDOWN TABLES WITH PIPES '|' AND HEADER DIVIDER BARS '| --- | --- |'.
3. Format all numbers with commas (e.g. `21,736` instead of `21736`, `4,557` instead of `4557`).
4. Highlight key totals, summary metrics, and insights in blockquotes `>` or bold badges (e.g. **`21,736`**).
5. Include relevant emoji indicators to make the report visually engaging and executive-ready.
"""
            try:
                markdown_report, _ = call_gemini_with_key_rotation(synthesis_prompt)
            except Exception:
                markdown_report = f"# Analytics Results\n\n**Total Records:** {len(rows)}\n\n```json\n{rows[:20]}\n```"
        elif not markdown_report:
            markdown_report = f"# ⚠️ Query Resolution Notice\n\nThe AI Agent was unable to resolve the query.\n\n```text\n{last_error}\n```"




    # Save Agent message to DB
    execution_time_ms = round((time.time() - start_time) * 1000, 2)
    agent_msg = ChatMessage(
        session_id=session.id,
        sender="agent",
        content=markdown_report,
        sql_used=sql_used,
        template_id=template_id,
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
            template_id=agent_msg.template_id,
            candidate_templates=candidate_templates,
            execution_time_ms=agent_msg.execution_time_ms,
            created_at=agent_msg.created_at.isoformat()
        ),
        "sql_used": sql_used,
        "template_id": template_id,
        "candidate_templates": candidate_templates,
        "execution_time_ms": execution_time_ms,
        "retry_count": retry_count,
        "status": "SUCCESS" if execution_success else "FAILED"
    }
