from __future__ import annotations

from typing import Any, Dict, Mapping

from models import Action

RISK_LEVEL_WEIGHT = 0.4
RISK_TYPE_WEIGHT = 0.3
REWRITE_WEIGHT = 0.2
REASON_WEIGHT = 0.1

REWRITE_KEYWORDS = {
    "reasonable",
    "subject to law",
    "limitation",
    "exception",
    "applicable law",
}
REASON_KEYWORDS = {
    "risk",
    "liability",
    "unfair",
    "legal",
}

TASK_FIELDS = {
    "easy": ("risk_type",),
    "medium": ("risk_type", "risk_level"),
    "hard": ("risk_type", "risk_level", "rewrite", "reason"),
}
FIELD_WEIGHTS = {
    "risk_level": RISK_LEVEL_WEIGHT,
    "risk_type": RISK_TYPE_WEIGHT,
    "rewrite": REWRITE_WEIGHT,
    "reason": REASON_WEIGHT,
}


def _to_prediction_dict(action: Action | Mapping[str, Any] | None) -> Dict[str, Any]:
    if action is None:
        payload: Dict[str, Any] = {}
    elif isinstance(action, Action):
        payload = action.model_dump()
    elif isinstance(action, Mapping):
        payload = dict(action)
    else:
        payload = {
            "risk_level": getattr(action, "risk_level", None),
            "risk_type": getattr(action, "risk_type", None),
            "rewrite": getattr(action, "rewrite", ""),
            "reason": getattr(action, "reason", ""),
        }

    return {
        "risk_level": _normalize_label(payload.get("risk_level")),
        "risk_type": _normalize_label(payload.get("risk_type")),
        "rewrite": _normalize_text(payload.get("rewrite")),
        "reason": _normalize_text(payload.get("reason")),
    }


def _normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _count_keyword_hits(text: str, keywords: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def _rewrite_quality_score(rewrite: str) -> float:
    if not rewrite:
        return 0.0
    hits = _count_keyword_hits(rewrite, REWRITE_KEYWORDS)
    return min(hits / 2.0, 1.0)


def _reason_quality_score(reason: str) -> float:
    if not reason:
        return 0.0
    hits = _count_keyword_hits(reason, REASON_KEYWORDS)
    return min(hits / 2.0, 1.0)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _clip_score(score: float) -> float:
    # Ensure score is strictly in (0, 1) range (not 0 or 1) per validator requirement
    return max(0.01, min(0.99, round(score, 4)))


def score_prediction(
    task: str,
    prediction: Action | Mapping[str, Any] | None,
    ground_truth: Action | Mapping[str, Any],
) -> Dict[str, Any]:
    normalized_task = task.strip().lower()
    if normalized_task not in TASK_FIELDS:
        raise ValueError(f"Unsupported task '{task}'. Expected one of: {', '.join(TASK_FIELDS)}.")

    required_fields = TASK_FIELDS[normalized_task]
    pred = _to_prediction_dict(prediction)
    truth = _to_prediction_dict(ground_truth)

    raw_positive = 0.0
    breakdown: Dict[str, float] = {
        "risk_level": 0.0,
        "risk_type": 0.0,
        "rewrite": 0.0,
        "reason": 0.0,
    }

    if "risk_level" in required_fields and pred["risk_level"] == truth["risk_level"]:
        breakdown["risk_level"] = RISK_LEVEL_WEIGHT
        raw_positive += RISK_LEVEL_WEIGHT

    if "risk_type" in required_fields and pred["risk_type"] == truth["risk_type"]:
        breakdown["risk_type"] = RISK_TYPE_WEIGHT
        raw_positive += RISK_TYPE_WEIGHT

    if "rewrite" in required_fields:
        breakdown["rewrite"] = round(REWRITE_WEIGHT * _rewrite_quality_score(pred["rewrite"]), 4)
        raw_positive += breakdown["rewrite"]

    if "reason" in required_fields:
        breakdown["reason"] = round(REASON_WEIGHT * _reason_quality_score(pred["reason"]), 4)
        raw_positive += breakdown["reason"]

    active_weight_total = sum(FIELD_WEIGHTS[field] for field in required_fields)
    normalized_positive = raw_positive / active_weight_total if active_weight_total else 0.0

    missing_fields = [field for field in required_fields if _is_missing(pred[field])]
    penalty = 0.2 * len(missing_fields)

    if all(_is_missing(pred[field]) for field in required_fields):
        penalty += 0.3

    final_score = _clip_score(normalized_positive - penalty)

    return {
        "score": final_score,
        "task": normalized_task,
        "required_fields": list(required_fields),
        "missing_fields": missing_fields,
        "raw_positive": round(raw_positive, 4),
        "normalized_positive": round(normalized_positive, 4),
        "penalty": round(penalty, 4),
        "breakdown": breakdown,
    }


def _grade(task: str, prediction: Action | Mapping[str, Any] | None, ground_truth: Action | Mapping[str, Any]) -> float:
    return score_prediction(task=task, prediction=prediction, ground_truth=ground_truth)["score"]


def grade_easy(prediction: Action | Mapping[str, Any] | None, ground_truth: Action | Mapping[str, Any]) -> float:
    return _grade("easy", prediction, ground_truth)


def grade_medium(prediction: Action | Mapping[str, Any] | None, ground_truth: Action | Mapping[str, Any]) -> float:
    return _grade("medium", prediction, ground_truth)


def grade_hard(prediction: Action | Mapping[str, Any] | None, ground_truth: Action | Mapping[str, Any]) -> float:
    return _grade("hard", prediction, ground_truth)
