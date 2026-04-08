from __future__ import annotations

import json
import os
import re
import sys
from statistics import mean
from typing import Any, Dict, List

from openai import OpenAI, OpenAIError

from env import LegalEnv
from models import Action, Observation

# Configuration via environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

PROMPT_TEMPLATE = """You are a legal AI assistant.

Analyze the contract clause.

Return ONLY JSON:

{{
"risk_level": "...",
"risk_type": "...",
"rewrite": "...",
"reason": "..."
}}

Clause:
{clause}"""

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_RISK_TYPES = {"liability", "termination", "payment", "confidentiality", "compliance"}


def extract_json_payload(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if not cleaned: return {}
    try: return json.loads(cleaned)
    except json.JSONDecodeError: pass

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        try: return json.loads(fenced_match.group(1))
        except json.JSONDecodeError: pass

    object_match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
    if object_match:
        try: return json.loads(object_match.group(1))
        except json.JSONDecodeError: pass
    return {}


def safe_action_from_payload(payload: Dict[str, Any]) -> Action:
    risk_level = str(payload.get("risk_level", "")).strip().lower() or None
    risk_type = str(payload.get("risk_type", "")).strip().lower() or None

    return Action(
        risk_level=risk_level if risk_level in VALID_RISK_LEVELS else None,
        risk_type=risk_type if risk_type in VALID_RISK_TYPES else None,
        rewrite=str(payload.get("rewrite", "") or "").strip(),
        reason=str(payload.get("reason", "") or "").strip(),
    )


def analyze_clause(client: OpenAI, observation: Observation) -> Action:
    prompt = PROMPT_TEMPLATE.format(clause=observation.clause)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        content = response.choices[0].message.content or "{}"
        payload = extract_json_payload(content)
        return safe_action_from_payload(payload)
    except OpenAIError as e:
        print(f"LLM Error: {type(e).__name__}: {e}")
        # Return fallback action so the task doesn't crash
        return Action(risk_level=None, risk_type=None, rewrite="", reason="Analysis failed due to LLM error")
    except Exception as e:
        print(f"Unexpected Error in analyze_clause: {type(e).__name__}: {e}")
        return Action(risk_level=None, risk_type=None, rewrite="", reason="Unexpected error")


def run_task(env: LegalEnv, client: OpenAI, task: str) -> float:
    print(f"START: {task}")
    try:
        observation = env.reset(task)
    except Exception as e:
        print(f"Error resetting environment: {e}")
        print(f"END: {task} | score: 0.0000")
        return 0.0

    scores: List[float] = []
    step_index = 0

    while True:
        action = analyze_clause(client, observation)
        try:
            observation, reward, done, _ = env.step(action)
            scores.append(reward.score)
            print(f"STEP: {step_index} | reward: {reward.score:.4f}")
            step_index += 1
            if done: break
        except Exception as e:
            print(f"Error in environment step: {e}")
            break

    final_score = mean(scores) if scores else 0.0
    print(f"END: {task} | score: {final_score:.4f}")
    return final_score


def main() -> None:
    print(f"Inference Config: API_BASE_URL={API_BASE_URL}, MODEL_NAME={MODEL_NAME}")
    if HF_TOKEN:
        print(f"HF_TOKEN present (length: {len(HF_TOKEN)})")
    else:
        print("Warning: HF_TOKEN is NOT set.")

    # Normalize base_url for OpenAI client
    normalized_url = API_BASE_URL
    if not normalized_url.endswith("/v1") and "/v1/" not in normalized_url:
        normalized_url = normalized_url.rstrip("/") + "/v1"

    print(f"Using normalized OpenAI base_url: {normalized_url}")

    try:
        client = OpenAI(
            base_url=normalized_url,
            api_key=HF_TOKEN or "no-token-provided"
        )
        env = LegalEnv()
    except Exception as e:
        print(f"Initialization Error: {e}")
        sys.exit(1)

    task_scores: Dict[str, float] = {}
    for task in env.available_tasks():
        task_scores[task] = run_task(env, client, task)

    average_score = mean(task_scores.values()) if task_scores else 0.0
    print(f"OVERALL_AVERAGE_SCORE: {average_score:.4f}")


if __name__ == "__main__":
    main()
