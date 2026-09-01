from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SuggestQueryRequest(BaseModel):
    query: str = Field(..., example="How many pending complaints in Road department?")
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    threshold: Optional[float] = Field(default=0.65, ge=0.0, le=1.0)


class DetectedValueDTO(BaseModel):
    id: Any
    label: str
    confidence: Optional[float] = None


class PlaceholderMetadataDTO(BaseModel):
    placeholder_name: str
    data_type: str
    input_mode: str
    source_table: Optional[str] = None
    source_id_column: Optional[str] = None
    source_label_column: Optional[str] = None
    required: bool = True
    display_order: int = 1


class SuggestionDTO(BaseModel):
    template_id: str
    intent: str
    question_template: str
    score: float
    detected_values: Dict[str, DetectedValueDTO]
    missing_placeholders: List[PlaceholderMetadataDTO]


class SuggestQueryResponse(BaseModel):
    query: str
    suggestions: List[SuggestionDTO]


class PlaceholderConfigPayload(BaseModel):
    placeholder_name: str
    data_type: str  # REFERENCE, ENUM, INTEGER, DATE_RANGE
    input_mode: str = "searchable_dropdown"
    source_table: Optional[str] = None
    source_id_column: Optional[str] = None
    source_label_column: Optional[str] = None
    required: bool = True
    display_order: int = 1


class QueryTemplateCreate(BaseModel):
    template_id: str = Field(..., example="CMP_099")
    intent: str = Field(..., example="complaints_by_department_and_ward")
    question_template: str = Field(..., example="How many complaints in {department} for {ward}?")
    retrieval_text: str = Field(..., example="count complaints filtered by department and ward")
    sql_template: str = Field(..., example="SELECT COUNT(*) FROM complaint_master WHERE department_id = :department_id AND ward_id = :ward_id")
    result_type: str = "tabular"
    is_active: bool = True
    is_verified: bool = True
    version: int = 1
    placeholders: List[PlaceholderConfigPayload] = []


class QueryTemplateUpdate(BaseModel):
    intent: Optional[str] = None
    question_template: Optional[str] = None
    retrieval_text: Optional[str] = None
    sql_template: Optional[str] = None
    result_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    version: Optional[int] = None
    placeholders: Optional[List[PlaceholderConfigPayload]] = None


class QueryTemplateDetailResponse(BaseModel):
    template_id: str
    intent: str
    question_template: str
    retrieval_text: str
    sql_template: str
    result_type: str
    is_active: bool
    is_verified: bool
    version: int
    has_embedding: bool
    placeholders: List[PlaceholderMetadataDTO]

    class Config:
        from_attributes = True
