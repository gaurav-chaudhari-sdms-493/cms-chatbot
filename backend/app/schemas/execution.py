from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ExecuteQueryRequest(BaseModel):
    template_id: str = Field(..., example="CMP_010")
    parameters: Dict[str, Any] = Field(default_factory=dict, example={"department_id": 7})
    max_rows: Optional[int] = Field(default=1000, ge=1, le=10000)


class ExecuteQueryResponse(BaseModel):
    status: str
    template_id: str
    execution_time_ms: float
    total_rows: int
    columns: List[str]
    data: List[Dict[str, Any]]
