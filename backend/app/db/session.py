import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Remote PMC Read-Only Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://cms-readonly-user:rfwxwbwyeue@115.160.211.220:2419/pmc_cms_new1"
)
SYNC_DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql://cms-readonly-user:rfwxwbwyeue@115.160.211.220:2419/pmc_cms_new1"
)

# Local Application Metadata Database (Containerized PostgreSQL)
METADATA_DATABASE_URL = os.getenv(
    "METADATA_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_password@localhost:5433/pmc_metadata_db"
)
SYNC_METADATA_DATABASE_URL = os.getenv(
    "SYNC_METADATA_DATABASE_URL",
    "postgresql://postgres:postgres_password@localhost:5433/pmc_metadata_db"
)

# 1. Sync & Async Engines for Remote PMC DB
async_pmc_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

sync_pmc_engine = create_engine(SYNC_DATABASE_URL, echo=False)

# 2. Metadata DB Engine (PostgreSQL)
metadata_engine = create_engine(SYNC_METADATA_DATABASE_URL, echo=False, pool_pre_ping=True)
MetadataSessionLocal = sessionmaker(bind=metadata_engine)


def get_metadata_session():
    """Obtain a synchronous session for local application metadata DB."""
    session = MetadataSessionLocal()
    try:
        return session
    finally:
        pass


def get_metadata_db():
    """FastAPI dependency yielding a metadata DB session."""
    db = MetadataSessionLocal()
    try:
        yield db
    finally:
        db.close()



def check_sync_db_connection() -> dict:
    """Check connectivity to remote PMC database and local metadata database."""
    with sync_pmc_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM department_master;"))
        dept_count = result.scalar()

        ext_result = conn.execute(text("SELECT extname FROM pg_extension;"))
        extensions = [r[0] for r in ext_result.fetchall()]

    metadata_status = "healthy"
    try:
        with metadata_engine.connect() as meta_conn:
            meta_conn.execute(text("SELECT 1;"))
    except Exception as err:
        metadata_status = f"unhealthy: {str(err)}"

    return {
        "status": "healthy" if metadata_status == "healthy" else "degraded",
        "department_master_rows": dept_count,
        "installed_extensions": extensions,
        "metadata_database": metadata_status
    }
