from fastapi import APIRouter
from app.db.session import check_sync_db_connection

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint validating database connectivity and API status."""
    try:
        db_status = check_sync_db_connection()
        return {
            "status": "healthy",
            "service": "PMC Officer Query System API",
            "version": "1.0.0-poc",
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "PMC Officer Query System API",
            "error": str(e)
        }
