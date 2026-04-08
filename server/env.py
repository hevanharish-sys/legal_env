from __future__ import annotations

from typing import Any, Dict, List, Tuple

from grader import score_prediction
from models import Action, Observation, Reward, TaskName, TaskSample


class LegalEnv:
    """Production-style OpenEnv environment for legal clause risk analysis."""

    def __init__(self) -> None:
        self._tasks = self._build_tasks()
        self._current_task: TaskName = "easy"
        self._current_index: int = 0
        self._current_observation: Observation = self._tasks["easy"][0].observation

    def available_tasks(self) -> List[str]:
        return list(self._tasks.keys())

    def reset(self, task: str) -> Observation:
        normalized_task = self._normalize_task(task)
        self._current_task = normalized_task
        self._current_index = 0
        self._current_observation = self._tasks[normalized_task][0].observation
        return self._current_observation

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        sample = self._current_sample()
        grading = score_prediction(self._current_task, action, sample.ground_truth)

        current_position = self._current_index
        is_last_sample = current_position >= len(self._tasks[self._current_task]) - 1
        if not is_last_sample:
            self._current_index += 1
            self._current_observation = self._tasks[self._current_task][self._current_index].observation

        info: Dict[str, Any] = {
            "task": self._current_task,
            "sample_id": sample.sample_id,
            "sample_index": current_position,
            "total_samples": len(self._tasks[self._current_task]),
            "ground_truth": sample.ground_truth.model_dump(),
            "grading": grading,
        }
        return self._current_observation, Reward(score=grading["score"]), is_last_sample, info

    def state(self) -> Observation:
        return self._current_observation

    def _current_sample(self) -> TaskSample:
        return self._tasks[self._current_task][self._current_index]

    def _normalize_task(self, task: str) -> TaskName:
        normalized_task = task.strip().lower()
        if normalized_task not in self._tasks:
            available = ", ".join(self._tasks)
            raise ValueError(f"Unsupported task '{task}'. Expected one of: {available}.")
        return normalized_task  # type: ignore[return-value]

    def _build_tasks(self) -> Dict[TaskName, List[TaskSample]]:
        return {
            "easy": [
                TaskSample(
                    sample_id="easy-1",
                    task="easy",
                    observation=Observation(
                        clause="User may terminate the agreement at any time with written notice.",
                        contract_type="SaaS subscription agreement",
                        jurisdiction="New York, USA",
                    ),
                    ground_truth=Action(
                        risk_level="low",
                        risk_type="termination",
                        rewrite="",
                        reason="",
                    ),
                ),
                TaskSample(
                    sample_id="easy-2",
                    task="easy",
                    observation=Observation(
                        clause="All user data must remain confidential and cannot be shared.",
                        contract_type="Software licensing agreement",
                        jurisdiction="California, USA",
                    ),
                    ground_truth=Action(
                        risk_level="medium",
                        risk_type="confidentiality",
                        rewrite="",
                        reason="",
                    ),
                ),
                TaskSample(
                    sample_id="easy-3",
                    task="easy",
                    observation=Observation(
                        clause="The company must comply with all applicable laws.",
                        contract_type="Master services agreement",
                        jurisdiction="England and Wales",
                    ),
                    ground_truth=Action(
                        risk_level="low",
                        risk_type="compliance",
                        rewrite="",
                        reason="",
                    ),
                ),
            ],
            "medium": [
                TaskSample(
                    sample_id="medium-1",
                    task="medium",
                    observation=Observation(
                        clause="Company is not liable for any indirect or direct damages.",
                        contract_type="Enterprise SaaS agreement",
                        jurisdiction="Delaware, USA",
                    ),
                    ground_truth=Action(
                        risk_level="high",
                        risk_type="liability",
                        rewrite="",
                        reason="",
                    ),
                ),
                TaskSample(
                    sample_id="medium-2",
                    task="medium",
                    observation=Observation(
                        clause="Payments once made are non-refundable under any condition.",
                        contract_type="Data processing addendum",
                        jurisdiction="European Union",
                    ),
                    ground_truth=Action(
                        risk_level="high",
                        risk_type="payment",
                        rewrite="",
                        reason="",
                    ),
                ),
                TaskSample(
                    sample_id="medium-3",
                    task="medium",
                    observation=Observation(
                        clause="The agreement may be terminated with 30 days notice.",
                        contract_type="Professional services agreement",
                        jurisdiction="Illinois, USA",
                    ),
                    ground_truth=Action(
                        risk_level="low",
                        risk_type="termination",
                        rewrite="",
                        reason="",
                    ),
                ),
            ],
            "hard": [
                TaskSample(
                    sample_id="hard-1",
                    task="hard",
                    observation=Observation(
                        clause="Company is not responsible for any damages, losses, or claims arising from service use.",
                        contract_type="Cloud platform agreement",
                        jurisdiction="California, USA",
                    ),
                    ground_truth=Action(
                        risk_level="high",
                        risk_type="liability",
                        rewrite="Company liability shall be limited to the extent permitted by applicable law.",
                        reason="The clause removes all liability, which creates significant legal risk.",
                    ),
                ),
                TaskSample(
                    sample_id="hard-2",
                    task="hard",
                    observation=Observation(
                        clause="All payments are final and no refunds will be issued.",
                        contract_type="Implementation services agreement",
                        jurisdiction="England and Wales",
                    ),
                    ground_truth=Action(
                        risk_level="high",
                        risk_type="payment",
                        rewrite="Payments may be refunded in exceptional circumstances subject to company policy.",
                        reason="Strict no-refund policies may be unfair and legally risky.",
                    ),
                ),
                TaskSample(
                    sample_id="hard-3",
                    task="hard",
                    observation=Observation(
                        clause="The company may terminate the agreement at any time without notice.",
                        contract_type="Managed services agreement",
                        jurisdiction="New South Wales, Australia",
                    ),
                    ground_truth=Action(
                        risk_level="medium",
                        risk_type="termination",
                        rewrite="The company may terminate the agreement with reasonable prior notice.",
                        reason="Termination without notice can be considered unfair.",
                    ),
                ),
            ],
        }


if __name__ == "__main__":
    env = LegalEnv()
    observation = env.reset("hard")
    print(observation.model_dump())
