from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process


class EntityResolver:
    """Resolves categorical string spans against database master tables using fuzzy matching."""

    @staticmethod
    def resolve_reference(
        query_text: str,
        source_table: str,
        source_id_col: str,
        source_label_col: str,
        pmc_session: Session,
        threshold: float = 75.0
    ) -> Optional[Dict[str, Any]]:
        """
        Queries target master table, matches substrings of query_text against labels using rapidfuzz,
        and returns canonical { "id": id_val, "label": label_val } if score >= threshold.
        """
        if not source_table or not source_id_col or not source_label_col:
            return None

        # Safe select from approved master tables only
        approved_tables = {
            "department_master",
            "ward_master",
            "category_master",
            "sub_category_master",
            "status_master",
            "zone_master",
            "prabhag_master"
        }
        if source_table not in approved_tables:
            return None

        sql = text(f"SELECT {source_id_col}, {source_label_col} FROM {source_table};")
        records = pmc_session.execute(sql).fetchall()
        if not records:
            return None

        # Build map of label -> id
        label_to_id = {str(r[1]): r[0] for r in records}
        candidate_labels = list(label_to_id.keys())

        # Extract best partial fuzzy match from query_text
        match_result = process.extractOne(
            query_text,
            candidate_labels,
            scorer=fuzz.partial_ratio
        )

        if match_result and match_result[1] >= threshold:
            best_label = match_result[0]
            matched_id = label_to_id[best_label]
            return {
                "id": matched_id,
                "label": best_label,
                "confidence": round(match_result[1], 2)
            }

        return None
