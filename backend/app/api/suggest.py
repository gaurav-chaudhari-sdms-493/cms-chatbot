from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_metadata_session, sync_pmc_engine
from app.schemas.query import SuggestQueryRequest, SuggestQueryResponse, SuggestionDTO, DetectedValueDTO, PlaceholderMetadataDTO
from app.retrieval.vector_store import VectorSearchEngine
from app.entities.extractor import EntityExtractor
from app.entities.resolver import EntityResolver

router = APIRouter()


@router.post("/query/suggest", response_model=SuggestQueryResponse)
def suggest_templates(payload: SuggestQueryRequest):
    """
    Accepts natural language query string, generates vector embedding, retrieves Top-K
    matching query templates, extracts entities, and returns missing placeholders.
    """
    metadata_session = get_metadata_session()
    
    try:
        # 1. Perform vector similarity search over templates
        candidate_templates = VectorSearchEngine.search_templates(
            query_text=payload.query,
            session=metadata_session,
            top_k=payload.top_k,
            threshold=payload.threshold
        )

        regex_entities = EntityExtractor.extract_regex_entities(payload.query)
        suggestions = []

        with sync_pmc_engine.connect() as pmc_conn:
            for cand in candidate_templates:
                detected_values = {}
                missing_placeholders = []

                for p in cand["placeholders"]:
                    p_name = p["placeholder_name"]
                    p_type = p["data_type"]
                    resolved_val = None

                    # Check if entity was resolved via DB reference matching
                    if p_type == "REFERENCE" and p.get("source_table"):
                        resolved_val = EntityResolver.resolve_reference(
                            query_text=payload.query,
                            source_table=p["source_table"],
                            source_id_col=p["source_id_column"],
                            source_label_col=p["source_label_column"],
                            pmc_session=pmc_conn,
                            threshold=75.0
                        )

                    # Check pattern/regex entity extraction
                    elif p_name in regex_entities:
                        val = regex_entities[p_name]
                        resolved_val = {"id": val, "label": str(val), "confidence": 1.0}

                    if resolved_val:
                        detected_values[p_name] = DetectedValueDTO(
                            id=resolved_val["id"],
                            label=resolved_val["label"],
                            confidence=resolved_val.get("confidence")
                        )
                    else:
                        missing_placeholders.append(PlaceholderMetadataDTO(**p))

                suggestions.append(
                    SuggestionDTO(
                        template_id=cand["template_id"],
                        intent=cand["intent"],
                        question_template=cand["question_template"],
                        score=cand["score"],
                        detected_values=detected_values,
                        missing_placeholders=missing_placeholders
                    )
                )

        return SuggestQueryResponse(
            query=payload.query,
            suggestions=suggestions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query suggestion error: {str(e)}")
    finally:
        metadata_session.close()
