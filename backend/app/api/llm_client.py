import os
import time
import logging
import requests
from typing import List, Optional, Dict, Any, Union
from google import genai
from dotenv import load_dotenv

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
        return None

    model_candidates = models or [
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-coder-32b-instruct",
        "deepseek/deepseek-r1-distill-llama-70b",
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

            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)

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

def get_api_keys() -> List[str]:
    keys = []
    k1 = os.getenv("GEMINI_API_KEY")
    k2 = os.getenv("GEMINI_API_KEY_2")
    k3 = os.getenv("GEMINI_API_KEY_3")
    if k1: keys.append(k1.strip())
    if k2: keys.append(k2.strip())
    if k3: keys.append(k3.strip())
    return keys

def call_gemini_with_key_rotation(contents: str, models: Optional[List[str]] = None) -> tuple[str, str]:
    """
    Calls OpenRouter API first (if key configured). If OpenRouter fails, falls back to direct Gemini key rotation.
    Returns (response_text, provider_info)
    """
    if OPENROUTER_API_KEY:
        openrouter_msg = call_openrouter_api(contents, models)
        if openrouter_msg and isinstance(openrouter_msg, dict):
            content = openrouter_msg.get("content") or ""
            if content.strip():
                return content, "OpenRouter Enterprise API"


    keys = get_api_keys()
    if not keys:
        raise ValueError("No OPENROUTER_API_KEY or GEMINI_API_KEY configured in environment.")

    model_candidates = models or ["gemini-2.5-flash", "gemini-1.5-flash"]

    last_err = ""

    for key_idx, key in enumerate(keys):
        client = genai.Client(api_key=key)
        for model_name in model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    logger.info(f"Gemini API success using Key #{key_idx + 1} and model '{model_name}'.")
                    return response.text, f"Key-{key_idx + 1}"
            except Exception as err:
                last_err = str(err)
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    logger.warning(f"Key #{key_idx + 1} hit 429 rate limit on model '{model_name}'. Rotating key...")
                    time.sleep(1.0)
                    break
                else:
                    logger.warning(f"Key #{key_idx + 1} failed on model '{model_name}': {last_err}")
                    continue

    raise RuntimeError(f"All LLM providers and keys failed. Last error: {last_err}")


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

