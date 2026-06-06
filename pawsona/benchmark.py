from __future__ import annotations

from dataclasses import dataclass

from pawsona.behavior import Scenario, choose_action, score_actions
from pawsona.evaluation import score_expected_action
from pawsona.pet import Pet
from pawsona.training import SCENARIOS


@dataclass(frozen=True)
class BenchmarkCase:
    scenario: Scenario
    expected_action: str


@dataclass(frozen=True)
class EnvironmentScore:
    environment: str
    split: str
    score: int
    cases: tuple[BenchmarkCase, ...]


@dataclass(frozen=True)
class BenchmarkReport:
    environment_scores: tuple[EnvironmentScore, ...]
    generalization_score: int


SCENARIOS_BY_NAME = {scenario.name: scenario for scenario in SCENARIOS}

HOME_CASES = (
    BenchmarkCase(
        scenario=SCENARIOS_BY_NAME["owner_arrives_home"],
        expected_action="observe_calmly",
    ),
    BenchmarkCase(
        scenario=SCENARIOS_BY_NAME["settle_during_noise"],
        expected_action="observe_calmly",
    ),
)

PARK_CASES = (
    BenchmarkCase(
        scenario=SCENARIOS_BY_NAME["fetch_at_park"],
        expected_action="bring_toy",
    ),
    BenchmarkCase(
        scenario=Scenario(
            name="recall_from_park",
            environment="park",
            cue="recall",
            distraction="other_dog",
            goal="return when called at the park",
            target_action="return_to_owner",
            target_skill="recall",
        ),
        expected_action="return_to_owner",
    ),
)

STREET_CASES = (
    BenchmarkCase(
        scenario=Scenario(
            name="street_recall",
            environment="street",
            cue="recall",
            distraction="traffic",
            goal="return when called near street noise",
            target_action="return_to_owner",
            target_skill="recall",
        ),
        expected_action="return_to_owner",
    ),
    BenchmarkCase(
        scenario=Scenario(
            name="street_focus",
            environment="street",
            cue="focus",
            distraction="food_wrapper",
            goal="keep attention on the owner near street distractions",
            target_action="return_to_owner",
            target_skill="focus",
        ),
        expected_action="return_to_owner",
    ),
    BenchmarkCase(
        scenario=Scenario(
            name="street_calm_noise",
            environment="street",
            cue="settle",
            distraction="traffic",
            goal="stay calm through street noise",
            target_action="observe_calmly",
            target_skill="settle",
        ),
        expected_action="observe_calmly",
    ),
)

BENCHMARK_ENVIRONMENTS = (
    ("Home", "familiar", HOME_CASES),
    ("Park", "transfer", PARK_CASES),
    ("Street", "unfamiliar", STREET_CASES),
)


def benchmark_pet(pet: Pet) -> BenchmarkReport:
    environment_scores = tuple(
        _score_environment(pet, environment, split, cases)
        for environment, split, cases in BENCHMARK_ENVIRONMENTS
    )
    generalization_targets = [
        environment_score.score
        for environment_score in environment_scores
        if environment_score.split != "familiar"
    ]
    generalization_score = round(sum(generalization_targets) / len(generalization_targets))
    return BenchmarkReport(
        environment_scores=environment_scores,
        generalization_score=generalization_score,
    )


def _score_environment(
    pet: Pet,
    environment: str,
    split: str,
    cases: tuple[BenchmarkCase, ...],
) -> EnvironmentScore:
    scores = []
    for case in cases:
        chosen_action, _chosen_scores = choose_action(pet, case.scenario)
        action_scores = score_actions(pet, case.scenario)
        score = score_expected_action(action_scores, case.expected_action)
        if chosen_action == case.expected_action:
            score = 100
        scores.append(score)

    return EnvironmentScore(
        environment=environment,
        split=split,
        score=round(sum(scores) / len(scores)),
        cases=cases,
    )
