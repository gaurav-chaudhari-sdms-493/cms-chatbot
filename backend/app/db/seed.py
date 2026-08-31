import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
from app.db.models import Base, QueryTemplate, QueryTemplatePlaceholder

FIXTURE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures/templates_seed.json"))

def load_canonical_templates():
    if os.path.exists(FIXTURE_PATH):
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

CANONICAL_TEMPLATES = load_canonical_templates()

METADATA_DATABASE_URL = os.getenv(
    "SYNC_METADATA_DATABASE_URL",
    os.getenv("METADATA_DATABASE_URL", "postgresql://postgres:postgres_password@localhost:5433/pmc_metadata_db")
)
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/multilingual-e5-base"
)


def seed_database():
    """Create metadata tables, compute embeddings, and seed canonical templates into metadata DB."""
    print(f"Connecting to application metadata database: {METADATA_DATABASE_URL}...")
    engine = create_engine(METADATA_DATABASE_URL, echo=False)

    # 1. Create metadata tables
    print("Creating application metadata tables if not exists...")
    Base.metadata.create_all(bind=engine)

    # 2. Load embedding model
    print(f"Loading SentenceTransformers embedding model '{EMBEDDING_MODEL_NAME}'...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        print(f"Seeding {len(CANONICAL_TEMPLATES)} canonical structural templates...")
        for t_data in CANONICAL_TEMPLATES:
            template_id = t_data["template_id"]

            retrieval_text = t_data["retrieval_text"]
            e5_passage_text = f"passage: {retrieval_text}"
            embedding_vector = model.encode(e5_passage_text, normalize_embeddings=True).tolist()

            existing = session.query(QueryTemplate).filter_by(template_id=template_id).first()
            if existing:
                existing.intent = t_data["intent"]
                existing.question_template = t_data["question_template"]
                existing.retrieval_text = t_data["retrieval_text"]
                existing.sql_template = t_data["sql_template"]
                existing.result_type = t_data.get("result_type", "tabular")
                existing.is_active = t_data.get("is_active", True)
                existing.version = t_data.get("version", 1)
                existing.embedding = embedding_vector
                print(f"  [UPDATED] Template {template_id} ({t_data['intent']})")
            else:
                template_obj = QueryTemplate(
                    template_id=template_id,
                    intent=t_data["intent"],
                    question_template=t_data["question_template"],
                    retrieval_text=t_data["retrieval_text"],
                    sql_template=t_data["sql_template"],
                    result_type=t_data.get("result_type", "tabular"),
                    is_active=t_data.get("is_active", True),
                    version=t_data.get("version", 1),
                    embedding=embedding_vector
                )
                session.add(template_obj)
                print(f"  [INSERTED] Template {template_id} ({t_data['intent']})")

            session.flush()

            session.query(QueryTemplatePlaceholder).filter_by(template_id=template_id).delete()
            for p_data in t_data.get("placeholders", []):
                placeholder_obj = QueryTemplatePlaceholder(
                    template_id=template_id,
                    placeholder_name=p_data["placeholder_name"],
                    data_type=p_data["data_type"],
                    input_mode=p_data.get("input_mode", "searchable_dropdown"),
                    source_table=p_data.get("source_table"),
                    source_id_column=p_data.get("source_id_column"),
                    source_label_column=p_data.get("source_label_column"),
                    required=p_data.get("required", True),
                    display_order=p_data.get("display_order", 1)
                )
                session.add(placeholder_obj)

        session.commit()
        print("Application metadata database seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"ERROR during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
