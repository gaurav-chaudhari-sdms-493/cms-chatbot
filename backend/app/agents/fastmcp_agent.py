import json
import logging
from typing import Tuple, List, Dict, Any
from app.api.llm_client import call_openrouter_api
from app.mcp.tools import execute_sql_query, sample_column_values, inspect_table_columns

logger = logging.getLogger("pmc_chatbot.agents.fastmcp")


class FastMCPAgent:
    """Specialized Agent for Autonomous Native FastMCP Tool Calling & Inspection."""

    @classmethod
    def run_tool_loop(
        cls,
        schema_context: str,
        question: str,
        max_steps: int = 5,
        history_context: str = ""
    ) -> Tuple[str, List[str], List[Any], int]:
        """
        Executes a True Native FastMCP Tool-Calling Loop.
        Returns (sql_used, columns, rows, steps_taken).
        """
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

        tool_models = ["meta-llama/llama-3.3-70b-instruct"]

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

                logger.info(f"FastMCPAgent Step {steps_taken}: Tool Call `{fname}` with args {args}")

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
