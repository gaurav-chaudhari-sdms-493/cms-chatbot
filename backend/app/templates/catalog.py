"""
Database Template Repository for PMC Officer Query System.
Dynamic ORM loader for query templates and placeholders stored in pmc_metadata_db.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import QueryTemplate, QueryTemplatePlaceholder
from app.db.session import get_metadata_session


class TemplateRepository:
    """Standard database repository service for reading and managing templates in pmc_metadata_db."""

    @staticmethod
    def get_all_active_templates(session: Session) -> List[QueryTemplate]:
        """Fetch all active templates from pmc_metadata_db."""
        return session.query(QueryTemplate).filter_by(is_active=True).all()

    @staticmethod
    def get_template_by_id(session: Session, template_id: str) -> Optional[QueryTemplate]:
        """Fetch a specific template by template_id from pmc_metadata_db."""
        return session.query(QueryTemplate).filter_by(template_id=template_id).first()

    @staticmethod
    def format_template_dict(template: QueryTemplate) -> Dict[str, Any]:
        """Formats QueryTemplate ORM instance into a dictionary."""
        placeholders = [
            {
                "placeholder_name": p.placeholder_name,
                "data_type": p.data_type,
                "input_mode": p.input_mode,
                "source_table": p.source_table,
                "source_id_column": p.source_id_column,
                "source_label_column": p.source_label_column,
                "required": p.required,
                "display_order": p.display_order
            }
            for p in sorted(template.placeholders, key=lambda x: x.display_order)
        ]
        return {
            "template_id": template.template_id,
            "intent": template.intent,
            "question_template": template.question_template,
            "retrieval_text": template.retrieval_text,
            "sql_template": template.sql_template,
            "result_type": template.result_type,
            "is_active": template.is_active,
            "version": template.version,
            "placeholders": placeholders
        }
