from __future__ import annotations

import json
import os
import re
from statistics import mean
from typing import Any, Dict, List

from openai import OpenAI

from env import LegalEnv
from models import Action, Observation

PROMPT_TEMPLATE = """You are a legal AI assistant.

Analyze the contract clause.

Return:

* risk_level (low/medium/high)
* risk_type (liability, termination, payment, confidentiality, compliance)
* rewrite (safer clause)
* reason (why risky)

Rules:

* Be realistic and professional
* Do not hallucinate laws
* Keep rewrite enforceable

Return ONLY JSON:

{
"risk_level": "...",
"risk_type": "...",
"rewrite": "...",
"reason": "..."
}

Clause:
{clause}"""

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_RISK_TYPES = {"liability", "termination", "payment", "confidentiality", "compliance"}


def extract_json_payload(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        return {}

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        try:
            return json.loads(fenced_match.group(1))
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(1))
        except json.JSONDecodeError:
            return {}

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
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    payload = extract_json_payload(content)
    return safe_action_from_payload(payload)


def run_task(env: LegalEnv, client: OpenAI, task: str) -> float:
    observation = env.reset(task)
    scores: List[float] = []

    while True:
        action = analyze_clause(client, observation)
        observation, reward, done, _ = env.step(action)
        scores.append(reward.score)
        if done:
            break

    return mean(scores) if scores else 0.0


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    env = LegalEnv()

    task_scores: Dict[str, float] = {}
    for task in env.available_tasks():
        task_scores[task] = run_task(env, client, task)

    for task, score in task_scores.items():
        print(f"{task}_score={score:.4f}")

    average_score = mean(task_scores.values()) if task_scores else 0.0
    print(f"average_score={average_score:.4f}")


if __name__ == "__main__":
    main()
