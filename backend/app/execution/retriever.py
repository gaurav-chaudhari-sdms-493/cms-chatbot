import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import QueryTemplate
from app.retrieval.embedder import embedding_service

class HybridTemplateRetriever:
    """
    Implements Hybrid Search (Dense E5 Vector Search + Lexical BM25 Search)
    combined via Reciprocal Rank Fusion (RRF) to retrieve candidate query templates.
    """

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def _lexical_score(query: str, template: QueryTemplate) -> float:
        """Computes keyword match score across retrieval_text, question_template, and intent."""
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return 0.0

        target_text = f"{template.question_template} {template.retrieval_text} {template.intent}".lower()
        matches = sum(1 for word in query_words if word in target_text and len(word) > 2)
        return matches / max(len(query_words), 1)

    @classmethod
    def get_top_candidates(cls, query_text: str, metadata_session: Session, top_k: int = 5) -> List[Tuple[QueryTemplate, float]]:
        """
        Executes Dense E5 + Lexical BM25 search and ranks templates using Reciprocal Rank Fusion (RRF).
        Returns list of (template, rrf_score) tuples.
        """
        # 1. Fetch active templates from DB
        templates = metadata_session.query(QueryTemplate).filter(
            QueryTemplate.is_active == True
        ).all()

        if not templates:
            return []

        # 2. Compute Dense Vector Cosine Similarity
        query_embedding = embedding_service.generate_embedding(query_text, is_query=True)

        dense_scores: List[Tuple[QueryTemplate, float]] = []
        dirty_templates = False

        for tpl in templates:
            if not tpl.embedding and (tpl.retrieval_text or tpl.question_template):
                try:
                    text_to_embed = tpl.retrieval_text or tpl.question_template
                    tpl.embedding = embedding_service.generate_embedding(text_to_embed, is_query=False)
                    dirty_templates = True
                except Exception as emb_err:
                    pass

            if tpl.embedding:
                sim = cls._cosine_similarity(query_embedding, tpl.embedding)
                dense_scores.append((tpl, sim))
            else:
                dense_scores.append((tpl, 0.0))

        if dirty_templates:
            try:
                metadata_session.commit()
            except Exception:
                metadata_session.rollback()

        # Sort dense scores descending
        dense_scores.sort(key=lambda x: x[1], reverse=True)
        dense_ranks = {tpl.template_id: rank + 1 for rank, (tpl, _) in enumerate(dense_scores)}

        # 3. Compute Lexical Scores
        lexical_scores: List[Tuple[QueryTemplate, float]] = []
        for tpl in templates:
            score = cls._lexical_score(query_text, tpl)
            lexical_scores.append((tpl, score))

        lexical_scores.sort(key=lambda x: x[1], reverse=True)
        lexical_ranks = {tpl.template_id: rank + 1 for rank, (tpl, _) in enumerate(lexical_scores)}

        # 4. Reciprocal Rank Fusion (RRF) Computation (k = 60)
        rrf_results: List[Tuple[QueryTemplate, float]] = []
        template_map = {t.template_id: t for t in templates}

        for tid, tpl in template_map.items():
            r_dense = dense_ranks.get(tid, 100)
            r_lexical = lexical_ranks.get(tid, 100)
            rrf_score = (1.0 / (60.0 + r_dense)) + (1.0 / (60.0 + r_lexical))
            rrf_results.append((tpl, rrf_score))

        rrf_results.sort(key=lambda x: x[1], reverse=True)
        return rrf_results[:top_k]
