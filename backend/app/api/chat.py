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
    total_records: Optional[int] = None
    created_at: str

class ChatSessionDetailResponse(BaseModel):
    id: str
    title: str
    mode: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageResponse]

class PageQueryRequest(BaseModel):
    sql_query: str
    page: int = 1
    page_size: int = 25
    search_term: Optional[str] = None
    sort_column: Optional[str] = None
    sort_direction: Optional[str] = None  # 'asc' | 'desc'
    column_filters: Optional[Dict[str, Any]] = None

class ColumnValuesRequest(BaseModel):
    sql_query: str
    column_name: str

def execute_paginated_sql(
    sql_query: str,
    page: int = 1,
    page_size: int = 25,
    search_term: Optional[str] = None,
    sort_column: Optional[str] = None,
    sort_direction: Optional[str] = None,
    column_filters: Optional[Dict[str, Any]] = None
):
    """
    Executes server-side sorting, column filtering, global search, COUNT(*) subquery, and page LIMIT/OFFSET
    against the PMC PostgreSQL DB across ALL matching records.
    """
    import re
    clean_sql = sql_query.strip().rstrip(';')

    # Strip top-level LIMIT / OFFSET from base query if present
    base_sql = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?', '', clean_sql, flags=re.IGNORECASE)

    # Wrap base query in subquery so we can apply search, column filters, and sorting safely
    wrap_sql = f"SELECT * FROM ({base_sql}) AS main_query"
    where_conditions = []

    with sync_pmc_engine.connect() as conn:
        # Resolve real PostgreSQL column names in subquery case-insensitively
        cols = []
        col_map = {}
        try:
            sample_res = conn.execute(text(f"SELECT * FROM ({base_sql}) AS main_query WHERE 1=0"))
            cols = list(sample_res.keys())
            col_map = {c.lower(): c for c in cols}
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        # 1. Global Search Filter across ALL columns
        if search_term and search_term.strip():
            st = search_term.strip().replace("'", "''")
            where_conditions.append(f"EXISTS (SELECT 1 FROM jsonb_each_text(to_jsonb(main_query)) t WHERE t.value ILIKE '%{st}%')")

        # 2. Per-Column Filters (supports exact string match, ILIKE, or multi-value IN arrays)
        if column_filters:
            for col_name, filter_val in column_filters.items():
                if filter_val is not None:
                    clean_col = col_map.get(col_name.strip().lower(), col_name.strip().replace('"', ''))
                    if isinstance(filter_val, list):
                        clean_vals = [str(v).replace("'", "''") for v in filter_val if v is not None and str(v).strip() != '']
                        if clean_vals:
                            quoted_vals = ", ".join([f"'{v}'" for v in clean_vals])
                            where_conditions.append(f"CAST(main_query.\"{clean_col}\" AS TEXT) IN ({quoted_vals})")
                    else:
                        fv = str(filter_val).strip().replace("'", "''")
                        if fv:
                            where_conditions.append(f"LOWER(CAST(main_query.\"{clean_col}\" AS TEXT)) ILIKE '%{fv.lower()}%'")

        full_where = ""
        if where_conditions:
            full_where = " WHERE " + " AND ".join(where_conditions)

        # 3. Order By clause across entire DB query
        order_by_clause = ""
        if sort_column and sort_column.strip() and sort_direction in ['asc', 'desc']:
            clean_sort_col = col_map.get(sort_column.strip().lower(), sort_column.strip().replace('"', ''))
            direction_str = sort_direction.upper()
            order_by_clause = f" ORDER BY main_query.\"{clean_sort_col}\" {direction_str} NULLS LAST"

        count_sql = f"SELECT COUNT(*) AS total FROM ({wrap_sql}{full_where}) AS count_subquery"
        offset = (page - 1) * page_size
    page_sql = f"{wrap_sql}{full_where}{order_by_clause} LIMIT {page_size} OFFSET {offset}"

    with sync_pmc_engine.connect() as conn:
        total_records = 0
        try:
            count_res = conn.execute(text(count_sql)).fetchone()
            if count_res:
                total_records = count_res[0]
        except Exception as err:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning(f"Count query failed: {err}")

        try:
            page_res = conn.execute(text(page_sql))
            cols = list(page_res.keys())
            raw_rows = page_res.fetchall()
            rows = [[str(val) if val is not None else "" for val in row] for row in raw_rows]
        except Exception as page_err:
            try:
                conn.rollback()
            except Exception:
                pass
            raise page_err

        if total_records == 0 and rows:
            total_records = len(rows)

        total_pages = (total_records + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "columns": cols,
            "rows": rows,
            "total_records": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": max(total_pages, 1)
        }

