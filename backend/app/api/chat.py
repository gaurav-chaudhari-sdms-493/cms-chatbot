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



@router.post("/sessions/{session_id}/message")
async def post_chat_message(session_id: str, payload: ChatMessageRequest, db: Session = Depends(get_metadata_db)):

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

    # Build multi-turn conversation context for LLM with LIVE DYNAMIC SCHEMA
    history_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
    live_schema_context = fetch_live_database_schema()
    prompt_context = [live_schema_context, "\n--- CONVERSATION HISTORY ---"]
    for m in history_msgs[:-1]:  # previous turns
        prompt_context.append(f"{'Officer' if m.sender == 'user' else 'Assistant'}: {m.content}")
        if m.sql_used:
            prompt_context.append(f"SQL Used: {m.sql_used}")

    
    # Process turn using Vanna AI 2.0 Agent (with MasterOrchestratorAgent fallback)
    from app.agents import MasterOrchestratorAgent

    history_dicts = [
        {"sender": m.sender, "content": m.content, "sql_used": getattr(m, 'sql_used', None)}
        for m in history_msgs[:-1]
    ]

    agent_res = None
    try:
        from app.vanna_agent import vanna_agent
        from vanna.servers.base import ChatHandler, ChatRequest
        
        chat_handler = ChatHandler(vanna_agent)
        vanna_req = ChatRequest(message=payload.content, conversation_id=session.id)
        
        start_time = time.time()
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            vanna_resp = await chat_handler.handle_poll(vanna_req)
        else:
            vanna_resp = loop.run_until_complete(chat_handler.handle_poll(vanna_req))
            
        exec_ms = round((time.time() - start_time) * 1000, 2)

        def get_field(obj, field, default=None):
            if isinstance(obj, dict):
                return obj.get(field, default)
            return getattr(obj, field, default)

        markdown_report = ""
        sql_used = ""
        for chunk in vanna_resp.chunks:
            rich = get_field(chunk, 'rich')
            if rich:
                r_type = get_field(rich, 'type')
                r_data = get_field(rich, 'data') or {}
                if r_type == 'text':
                    content = get_field(r_data, 'content')
                    if content and content not in markdown_report:
                        markdown_report += content + "\n\n"
                elif r_type == 'status_card':
                    metadata = get_field(r_data, 'metadata') or {}
                    sql = get_field(metadata, 'sql')
                    if sql:
                        sql_used = sql
                elif r_type == 'dataframe':
                    cols = get_field(r_data, 'columns') or []
                    rows = get_field(r_data, 'data') or []
                    if cols and rows:
                        table_md = "| " + " | ".join(str(c) for c in cols) + " |\n"
                        table_md += "| " + " | ".join(["---"] * len(cols)) + " |\n"
                        for row in rows[:100]:
                            table_md += "| " + " | ".join(str(get_field(row, c, '')) for c in cols) + " |\n"
                        markdown_report += "\n" + table_md + "\n"

            if not rich:
                simple = get_field(chunk, 'simple')
                if simple:
                    stext = get_field(simple, 'text')
                    if stext and isinstance(stext, str):
                        stext = stext.strip()
                        if stext and stext not in markdown_report and "Tool completed successfully" not in stext and "IMPORTANT: FOR VISUALIZE_DATA" not in stext:
                            markdown_report += stext + "\n"


        
        if not markdown_report.strip():
            # Default response for casual greetings if no text chunk was generated
            markdown_report = "Hello! I am Vanna AI 2.0. How can I assist you with PMC database analytics today?"

        agent_res = {
            "content": markdown_report.strip(),
            "sql_used": sql_used,
            "execution_time_ms": exec_ms,
            "status": "SUCCESS"
        }
    except Exception as e:
        logger.warning(f"Vanna AI processing exception: {e}")

    if not agent_res:
        agent_res = MasterOrchestratorAgent.process_query(
            query_text=payload.content,
            metadata_session=db,
            session_history=history_dicts,
            max_retries=3
        )



    markdown_report = agent_res.get("content", "")
    sql_used = agent_res.get("sql_used", "")
    template_id = agent_res.get("template_id")
    candidate_templates = agent_res.get("candidate_templates")
    execution_time_ms = agent_res.get("execution_time_ms", 0.0)
    retry_count = agent_res.get("retry_count", 0)
    execution_success = agent_res.get("status") in ["SUCCESS", "REFUSED", "FOLLOW_UP"]

    # Save Agent message to DB
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

