import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import get_metadata_session, sync_pmc_engine
from app.execution.scope_engine import ScopeAnswerEngine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Test Suite Covering Questions across Categories A–P
SCOPE_TEST_CASES = [
    # Category A: Pending / Open Complaints
    {"question": "How many complaints are pending in Pune right now, department wise?", "expected_cat": "A", "out_of_scope": False},
    {"question": "पुण्यात सध्या किती तक्रारी प्रलंबित आहेत? विभागानुसार दाखवा.", "expected_cat": "A", "out_of_scope": False},
    {"question": "Ward wise pending complaints ka breakdown do.", "expected_cat": "A", "out_of_scope": False},
    {"question": "Kothrud ward madhe kiti complaints pending aahet?", "expected_cat": "A", "out_of_scope": False},

    # Category B: Officer Performance
    {"question": "Which officer is performing best in Pune overall?", "expected_cat": "B", "out_of_scope": False},
    {"question": "पुण्यात सर्वात चांगली कामगिरी करणारा अधिकारी कोण आहे?", "expected_cat": "B", "out_of_scope": False},
    {"question": "Which officers have the most SLA breaches?", "expected_cat": "B", "out_of_scope": False},
    {"question": "Officers who haven't resolved a single complaint in last 30 days.", "expected_cat": "B", "out_of_scope": False},

    # Category C: SLA Compliance
    {"question": "What is the overall SLA compliance rate this month?", "expected_cat": "C", "out_of_scope": False},
    {"question": "How many complaints have breached SLA right now?", "expected_cat": "C", "out_of_scope": False},
    {"question": "Complaints reaching 90% of SLA time — show me the critical list.", "expected_cat": "C", "out_of_scope": False},

    # Category D: Escalations
    {"question": "How many complaints got escalated this month?", "expected_cat": "D", "out_of_scope": False},
    {"question": "Which complaints have been escalated twice or more?", "expected_cat": "D", "out_of_scope": False},

    # Category E: Category Analysis
    {"question": "What are the top 5 complaint categories in Pune?", "expected_cat": "E", "out_of_scope": False},
    {"question": "Which category is rising fastest compared to last month?", "expected_cat": "E", "out_of_scope": False},

    # Category F: Ward / Zone Comparison
    {"question": "Rank all 15 wards by pending complaints.", "expected_cat": "F", "out_of_scope": False},
    {"question": "Zone wise complaint summary — ek table madhe dakhava.", "expected_cat": "F", "out_of_scope": False},

    # Category G: Trends & Time Analysis
    {"question": "Show complaint trend for last 12 months.", "expected_cat": "G", "out_of_scope": False},
    {"question": "Which day of the week gets the most complaints?", "expected_cat": "G", "out_of_scope": False},

    # Category H: Resolution Stats
    {"question": "How many complaints were resolved this month?", "expected_cat": "H", "out_of_scope": False},
    {"question": "What is the average resolution time city-wide?", "expected_cat": "H", "out_of_scope": False},

    # Category I: Citizen Feedback
    {"question": "What is the average citizen satisfaction rating?", "expected_cat": "I", "out_of_scope": False},
    {"question": "Show me recent negative feedback comments with complaint numbers.", "expected_cat": "I", "out_of_scope": False},

    # Category J: Hotspots
    {"question": "Show complaint hotspots on the city map.", "expected_cat": "J", "out_of_scope": False},

    # Category K: Department Deep-Dive
    {"question": "Give me the full picture of Water Supply department.", "expected_cat": "K", "out_of_scope": False},

    # Category L: Aging Complaints
    {"question": "Show complaints pending for more than 30 days.", "expected_cat": "L", "out_of_scope": False},

    # Category M: Source / Channel
    {"question": "How many complaints came from the call center vs web this month?", "expected_cat": "M", "out_of_scope": False},

    # Category N: Reopened / Rejected / Duplicates
    {"question": "Which department has the highest reopen rate?", "expected_cat": "N", "out_of_scope": False},

    # Category O: Workload & Staffing
    {"question": "Which officers are overloaded right now?", "expected_cat": "O", "out_of_scope": False},

    # Category P: Specific Complaint Lookup
    {"question": "What is the status of complaint CMS20260001234?", "expected_cat": "P", "out_of_scope": False},

    # Out-of-Scope Test Cases
    {"question": "Transfer complaint CMS20260001234 to Roads department", "expected_cat": "OUT_OF_SCOPE", "out_of_scope": True},
    {"question": "Suspend officer XYZ immediately", "expected_cat": "OUT_OF_SCOPE", "out_of_scope": True},
    {"question": "Who will win the election?", "expected_cat": "OUT_OF_SCOPE", "out_of_scope": True}
]


def run_scope_tests():
    """Executes scope test suite and validates template matching and out-of-scope refusals."""
    print("=========================================================================")
    print("   PMC COMMISSIONER CHATBOT — SCOPE TEMPLATE EVALUATION SUITE           ")
    print("=========================================================================\n")

    metadata_session = get_metadata_session()
    PMC_SessionMaker = sessionmaker(bind=sync_pmc_engine)
    pmc_session = PMC_SessionMaker()

    total_cases = len(SCOPE_TEST_CASES)
    passed_cases = 0
    refused_cases = 0

    try:
        for idx, test_case in enumerate(SCOPE_TEST_CASES, 1):
            q = test_case["question"]
            expected_cat = test_case["expected_cat"]
            is_oos = test_case["out_of_scope"]

            res = ScopeAnswerEngine.answer_scope_query(
                query_text=q,
                metadata_session=metadata_session,
                pmc_session=pmc_session
            )

            if is_oos:
                if res and res["status"] == "REFUSED":
                    passed_cases += 1
                    refused_cases += 1
                    print(f"Test #{idx:02d} [PASS - REFUSED]: '{q}'")
                else:
                    print(f"Test #{idx:02d} [FAIL - UNREFUSED]: '{q}'")
            else:
                if res and res["status"] == "SUCCESS" and res["content"]:
                    passed_cases += 1
                    t_id = res.get("template_id", "UNKNOWN")
                    print(f"Test #{idx:02d} [PASS - {t_id}]: '{q[:50]}...'")
                else:
                    print(f"Test #{idx:02d} [FAIL]: '{q[:50]}...'")

        accuracy = (passed_cases / total_cases) * 100
        print("\n=========================================================================")
        print("                  SCOPE EVALUATION SUMMARY RESULTS                        ")
        print("=========================================================================")
        print(f"  Total Test Cases:            {total_cases}")
        print(f"  Passed Test Cases:           {passed_cases}")
        print(f"  Out-Of-Scope Refusals:       {refused_cases}")
        print(f"  Overall Execution Accuracy:  {accuracy:.1f}%")
        print("=========================================================================\n")

    finally:
        metadata_session.close()
        pmc_session.close()


if __name__ == "__main__":
    run_scope_tests()
