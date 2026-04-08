import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

TEST_CASES = {
    "easy": [
        {
            "clause": "User may terminate the agreement at any time with written notice.",
            "action": {"risk_level": "low", "risk_type": "termination", "rewrite": "", "reason": ""}
        },
        {
            "clause": "All user data must remain confidential and cannot be shared.",
            "action": {"risk_level": "medium", "risk_type": "confidentiality", "rewrite": "", "reason": ""}
        },
        {
            "clause": "The company must comply with all applicable laws.",
            "action": {"risk_level": "low", "risk_type": "compliance", "rewrite": "", "reason": ""}
        }
    ],
    "medium": [
        {
            "clause": "Company is not liable for any indirect or direct damages.",
            "action": {"risk_level": "high", "risk_type": "liability", "rewrite": "", "reason": ""}
        },
        {
            "clause": "Payments once made are non-refundable under any condition.",
            "action": {"risk_level": "high", "risk_type": "payment", "rewrite": "", "reason": ""}
        },
        {
            "clause": "The agreement may be terminated with 30 days notice.",
            "action": {"risk_level": "low", "risk_type": "termination", "rewrite": "", "reason": ""}
        }
    ],
    "hard": [
        {
            "clause": "Company is not responsible for any damages, losses, or claims arising from service use.",
            "action": {
                "risk_level": "high",
                "risk_type": "liability",
                "rewrite": "Company liability shall be limited to the extent permitted by applicable law.",
                "reason": "The clause removes all liability, which creates significant legal risk."
            }
        },
        {
            "clause": "All payments are final and no refunds will be issued.",
            "action": {
                "risk_level": "high",
                "risk_type": "payment",
                "rewrite": "Payments may be refunded in exceptional circumstances subject to company policy.",
                "reason": "Strict no-refund policies may be unfair and legally risky."
            }
        },
        {
            "clause": "The company may terminate the agreement at any time without notice.",
            "action": {
                "risk_level": "medium",
                "risk_type": "termination",
                "rewrite": "The company may terminate the agreement with reasonable prior notice.",
                "reason": "Termination without notice can be considered unfair."
            }
        }
    ]
}

def run_tests():
    for task, cases in TEST_CASES.items():
        print(f"\n--- Testing Task: {task.upper()} ---")
        # Reset environment
        resp = requests.get(f"{API_BASE_URL}/reset?task={task}")
        if resp.status_code != 200:
            print(f"Failed to reset task {task}: {resp.text}")
            continue
        
        for i, case in enumerate(cases):
            print(f"Case {i+1}: {case['clause'][:50]}...")
            resp = requests.post(f"{API_BASE_URL}/step", json=case['action'])
            if resp.status_code != 200:
                print(f"  Error: {resp.text}")
                continue
            
            data = resp.json()
            score = data['reward']['score']
            grading = data['info']['grading']
            print(f"  Score: {score}")
            if score < 1.0:
                print(f"  Grading Details: {json.dumps(grading['breakdown'], indent=2)}")
                print(f"  Missing Fields: {grading['missing_fields']}")

if __name__ == "__main__":
    run_tests()
