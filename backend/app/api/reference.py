from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.db.session import sync_pmc_engine

router = APIRouter()

APPROVED_MASTER_TABLES = {
    "department_master": ("id", "department_name"),
    "ward_master": ("id", "ward_name"),
    "category_master": ("id", "category_name"),
    "sub_category_master": ("id", "sub_category_name"),
    "status_master": ("id", "status_name"),
    "zone_master": ("id", "zone_name"),
    "prabhag_master": ("id", "prabhag_name")
}


@router.get("/reference/{source_table}")
def get_reference_options(source_table: str, q: Optional[str] = Query(None)):
    """
    Returns valid categorical options from database master tables for UI dropdown controls.
    """
    if source_table not in APPROVED_MASTER_TABLES:
        raise HTTPException(status_code=400, detail=f"Table '{source_table}' is not an approved reference source.")

    id_col, label_col = APPROVED_MASTER_TABLES[source_table]
    
    with sync_pmc_engine.connect() as conn:
        if q and q.strip():
            sql = text(f"SELECT {id_col}, {label_col} FROM {source_table} WHERE LOWER({label_col}) LIKE :q ORDER BY {label_col} ASC LIMIT 100;")
            records = conn.execute(sql, {"q": f"%{q.strip().lower()}%"}).fetchall()
        else:
            sql = text(f"SELECT {id_col}, {label_col} FROM {source_table} ORDER BY {label_col} ASC LIMIT 500;")
            records = conn.execute(sql).fetchall()

        options = [{"id": r[0], "label": str(r[1])} for r in records]
        return {
            "source_table": source_table,
            "total": len(options),
            "options": options
        }