@router.post("/query-page")
def get_query_page(payload: PageQueryRequest):
    if not payload.sql_query or not payload.sql_query.strip():
        raise HTTPException(status_code=400, detail="SQL query is required")
    try:
        res = execute_paginated_sql(
            sql_query=payload.sql_query,
            page=payload.page,
            page_size=payload.page_size,
            search_term=payload.search_term,
            sort_column=payload.sort_column,
            sort_direction=payload.sort_direction,
            column_filters=payload.column_filters
        )
        return res
    except Exception as e:
        logger.error(f"Page query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/column-values")
def get_column_values(payload: ColumnValuesRequest):
    if not payload.sql_query or not payload.sql_query.strip():
        raise HTTPException(status_code=400, detail="SQL query is required")
    if not payload.column_name or not payload.column_name.strip():
        raise HTTPException(status_code=400, detail="Column name is required")

    import re
    clean_sql = payload.sql_query.strip().rstrip(';')
    base_sql = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?', '', clean_sql, flags=re.IGNORECASE)

    with sync_pmc_engine.connect() as conn:
        col_map = {}
        try:
            sample_res = conn.execute(text(f"SELECT * FROM ({base_sql}) AS main_query WHERE 1=0"))
            cols = list(sample_res.keys())
            col_map = {c.lower(): c for c in cols}
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        clean_col = col_map.get(payload.column_name.strip().lower(), payload.column_name.strip().replace('"', ''))

        values_sql = f"""
            SELECT COALESCE(CAST(main_query."{clean_col}" AS TEXT), '(Blank / Null)') AS val, COUNT(*) AS count
            FROM ({base_sql}) AS main_query
            GROUP BY val
            ORDER BY count DESC, val ASC
            LIMIT 500
        """
        try:
            res = conn.execute(text(values_sql)).fetchall()
            items = [{"value": str(row[0]) if row[0] is not None else "(Blank / Null)", "count": row[1]} for row in res]
            return {"column": payload.column_name, "values": items}
        except Exception as e:
            logger.error(f"Error fetching column values for {payload.column_name}: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=str(e))

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
                total_records=getattr(m, 'total_records', None),
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
            total_records=getattr(m, 'total_records', None),
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

        # Check top-level vanna_resp attributes if present
        if hasattr(vanna_resp, 'sql') and vanna_resp.sql:
            sql_used = str(vanna_resp.sql).strip()

        for chunk in (getattr(vanna_resp, 'chunks', None) or []):
            rich = get_field(chunk, 'rich')
            if rich:
                r_type = get_field(rich, 'type')
                r_data = get_field(rich, 'data') or {}
                if r_type in ('text', 'markdown'):
                    content = get_field(r_data, 'content') or get_field(r_data, 'text')
                    if content and content not in markdown_report:
                        markdown_report += str(content) + "\n\n"

                # Extract SQL from rich chunk data/metadata regardless of component type
                metadata = get_field(r_data, 'metadata') or {}
                extracted_sql = (
                    get_field(metadata, 'sql') or
                    get_field(r_data, 'sql') or
                    get_field(r_data, 'code') or
                    get_field(get_field(r_data, 'tool_call', {}), 'args', {}).get('sql')
                )
                if extracted_sql and isinstance(extracted_sql, str) and extracted_sql.strip():
                    sql_used = extracted_sql.strip()

            simple = get_field(chunk, 'simple')
            if simple:
                stext = get_field(simple, 'text') or get_field(simple, 'content')
                if stext and isinstance(stext, str):
                    stext = stext.strip()
                    if stext and stext not in markdown_report:
                        markdown_report += stext + "\n\n"

            # Direct attributes on chunk
            ctext = get_field(chunk, 'text') or get_field(chunk, 'content')
            if ctext and isinstance(ctext, str) and ctext.strip() not in markdown_report:
                markdown_report += ctext.strip() + "\n\n"

            csql = get_field(chunk, 'sql') or get_field(chunk, 'code')
            if csql and isinstance(csql, str) and csql.strip():
                sql_used = csql.strip()

        # If sql_used not found from chunks, attempt regex extraction from markdown_report
        if not sql_used:
            import re
            sql_match = re.search(r'```sql\s*(.*?)\s*```', markdown_report, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql_used = sql_match.group(1).strip()

        total_records = None
        if sql_used.strip():
            # 1. Execute COUNT(*) subquery to get exact total records across DB
            try:
                import re
                clean_sql = sql_used.strip().rstrip(';')
                base_sql = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?', '', clean_sql, flags=re.IGNORECASE)
                count_sql = f"SELECT COUNT(*) AS total FROM ({base_sql}) AS count_subquery"
                with sync_pmc_engine.connect() as conn:
                    try:
                        c_res = conn.execute(text(count_sql)).fetchone()
                        if c_res:
                            total_records = c_res[0]
                    except Exception as sub_err:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        raise sub_err
            except Exception as cnt_err:
                logger.warning(f"Count calculation failed: {cnt_err}")

            # 2. Always fetch clean Page 1 (25 rows) directly from PMC DB
            try:
                page_data = execute_paginated_sql(sql_used, page=1, page_size=25)
                cols = page_data["columns"]
                rows = page_data["rows"]
                if total_records is None:
                    total_records = page_data["total_records"]

                if cols and rows:
                    table_md = "| " + " | ".join(str(c) for c in cols) + " |\n"
                    table_md += "| " + " | ".join(["---"] * len(cols)) + " |\n"
                    for row in rows:
                        table_md += "| " + " | ".join(str(val) if val is not None else '' for val in row) + " |\n"

                    # Always output clean paginated table with total records header and zero raw dumps
                    if total_records is not None:
                        markdown_report = f"### Query Results ({total_records:,} total records)\n\n{table_md}"
                    else:
                        markdown_report = table_md
                else:
                    markdown_report = "Query executed successfully. No matching records found."
            except Exception as sql_err:
                logger.error(f"SQL execution error: {sql_err}")
                markdown_report = f"Error executing query: {sql_err}"

        # Optional Legacy Fallback Switch (Set to True if legacy MasterOrchestratorAgent fallback is desired)
        ENABLE_LEGACY_ORCHESTRATOR_FALLBACK = False

        if ENABLE_LEGACY_ORCHESTRATOR_FALLBACK and (not markdown_report.strip() or "No matching records found" in markdown_report or markdown_report.strip() == "No response generated."):
            logger.info(f"Vanna AI yielded empty/zero-result report for query '{payload.content}'. Invoking MasterOrchestratorAgent auto-correction...")
            try:
                orch_res = MasterOrchestratorAgent.process_query(
                    query_text=payload.content,
                    metadata_session=db,
                    session_history=history_dicts
                )
                if orch_res and orch_res.get("content") and "No matching records found" not in orch_res.get("content"):
                    markdown_report = orch_res.get("content").strip()
                    sql_used = orch_res.get("sql_used") or sql_used
                    template_id = orch_res.get("template_id")
                    candidate_templates = orch_res.get("candidate_templates")
                    if orch_res.get("execution_time_ms"):
                        exec_ms += orch_res.get("execution_time_ms")
            except Exception as orch_err:
                logger.error(f"MasterOrchestratorAgent fallback failed: {orch_err}")

        if not markdown_report.strip():
            markdown_report = "Query executed successfully. No matching records found for your query."

        agent_res = {
            "content": markdown_report.strip(),
            "sql_used": sql_used,
            "total_records": total_records,
            "execution_time_ms": exec_ms,
            "status": "SUCCESS"
        }
    except Exception as e:
        logger.error(f"Vanna AI processing exception: {e}")
        orch_content = ""
        if ENABLE_LEGACY_ORCHESTRATOR_FALLBACK:
            try:
                orch_res = MasterOrchestratorAgent.process_query(
                    query_text=payload.content,
                    metadata_session=db,
                    session_history=history_dicts
                )
                orch_content = orch_res.get("content", "").strip()
                sql_used = orch_res.get("sql_used", "")
            except Exception:
                pass

        agent_res = {
            "content": orch_content if orch_content else f"An error occurred while processing your request: {e}",
            "sql_used": sql_used,
            "total_records": None,
            "execution_time_ms": 0.0,
            "status": "SUCCESS" if orch_content else "ERROR"
        }



    markdown_report = agent_res.get("content", "")
    sql_used = agent_res.get("sql_used", "")
    template_id = agent_res.get("template_id")
    candidate_templates = agent_res.get("candidate_templates")
    execution_time_ms = agent_res.get("execution_time_ms", 0.0)
    total_records = agent_res.get("total_records")
    retry_count = agent_res.get("retry_count", 0)
    execution_success = agent_res.get("status") in ["SUCCESS", "REFUSED", "FOLLOW_UP"]

    # Save Agent message to DB
    agent_msg = ChatMessage(
        session_id=session.id,
        sender="agent",
        content=markdown_report,
        sql_used=sql_used,
        template_id=template_id,
        total_records=total_records,
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
            total_records=total_records,
            created_at=agent_msg.created_at.isoformat()
        ),
        "sql_used": sql_used,
        "template_id": template_id,
        "candidate_templates": candidate_templates,
        "execution_time_ms": execution_time_ms,
        "total_records": total_records,
        "retry_count": retry_count,
        "status": "SUCCESS" if execution_success else "FAILED"
    }

