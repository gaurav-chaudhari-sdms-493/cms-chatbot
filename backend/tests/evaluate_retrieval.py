import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import get_metadata_session
from app.db.models import TemplateTestCase, Base, QueryTemplate
from app.schemas.query import SuggestQueryRequest
from app.api.suggest import suggest_templates

load_dotenv()

# Held-Out Paraphrase Evaluation Test Cases
EVALUATION_TEST_CASES = [
    # CMP_001: citywide_pending_complaints_count
    {"nl_question": "What is the total open grievance count across the city?", "expected": "CMP_001"},
    {"nl_question": "Give me the total unresolved backlog in PMC.", "expected": "CMP_001"},
    {"nl_question": "How many grievances are currently active citywide?", "expected": "CMP_001"},

    # CMP_010: pending_complaints_by_department
    {"nl_question": "How many complaints are still open in Road department?", "expected": "CMP_010"},
    {"nl_question": "What is the pending count for Water Supply dept?", "expected": "CMP_010"},
    {"nl_question": "Show total unresolved issues in Drainage department.", "expected": "CMP_010"},

    # CMP_020: pending_complaints_by_ward
    {"nl_question": "How many pending issues in Kothrud ward office?", "expected": "CMP_020"},
    {"nl_question": "Show open complaints for Hadapsar ward.", "expected": "CMP_020"},

    # CMP_030: pending_complaints_by_category
    {"nl_question": "How many unresolved grievances for Potholes?", "expected": "CMP_030"},
    {"nl_question": "Total pending count for Garbage Dumping category.", "expected": "CMP_030"},

    # CMP_040: sla_breached_complaints_count
    {"nl_question": "How many complaints have passed their deadline citywide?", "expected": "CMP_040"},
    {"nl_question": "Show total count of late overdue complaints in PMC.", "expected": "CMP_040"},

    # CMP_050: department_pending_in_ward
    {"nl_question": "How many open Road complaints in Aundh ward?", "expected": "CMP_050"},
    {"nl_question": "Show unresolved Drainage issues in Kothrud-Bavdhan ward.", "expected": "CMP_050"},
]


def run_evaluation():
    """Executes held-out test suite and computes Top-1 & Top-3 retrieval accuracy."""
    print("=========================================================")
    print("   PMC OFFICER QUERY SYSTEM — RETRIEVAL EVALUATION       ")
    print("=========================================================\n")

    session = get_metadata_session()
    
    # 1. Seed held-out test cases into template_test_cases table
    print(f"Populating {len(EVALUATION_TEST_CASES)} held-out paraphrase test cases...")
    session.query(TemplateTestCase).delete()
    for case in EVALUATION_TEST_CASES:
        obj = TemplateTestCase(
            nl_question=case["nl_question"],
            expected_template_id=case["expected"]
        )
        session.add(obj)
    session.commit()

    # 2. Run Evaluation
    total_cases = len(EVALUATION_TEST_CASES)
    top1_correct = 0
    top3_correct = 0
    wrong_template_executions = 0

    print("\nRunning Evaluation Suite against Retrieval Engine...\n")
    
    for idx, case in enumerate(EVALUATION_TEST_CASES, 1):
        q = case["nl_question"]
        expected_id = case["expected"]
        
        req = SuggestQueryRequest(query=q, top_k=3, threshold=0.50)
        res = suggest_templates(req)
        
        retrieved_ids = [s.template_id for s in res.suggestions]
        top1_id = retrieved_ids[0] if retrieved_ids else None
        
        is_top1 = (top1_id == expected_id)
        is_top3 = (expected_id in retrieved_ids)

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1
        else:
            wrong_template_executions += 1

        status_str = "TOP-1 PASS" if is_top1 else ("TOP-3 PASS" if is_top3 else "FAIL")
        print(f"Test #{idx:02d} [{status_str}]: '{q}'")
        print(f"  Expected: {expected_id} | Retrieved: {retrieved_ids}")

    # 3. Calculate Accuracy Percentages
    top1_acc = (top1_correct / total_cases) * 100
    top3_acc = (top3_correct / total_cases) * 100
    wrong_exec_rate = (wrong_template_executions / total_cases) * 100

    print("\n=========================================================")
    print("                  EVALUATION SUMMARY RESULTS             ")
    print("=========================================================")
    print(f"  Total Test Cases:            {total_cases}")
    print(f"  Top-1 Retrieval Accuracy:    {top1_acc:.1f}%  (Target: >= 75.0%)")
    print(f"  Top-3 Retrieval Accuracy:    {top3_acc:.1f}%  (Target: >= 90.0%)")
    print(f"  Wrong-Template Exec Rate:    {wrong_exec_rate:.1f}%  (Target: 0.0%)")
    print("=========================================================")

    if top3_acc >= 90.0:
        print("\nDECISION GATE: GO (Core hypothesis validated!)")
    else:
        print("\nDECISION GATE: CONDITIONAL (Tuning required)")

    session.close()


if __name__ == "__main__":
    run_evaluation()
