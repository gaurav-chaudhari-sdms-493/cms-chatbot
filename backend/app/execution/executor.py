import time
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.models import QueryTemplate, QueryTemplatePlaceholder
from app.execution.validator import SQLSafetyValidator


class QueryExecutor:
    """Safe parameterized SQL executor for approved templates."""

    @staticmethod
    def execute_template(
        template_id: str,
        parameters: Dict[str, Any],
        metadata_session: Session,
        pmc_session: Session,
        max_rows: int = 1000,
        timeout_sec: int = 10
    ) -> Dict[str, Any]:
        """
        Validates template approval, binds parameters securely, enforces statement timeout,
        and executes SQL query against remote PMC database.
        """
        start_time = time.time()

        # 1. Fetch template record from metadata DB
        template = metadata_session.query(QueryTemplate).filter(
            QueryTemplate.template_id == template_id,
            QueryTemplate.is_active == True
        ).first()

        if not template:
            raise ValueError(f"Template '{template_id}' is not active or approved.")

        # 2. SQL Safety Validation
        if not SQLSafetyValidator.validate_sql(template.sql_template):
            raise ValueError(f"Template '{template_id}' failed safety validation rules.")

        # 3. Normalize parameter keys (e.g. handle limit vs limit_id, department_id vs department)
        normalized_params: Dict[str, Any] = {}
        for k, v in parameters.items():
            normalized_params[k] = v
            if k.endswith("_id"):
                base_k = k[:-3]
                normalized_params[base_k] = v
            else:
                id_k = f"{k}_id"
                normalized_params[id_k] = v

        # 4. Bind parameters securely using SQLAlchemy text()
        sql_stmt = text(template.sql_template)

        # Set statement timeout on postgres connection
        pmc_session.execute(text(f"SET statement_timeout = '{timeout_sec}s';"))

        # 5. Execute parameterized query
        cursor = pmc_session.execute(sql_stmt, normalized_params)
        columns = list(cursor.keys())
        rows = cursor.fetchmany(max_rows)

        formatted_data = [dict(zip(columns, row)) for row in rows]
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # 6. Record execution audit log in local metadata DB
        try:
            from app.db.models import QueryExecutionLog
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
            print(f"Warning: Failed to log query execution: {log_err}")

        return {
            "status": "SUCCESS",
            "template_id": template_id,
            "execution_time_ms": elapsed_ms,
            "total_rows": len(formatted_data),
            "columns": columns,
            "data": formatted_data
        }
