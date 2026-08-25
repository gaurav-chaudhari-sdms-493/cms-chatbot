from fastapi import APIRouter, HTTPException
from app.db.session import get_metadata_session, sync_pmc_engine
from app.schemas.execution import ExecuteQueryRequest, ExecuteQueryResponse
from app.execution.executor import QueryExecutor
from sqlalchemy.orm import sessionmaker

router = APIRouter()


@router.post("/query/execute", response_model=ExecuteQueryResponse)
def execute_query(payload: ExecuteQueryRequest):
    """
    Executes an approved, parameterized structural query template against PMC database.
    """
    metadata_session = get_metadata_session()
    PMC_SessionMaker = sessionmaker(bind=sync_pmc_engine)
    pmc_session = PMC_SessionMaker()

    try:
        result = QueryExecutor.execute_template(
            template_id=payload.template_id,
            parameters=payload.parameters,
            metadata_session=metadata_session,
            pmc_session=pmc_session,
            max_rows=payload.max_rows
        )
        return ExecuteQueryResponse(**result)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")
    finally:
        metadata_session.close()
        pmc_session.close()
