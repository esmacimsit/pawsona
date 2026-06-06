from __future__ import annotations

from dataclasses import dataclass

from pawsona.benchmark import benchmark_pet
from pawsona.evaluation import evaluate_pet
from pawsona.pet import Pet


@dataclass(frozen=True)
class TradeoffReport:
    task_score: int
    generalization_score: int
    overfit_score: int
    interpretation: str


def analyze_tradeoff(pet: Pet) -> TradeoffReport:
    evaluation = evaluate_pet(pet)
    benchmark = benchmark_pet(pet)

    task_score = evaluation.overall_score
    generalization_score = benchmark.generalization_score
    overfit_score = max(0, min(100, task_score - generalization_score))

    return TradeoffReport(
        task_score=task_score,
        generalization_score=generalization_score,
        overfit_score=overfit_score,
        interpretation=_interpret_scores(task_score, generalization_score, overfit_score),
    )


def _interpret_scores(
    task_score: int,
    generalization_score: int,
    overfit_score: int,
) -> str:
    if task_score >= 70 and generalization_score >= 70:
        return "Balanced training: known tasks and transfer environments are both strong."
    if task_score >= 70 and generalization_score < 60:
        return (
            "Likely overfitting: known evaluation tasks are stronger than transfer "
            "environments."
        )
    if task_score < 50 and generalization_score < 50:
        return "Undertrained: both known tasks and transfer environments are weak."
    if task_score < 60 and generalization_score >= 60:
        return "Broad but weak: transfer behavior is steadier than known task performance."
    if overfit_score >= 20:
        return (
            "Possible narrow training: task performance is ahead of generalization by a "
            "meaningful margin."
        )
    return "Mild tradeoff: task and generalization scores are in a similar range."
