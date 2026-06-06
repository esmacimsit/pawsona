from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pawsona.behavior import Scenario
from pawsona.pet import SKILL_KEYS, Pet
from pawsona.tradeoff import TradeoffReport, analyze_tradeoff
from pawsona.training import ACTION_SKILLS, SCENARIOS, normalize_feedback, train_action


class DatasetError(Exception):
    """Raised when a dataset cannot be loaded or replayed."""


@dataclass(frozen=True)
class InteractionSample:
    scenario: Scenario
    action: str
    feedback: str


@dataclass(frozen=True)
class DatasetTrainingReport:
    before: TradeoffReport
    after: TradeoffReport
    samples_loaded: int
    samples_seen: int
    applied_updates: int
    skipped_samples: int


SCENARIOS_BY_NAME = {scenario.name: scenario for scenario in SCENARIOS}


def load_jsonl_dataset(path: Path) -> tuple[InteractionSample, ...]:
    if not path.exists():
        raise DatasetError(f"{path}: dataset file does not exist")
    if not path.is_file():
        raise DatasetError(f"{path}: dataset path is not a file")

    samples: list[InteractionSample] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as error:
            raise DatasetError(f"{path}:{line_number}: invalid JSON: {error}") from error
        if not isinstance(data, dict):
            raise DatasetError(f"{path}:{line_number}: sample must be a JSON object")
        samples.append(_parse_sample(data, path, line_number))

    if not samples:
        raise DatasetError(f"{path}: dataset must contain at least one sample")
    return tuple(samples)


def train_from_dataset(
    pet: Pet,
    samples: tuple[InteractionSample, ...],
    epochs: int,
) -> tuple[Pet, DatasetTrainingReport]:
    if epochs < 1:
        raise DatasetError("--epochs must be 1 or greater")

    before = analyze_tradeoff(pet)
    trained_pet = pet
    applied_updates = 0

    for _epoch in range(epochs):
        for sample in samples:
            trained_pet, _updates = train_action(
                trained_pet,
                sample.scenario,
                sample.action,
                sample.feedback,
            )
            applied_updates += 1

    after = analyze_tradeoff(trained_pet)
    samples_seen = len(samples) * epochs
    return trained_pet, DatasetTrainingReport(
        before=before,
        after=after,
        samples_loaded=len(samples),
        samples_seen=samples_seen,
        applied_updates=applied_updates,
        skipped_samples=samples_seen - applied_updates,
    )


def _parse_sample(data: dict[str, Any], path: Path, line_number: int) -> InteractionSample:
    scenario_name = _required_string(data, "scenario", path, line_number)
    environment = _required_string(data, "environment", path, line_number)
    cue = _required_string(data, "cue", path, line_number)
    distraction = _required_string(data, "distraction", path, line_number)
    action = _required_string(data, "action", path, line_number)
    raw_feedback = _required_feedback(data, path, line_number)
    target_skill = _required_string(data, "target_skill", path, line_number)

    if action not in ACTION_SKILLS:
        raise DatasetError(f"{path}:{line_number}: unknown action '{action}'")
    if target_skill not in SKILL_KEYS:
        raise DatasetError(f"{path}:{line_number}: unknown target_skill '{target_skill}'")

    feedback = normalize_feedback(raw_feedback)
    if feedback is None:
        raise DatasetError(f"{path}:{line_number}: unknown feedback '{raw_feedback}'")

    base_scenario = SCENARIOS_BY_NAME.get(scenario_name)
    target_action = _optional_string(data.get("target_action"), path, line_number, "target_action")
    if target_action is None:
        target_action = base_scenario.target_action if base_scenario is not None else action
    if target_action not in ACTION_SKILLS:
        raise DatasetError(f"{path}:{line_number}: unknown target_action '{target_action}'")

    goal = _optional_string(data.get("goal"), path, line_number, "goal")
    if goal is None:
        goal = base_scenario.goal if base_scenario is not None else f"dataset scenario: {scenario_name}"

    scenario = Scenario(
        name=scenario_name,
        environment=environment,
        cue=cue,
        distraction=distraction,
        goal=goal,
        target_action=target_action,
        target_skill=target_skill,
    )
    return InteractionSample(scenario=scenario, action=action, feedback=feedback)


def _required_string(data: dict[str, Any], key: str, path: Path, line_number: int) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DatasetError(f"{path}:{line_number}: '{key}' must be a non-empty string")
    return value.strip()


def _required_feedback(data: dict[str, Any], path: Path, line_number: int) -> str:
    value = data.get("feedback")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    raise DatasetError(f"{path}:{line_number}: 'feedback' must be a non-empty string or number")


def _optional_string(
    value: Any,
    path: Path,
    line_number: int,
    key: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DatasetError(f"{path}:{line_number}: '{key}' must be a non-empty string")
    return value.strip()
