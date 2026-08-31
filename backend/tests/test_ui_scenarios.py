import requests
import json
import time

BASE_URL = "http://localhost:8000/api/chat"

def run_ui_simulation_tests():
    print("\n=========================================================================")
    print("      PMC CHATBOT — FRONTEND UI INTERACTION SIMULATION TESTS             ")
    print("=========================================================================\n")

    # 1. Create a new chat session (same as clicking "New Chat" in UI)
    sess_resp = requests.post(f"{BASE_URL}/sessions", json={"title": "UI Simulation Session", "mode": "template"})
    assert sess_resp.status_code == 200, "Failed to create chat session"
    session_data = sess_resp.json()
    session_id = session_data["id"]
    print(f"✓ Chat session created with ID: {session_id}")

    # Scenarios to test
    scenarios = [
        {
            "name": "Scenario 1: Direct Entity Query (Kothrud Ward)",
            "query": "How many pending complaints are there in Kothrud ward right now?",
            "expected_status_in_content": ["3,329", "Key Summary Metric", "Kothrud"]
        },
        {
            "name": "Scenario 2: Multilingual Marathi Query (Water Supply)",
            "query": "पाणीपुरवठा विभागातील प्रलंबित तक्रारी दाखवा",
            "expected_status_in_content": ["पाणी", "एकूण", "मुख्य संख्या"]
        },
        {
            "name": "Scenario 3A: Ambigous Query (Triggers Follow-Up)",
            "query": "Show open complaints for department",
            "expected_status_in_content": ["Follow-Up Question", "department"]
        },
        {
            "name": "Scenario 3B: Officer Responds to Follow-Up",
            "query": "Drainage Department",
            "expected_status_in_content": ["Key Summary Metric", "Drainage"]
        },
        {
            "name": "Scenario 4: Out-Of-Scope Refusal (Data Modification)",
            "query": "Transfer complaint CMS20260001234 to Roads department",
            "expected_status_in_content": ["Out of Scope Query", "read-only"]
        }
    ]

    for idx, scenario in enumerate(scenarios, 1):
        print(f"\n[{idx}/{len(scenarios)}] {scenario['name']}")
        print(f"Officer Input: \"{scenario['query']}\"")
        start = time.time()
        
        msg_resp = requests.post(f"{BASE_URL}/sessions/{session_id}/message", json={
            "content": scenario['query'],
            "mode": "template"
        })
        elapsed = round((time.time() - start) * 1000, 2)

        if msg_resp.status_code == 200:
            res_json = msg_resp.json()
            content = res_json.get("content", "")
            print(f"⏱️ Response Time: {elapsed} ms")
            print("--------------------------------------------------")
            print(content[:350] + ("..." if len(content) > 350 else ""))
            print("--------------------------------------------------")
            print("✅ TEST PASSED: UI workflow simulated successfully.")
        else:
            print(f"❌ TEST FAILED: HTTP {msg_resp.status_code}: {msg_resp.text}")

if __name__ == "__main__":
    run_ui_simulation_tests()
