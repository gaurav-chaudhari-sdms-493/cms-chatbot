import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import metadata_engine, sync_pmc_engine
from sqlalchemy.orm import sessionmaker
from app.agents import MasterOrchestratorAgent

def test_pothole_memory_sequence():
    MetadataSession = sessionmaker(bind=metadata_engine)
    metadata_db = MetadataSession()

    try:
        # Turn 1: Pothole complaints
        print("\n--- TURN 1: User says 'pothole complaints' ---")
        q1 = "pothole complaints"
        res1 = MasterOrchestratorAgent.process_query(
            query_text=q1,
            metadata_session=metadata_db,
            session_history=[]
        )
        print(f"Status: {res1.get('status')}")
        print(f"Content: {res1.get('content')}\n")

        # Turn 2: User says 'yes'
        print("\n--- TURN 2: User says 'yes' ---")
        history_turn2 = [
            {"sender": "user", "content": q1},
            {"sender": "agent", "content": res1.get("content")}
        ]
        q2 = "yes"
        res2 = MasterOrchestratorAgent.process_query(
            query_text=q2,
            metadata_session=metadata_db,
            session_history=history_turn2
        )
        print(f"Status: {res2.get('status')}")
        print(f"SQL Used: {res2.get('sql_used')}")
        print(f"Content:\n{res2.get('content')[:300]}...\n")

        # Turn 3: User says 'all complains'
        print("\n--- TURN 3: User says 'all complains' ---")
        history_turn3 = [
            {"sender": "user", "content": q1},
            {"sender": "agent", "content": res1.get("content")},
            {"sender": "user", "content": q2},
            {"sender": "agent", "content": res2.get("content"), "sql_used": res2.get("sql_used")}
        ]
        q3 = "all complains"
        res3 = MasterOrchestratorAgent.process_query(
            query_text=q3,
            metadata_session=metadata_db,
            session_history=history_turn3
        )
        print(f"Status: {res3.get('status')}")
        print(f"Template ID: {res3.get('template_id')}")
        print(f"SQL Used: {res3.get('sql_used')}")
        print(f"Content:\n{res3.get('content')[:500]}...\n")

    finally:
        metadata_db.close()

if __name__ == "__main__":
    test_pothole_memory_sequence()
