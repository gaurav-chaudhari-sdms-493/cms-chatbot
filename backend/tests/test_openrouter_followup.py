import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import metadata_engine, sync_pmc_engine
from sqlalchemy.orm import sessionmaker
from app.execution.scope_engine import ScopeAnswerEngine

def test_interactive_followup_flow():
    MetadataSession = sessionmaker(bind=metadata_engine)
    PMCSession = sessionmaker(bind=sync_pmc_engine)

    metadata_db = MetadataSession()
    pmc_db = PMCSession()

    try:
        print("\n--- 1. Testing Ambigous / Missing Info Query ---")
        q1 = "Show pending complaints for department"
        res1 = ScopeAnswerEngine.answer_scope_query(
            query_text=q1,
            metadata_session=metadata_db,
            pmc_session=pmc_db
        )
        print(f"Status: {res1.get('status')}")
        print(f"Response Content:\n{res1.get('content')}\n")

        print("\n--- 2. Testing Officer Follow-Up Response ---")
        history = [
            {"sender": "user", "content": q1},
            {"sender": "assistant", "content": res1.get('content')}
        ]
        q2 = "Water Supply"
        res2 = ScopeAnswerEngine.answer_scope_query(
            query_text=q2,
            metadata_session=metadata_db,
            pmc_session=pmc_db,
            session_history=history
        )
        print(f"Status: {res2.get('status')}")
        print(f"Template ID: {res2.get('template_id')}")
        print(f"SQL Used: {res2.get('sql_used')}")
        print(f"Response Content:\n{res2.get('content')[:300]}...\n")

    finally:
        metadata_db.close()
        pmc_db.close()

if __name__ == "__main__":
    test_interactive_followup_flow()
