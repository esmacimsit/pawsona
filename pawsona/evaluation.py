from __future__ import annotations

from dataclasses import dataclass

from pawsona.behavior import Scenario, choose_action, score_actions
from pawsona.pet import Pet
from pawsona.training import SCENARIOS


@dataclass(frozen=True)
class EvaluationCase:
    metric: str
    scenario: Scenario
    expected_action: str


@dataclass(frozen=True)
class EvaluationResult:
    metric: str
    scenario_name: str
    expected_action: str
    chosen_action: str
    score: int


@dataclass(frozen=True)
class EvaluationReport:
    results: tuple[EvaluationResult, ...]
    overall_score: int


SCENARIOS_BY_NAME = {scenario.name: scenario for scenario in SCENARIOS}

EVALUATION_CASES = (
    EvaluationCase(
        metric="Recall Accuracy",
        scenario=SCENARIOS_BY_NAME["recall_from_yard"],
        expected_action="return_to_owner",
    ),
    EvaluationCase(
        metric="Focus Score",
        scenario=SCENARIOS_BY_NAME["focus_near_food"],
        expected_action="return_to_owner",
    ),
    EvaluationCase(
        metric="Calm Greeting Score",
        scenario=SCENARIOS_BY_NAME["owner_arrives_home"],
        expected_action="observe_calmly",
    ),
)


def evaluate_pet(pet: Pet) -> EvaluationReport:
    results = tuple(_evaluate_case(pet, case) for case in EVALUATION_CASES)
    overall = round(sum(result.score for result in results) / len(results))
    return EvaluationReport(results=results, overall_score=overall)


def _evaluate_case(pet: Pet, case: EvaluationCase) -> EvaluationResult:
    chosen_action, _chosen_scores = choose_action(pet, case.scenario)
    scores = score_actions(pet, case.scenario)
    return EvaluationResult(
        metric=case.metric,
        scenario_name=case.scenario.name,
        expected_action=case.expected_action,
        chosen_action=chosen_action,
        score=score_expected_action(scores, case.expected_action),
    )


def score_expected_action(scores: dict[str, float], expected_action: str) -> int:
    if expected_action not in scores:
        return 0

    best_score = max(scores.values())
    target_score = scores[expected_action]
    if target_score == best_score:
        return 100
    if best_score <= 0:
        return 0

    return round(max(0.0, min(1.0, target_score / best_score)) * 100)
