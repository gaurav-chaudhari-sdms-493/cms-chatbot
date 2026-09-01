import re
import time
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.models import QueryTemplate, QueryExecutionLog

logger = logging.getLogger("pmc_chatbot.agents.sql_executor")


class SQLValidationError(ValueError):
    """Raised when SQL fails safety validation constraints."""
    pass


class SQLExecutorAgent:
    """Specialized Agent for SQL Safety Validation & Parameterized Execution."""

    DISALLOWED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "GRANT", "REVOKE", "EXEC", "EXECUTE", "CREATE", "REPLACE"
    ]

    @classmethod
    def validate_sql(cls, sql_text: str) -> bool:
        """Ensures SQL statement begins with SELECT or WITH and contains no mutation keywords."""
        cleaned_sql = sql_text.strip()
        if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
            raise SQLValidationError("SQL statement must begin with SELECT or WITH.")

        for keyword in cls.DISALLOWED_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                raise SQLValidationError(f"Forbidden SQL keyword detected: '{keyword}'")

        return True

    @classmethod
    def execute_template(
        cls,
        template_id: str,
        parameters: Dict[str, Any],
        metadata_session: Session,
        pmc_session: Session,
        max_rows: int = 1000,
        timeout_sec: int = 10
    ) -> Dict[str, Any]:
        """Validates template approval, binds parameters securely, enforces statement timeout, and executes SQL."""
        start_time = time.time()

        # 1. Fetch template record
        template = metadata_session.query(QueryTemplate).filter(
            QueryTemplate.template_id == template_id,
            QueryTemplate.is_active == True
        ).first()

        if not template:
            raise ValueError(f"Template '{template_id}' is not active or approved.")

        # 2. SQL Safety Validation
        cls.validate_sql(template.sql_template)

        # 3. Normalize parameter keys (e.g. handle limit vs limit_id, department_id vs department)
        normalized_params: Dict[str, Any] = {}
        for k, v in parameters.items():
            normalized_params[k] = v
            if k.endswith("_id"):
                normalized_params[k[:-3]] = v
            else:
                normalized_params[f"{k}_id"] = v

        # 4. Bind parameters securely
        sql_stmt = text(template.sql_template)
        for bp_name in sql_stmt._bindparams.keys():
            if bp_name not in normalized_params:
                normalized_params[bp_name] = None

        # Set statement timeout on connection
        pmc_session.execute(text(f"SET statement_timeout = '{timeout_sec}s';"))

        # 5. Execute query
        cursor = pmc_session.execute(sql_stmt, normalized_params)
        columns = list(cursor.keys())
        rows = cursor.fetchmany(max_rows)

        formatted_data = [dict(zip(columns, row)) for row in rows]
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # 6. Audit Logging
        try:
            log_entry = QueryExecutionLog(
                query_text=template.retrieval_text,
                template_id=template_id,
                template_version=template.version,
                bound_parameters=parameters,
                result_row_count=len(formatted_data),
                execution_time_ms=elapsed_ms,
                status="SUCCESS"
            )
            metadata_session.add(log_entry)
            metadata_session.commit()
        except Exception as log_err:
            metadata_session.rollback()
            logger.warning(f"Failed to log query execution: {log_err}")

        logger.info(f"SQLExecutorAgent executed template '{template_id}' in {elapsed_ms}ms ({len(formatted_data)} rows)")

        return {
            "status": "SUCCESS",
            "template_id": template_id,
            "sql_template": template.sql_template,
            "execution_time_ms": elapsed_ms,
            "total_rows": len(formatted_data),
            "columns": columns,
            "data": formatted_data
        }
