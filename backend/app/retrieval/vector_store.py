import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import QueryTemplate
from app.retrieval.embedder import embedding_service


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class VectorSearchEngine:
    """Engine for ranking structural query templates by vector similarity and placeholder count alignment."""

    @staticmethod
    def search_templates(
        query_text: str,
        session: Session,
        top_k: int = 5,
        threshold: float = 0.50
    ) -> List[Dict[str, Any]]:
        """
        Generates query embedding and ranks candidate query templates by cosine similarity.
        Filters out candidates scoring below similarity threshold.
        """
        # Generate query vector with 'query: ' prefix
        query_vector = embedding_service.generate_embedding(query_text, is_query=True)

        # Fetch active templates from metadata DB
        templates = session.query(QueryTemplate).filter(QueryTemplate.is_active == True).all()

        scored_candidates = []
        for t in templates:
            if not t.embedding:
                continue
            
            score = cosine_similarity(query_vector, t.embedding)
            if score >= threshold:
                placeholder_list = [
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
                    for p in t.placeholders
                ]

                scored_candidates.append({
                    "template_id": t.template_id,
                    "intent": t.intent,
                    "question_template": t.question_template,
                    "retrieval_text": t.retrieval_text,
                    "sql_template": t.sql_template,
                    "result_type": t.result_type,
                    "version": t.version,
                    "score": round(score, 4),
                    "placeholders": placeholder_list
                })

        # Sort candidates descending by similarity score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]
