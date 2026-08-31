import os
import time
import logging
import requests
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

logger = logging.getLogger("pmc_chatbot.llm")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Standard FastMCP Tool Schemas exposed to AI models
MCP_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Executes a read-only PostgreSQL SELECT query against the PMC Grievance Database and returns execution results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string", "description": "Valid PostgreSQL SELECT query to execute against PMC DB"}
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sample_values",
            "description": "Samples distinct non-null column values from any PostgreSQL table to inspect real data (including Marathi terms) prior to query building.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "PostgreSQL table name (e.g. ward_master, category_master, user_master, status_master)"},
                    "column_name": {"type": "string", "description": "Column name to sample distinct values from"}
                },
                "required": ["table_name", "column_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_columns",
            "description": "Returns column names and data types for any PMC database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Table name to inspect schema for"}
                },
                "required": ["table_name"]
            }
        }
    }
]

def call_openrouter_api(contents: Union[str, List[Dict[str, Any]]], models: Optional[List[str]] = None, use_tools: bool = False) -> Optional[Dict[str, Any]]:
    """Calls OpenRouter unified AI endpoint with enterprise models and optional native FastMCP tool schemas."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured in .env file.")

    model_candidates = models or [
        "google/gemini-2.5-flash",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-coder-32b-instruct",
        "meta-llama/llama-3.1-8b-instruct"
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "PMC Officer Query System",
        "Content-Type": "application/json"
    }

    messages = contents if isinstance(contents, list) else [{"role": "user", "content": contents}]

    for model_name in model_candidates:
        try:
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.1
            }
            if use_tools:
                payload["tools"] = MCP_TOOLS_SCHEMA

            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content")
                if content and str(content).strip():
                    logger.info(f"OpenRouter API success using model '{model_name}'.")
                    return message
                elif use_tools and message.get("tool_calls"):
                    logger.info(f"OpenRouter API success (tool call) using model '{model_name}'.")
                    return message
            else:
                logger.warning(f"OpenRouter model '{model_name}' returned status {resp.status_code}: {resp.text}")
        except Exception as err:
            logger.warning(f"OpenRouter attempt failed on '{model_name}': {str(err)}")
            continue

    return None

def call_gemini_with_key_rotation(contents: str, models: Optional[List[str]] = None) -> tuple[str, str]:
    """
    Standard OpenRouter LLM interface. Calls OpenRouter API and returns (response_text, provider_info).
    """
    msg = call_openrouter_api(contents, models)
    if msg and isinstance(msg, dict):
        content = msg.get("content") or ""
        if content.strip():
            return content, "OpenRouter Enterprise API"
    
    raise RuntimeError("OpenRouter API request failed across all candidate models.")


def execute_fastmcp_agent_loop(schema_context: str, question: str, max_steps: int = 5, history_context: str = "") -> tuple[str, list, list, int]:
    """
    Executes a True Native FastMCP Tool-Calling Loop.
    The AI model interactively calls FastMCP tools (sample_values, inspect_columns, execute_sql).
    Returns (sql_used, columns, rows, steps_taken)
    """
    from app.mcp.tools import execute_sql_query, sample_column_values, inspect_table_columns
    import json

    system_instructions = (
        f"You are an autonomous PostgreSQL Data Analyst AI.\n"
        f"You have access to native FastMCP tools: `sample_values`, `inspect_columns`, `execute_sql`.\n"
        f"Use these tools interactively to inspect schema definitions, sample distinct lookup values, and execute read-only PostgreSQL SELECT queries to answer the officer's question.\n"
        f"Note for date queries: For complaint resolution timeframes (e.g. 'resolved in the last 30 days'), check `updated_at` timestamps in addition to `created_at`.\n\n"
        f"{schema_context}"
    )

    user_prompt = f"Previous Conversation Context:\n{history_context}\n\nCurrent Question: {question}" if history_context else question

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt}
    ]


    tool_models = ["google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct", "openai/gpt-4o-mini"]

    sql_used = ""
    columns = []
    rows = []
    steps_taken = 0

    for step in range(max_steps):
        steps_taken = step + 1
        msg = call_openrouter_api(messages, models=tool_models, use_tools=True)
        if not msg:
            break

        messages.append(msg)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            break

        for tc in tool_calls:
            func = tc.get("function", {})
            fname = func.get("name")
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str)
            except Exception:
                args = {}

            logger.info(f"FastMCP Agent Step {steps_taken}: Tool Call `{fname}` with args {args}")

            if fname == "sample_values":
                res = sample_column_values(args.get("table_name", ""), args.get("column_name", ""))
            elif fname == "inspect_columns":
                res = inspect_table_columns(args.get("table_name", ""))
            elif fname == "execute_sql":
                res = execute_sql_query(args.get("sql_query", ""))
                if res.get("status") == "SUCCESS":
                    columns = res.get("columns", [])
                    res_rows = res.get("rows", [])
                    is_zero = len(res_rows) == 0 or (len(res_rows) == 1 and len(res_rows[0]) == 1 and str(res_rows[0][0]).strip() in ["0", "None", "", "null"])
                    if not is_zero or not sql_used:
                        sql_used = args.get("sql_query", "")
                        rows = res_rows
                    if is_zero:
                        res["note"] = "Query returned 0 matching records. Consider calling `sample_values` to verify exact category names (English/Marathi) in category_master or status_group in status_master."
            else:
                res = {"error": f"Unknown function {fname}"}

            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "name": fname,
                "content": json.dumps(res)
            })


    return sql_used, columns, rows, steps_taken

