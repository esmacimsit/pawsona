from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from pawsona.behavior import choose_action
from pawsona.pet import Pet
from pawsona.training import SCENARIOS, scenario_for_round


@dataclass(frozen=True)
class StatusObservation:
    action_counts: Counter[str]
    scenario_counts: dict[str, Counter[str]]
    rounds: int


def observe_status(pet: Pet, rounds: int = 10) -> StatusObservation:
    action_counts: Counter[str] = Counter()
    scenario_counts: dict[str, Counter[str]] = {
        scenario.name: Counter() for scenario in SCENARIOS
    }

    for round_index in range(rounds):
        scenario = scenario_for_round(round_index)
        action, _scores = choose_action(pet, scenario)
        action_counts[action] += 1
        scenario_counts[scenario.name][action] += 1

    return StatusObservation(
        action_counts=action_counts,
        scenario_counts=scenario_counts,
        rounds=rounds,
    )
