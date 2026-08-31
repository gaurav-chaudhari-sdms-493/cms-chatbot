from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.db.session import get_metadata_session
from app.db.models import QueryTemplate, QueryTemplatePlaceholder
from app.schemas.query import (
    QueryTemplateCreate,
    QueryTemplateUpdate,
    QueryTemplateDetailResponse,
    PlaceholderMetadataDTO
)
from app.retrieval.embedder import embedding_service
from app.execution.validator import SQLSafetyValidator

router = APIRouter()


def _format_template_response(template: QueryTemplate) -> dict:
    placeholders = [
        PlaceholderMetadataDTO(
            placeholder_name=p.placeholder_name,
            data_type=p.data_type,
            input_mode=p.input_mode,
            source_table=p.source_table,
            source_id_column=p.source_id_column,
            source_label_column=p.source_label_column,
            required=p.required,
            display_order=p.display_order
        )
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
        "has_embedding": bool(template.embedding),
        "placeholders": placeholders
    }


@router.get("/templates", response_model=List[QueryTemplateDetailResponse])
@router.get("/admin/templates", response_model=List[QueryTemplateDetailResponse])
def list_templates(q: Optional[str] = Query(None, description="Search term for template ID, intent, or question")):
    """List all query templates in the metadata database."""
    session: Session = get_metadata_session()
    try:
        query = session.query(QueryTemplate)
        if q:
            search_pattern = f"%{q.strip()}%"
            query = query.filter(
                (QueryTemplate.template_id.ilike(search_pattern)) |
                (QueryTemplate.intent.ilike(search_pattern)) |
                (QueryTemplate.question_template.ilike(search_pattern)) |
                (QueryTemplate.retrieval_text.ilike(search_pattern))
            )
        templates = query.order_by(QueryTemplate.template_id).all()
        return [_format_template_response(t) for t in templates]
    finally:
        session.close()


@router.get("/templates/{template_id}", response_model=QueryTemplateDetailResponse)
@router.get("/admin/templates/{template_id}", response_model=QueryTemplateDetailResponse)
def get_template(template_id: str):
    """Fetch details of a single query template."""
    session: Session = get_metadata_session()
    try:
        template = session.query(QueryTemplate).filter_by(template_id=template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
        return _format_template_response(template)
    finally:
        session.close()


@router.post("/templates", response_model=QueryTemplateDetailResponse, status_code=201)
@router.post("/admin/templates", response_model=QueryTemplateDetailResponse, status_code=201)
def create_template(payload: QueryTemplateCreate):
    """Create a new structural query template and generate its vector embedding."""
    session: Session = get_metadata_session()
    try:
        # Check uniqueness
        existing = session.query(QueryTemplate).filter_by(template_id=payload.template_id.strip()).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Template ID '{payload.template_id}' already exists.")

        # SQL Safety Check
        if not SQLSafetyValidator.validate_sql(payload.sql_template):
            raise HTTPException(status_code=400, detail="SQL statement failed safety validation rules (only SELECT statements are allowed).")

        # Generate embedding vector
        embedding_vector = embedding_service.generate_embedding(payload.retrieval_text, is_query=False)

        template_obj = QueryTemplate(
            template_id=payload.template_id.strip(),
            intent=payload.intent.strip(),
            question_template=payload.question_template.strip(),
            retrieval_text=payload.retrieval_text.strip(),
            sql_template=payload.sql_template.strip(),
            result_type=payload.result_type,
            is_active=payload.is_active,
            version=payload.version,
            embedding=embedding_vector
        )
        session.add(template_obj)
        session.flush()

        # Add placeholders
        for p in payload.placeholders:
            placeholder_obj = QueryTemplatePlaceholder(
                template_id=template_obj.template_id,
                placeholder_name=p.placeholder_name.strip(),
                data_type=p.data_type,
                input_mode=p.input_mode,
                source_table=p.source_table,
                source_id_column=p.source_id_column,
                source_label_column=p.source_label_column,
                required=p.required,
                display_order=p.display_order
            )
            session.add(placeholder_obj)

        session.commit()
        session.refresh(template_obj)
        return _format_template_response(template_obj)
    except HTTPException:
        session.rollback()
        raise
    except Exception as err:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(err)}")
    finally:
        session.close()


@router.put("/templates/{template_id}", response_model=QueryTemplateDetailResponse)
@router.put("/admin/templates/{template_id}", response_model=QueryTemplateDetailResponse)
def update_template(template_id: str, payload: QueryTemplateUpdate):
    """Update an existing structural query template and re-compute its embedding if modified."""
    session: Session = get_metadata_session()
    try:
        template = session.query(QueryTemplate).filter_by(template_id=template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")

        # Update SQL template with safety check if provided
        if payload.sql_template is not None:
            if not SQLSafetyValidator.validate_sql(payload.sql_template):
                raise HTTPException(status_code=400, detail="SQL statement failed safety validation rules.")
            template.sql_template = payload.sql_template.strip()

        if payload.intent is not None:
            template.intent = payload.intent.strip()
        if payload.question_template is not None:
            template.question_template = payload.question_template.strip()
        if payload.result_type is not None:
            template.result_type = payload.result_type
        if payload.is_active is not None:
            template.is_active = payload.is_active
        if payload.version is not None:
            template.version = payload.version

        # Re-compute embedding if retrieval_text changed or embedding missing
        if payload.retrieval_text is not None:
            template.retrieval_text = payload.retrieval_text.strip()
            template.embedding = embedding_service.generate_embedding(template.retrieval_text, is_query=False)

        # Update placeholders if provided
        if payload.placeholders is not None:
            session.query(QueryTemplatePlaceholder).filter_by(template_id=template_id).delete()
            for p in payload.placeholders:
                placeholder_obj = QueryTemplatePlaceholder(
                    template_id=template_id,
                    placeholder_name=p.placeholder_name.strip(),
                    data_type=p.data_type,
                    input_mode=p.input_mode,
                    source_table=p.source_table,
                    source_id_column=p.source_id_column,
                    source_label_column=p.source_label_column,
                    required=p.required,
                    display_order=p.display_order
                )
                session.add(placeholder_obj)

        session.commit()
        session.refresh(template)
        return _format_template_response(template)
    except HTTPException:
        session.rollback()
        raise
    except Exception as err:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(err)}")
    finally:
        session.close()


@router.delete("/admin/templates/{template_id}")
def delete_template(template_id: str):
    """Delete a query template from the metadata database."""
    session: Session = get_metadata_session()
    try:
        template = session.query(QueryTemplate).filter_by(template_id=template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")

        session.delete(template)
        session.commit()
        return {"status": "SUCCESS", "message": f"Template '{template_id}' deleted successfully."}
    except Exception as err:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(err)}")
    finally:
        session.close()
