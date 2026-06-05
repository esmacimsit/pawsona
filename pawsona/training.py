from __future__ import annotations

from dataclasses import replace

from pawsona.behavior import Scenario, choose_action
from pawsona.pet import Pet


SCENARIOS = (
    Scenario(
        name="owner_arrives_home",
        environment="home",
        cue="greeting",
        distraction="door_noise",
        goal="stay calm when the owner arrives",
        target_action="observe_calmly",
        target_skill="settle",
    ),
    Scenario(
        name="recall_from_yard",
        environment="outside",
        cue="recall",
        distraction="squirrel",
        goal="return when called",
        target_action="return_to_owner",
        target_skill="recall",
    ),
    Scenario(
        name="fetch_at_park",
        environment="park",
        cue="fetch",
        distraction="squirrel",
        goal="bring the toy back",
        target_action="bring_toy",
        target_skill="fetch",
    ),
    Scenario(
        name="focus_near_food",
        environment="kitchen",
        cue="focus",
        distraction="meat",
        goal="keep attention on the owner",
        target_action="return_to_owner",
        target_skill="focus",
    ),
    Scenario(
        name="settle_during_noise",
        environment="home",
        cue="settle",
        distraction="door_noise",
        goal="settle through a noise",
        target_action="observe_calmly",
        target_skill="settle",
    ),
)

FEEDBACK_LABELS = {
    "1": "reward",
    "2": "praise",
    "3": "ignore",
    "4": "correct",
    "reward": "reward",
    "praise": "praise",
    "ignore": "ignore",
    "correct": "correct",
}

ACTION_SKILLS = {
    "observe_calmly": "settle",
    "jump_excitedly": "settle",
    "bark_at_noise": "focus",
    "bring_toy": "fetch",
    "return_to_owner": "recall",
}


def scenario_for_round(round_index: int) -> Scenario:
    return SCENARIOS[round_index % len(SCENARIOS)]


def normalize_feedback(value: str) -> str | None:
    return FEEDBACK_LABELS.get(value.strip().lower())


def train_once(pet: Pet, scenario: Scenario, feedback: str) -> tuple[Pet, dict[str, float]]:
    action, _scores = choose_action(pet, scenario)
    skill_updates = _skill_updates(action, scenario, feedback)
    memory_updates = _memory_updates(action, scenario, feedback)

    skills = dict(pet.skills)
    memory = dict(pet.memory)
    applied: dict[str, float] = {}

    for skill, delta in skill_updates.items():
        old_value = skills.get(skill, 0.0)
        new_value = _clamp(old_value + delta)
        skills[skill] = new_value
        applied[f"{skill}_skill"] = round(new_value - old_value, 3)

    for key, delta in memory_updates.items():
        old_value = memory.get(key, 0.0)
        new_value = _clamp(old_value + delta, minimum=-1.0)
        memory[key] = new_value
        applied[f"{key}_memory"] = round(new_value - old_value, 3)

    return replace(pet, skills=skills, memory=memory), applied


def _skill_updates(action: str, scenario: Scenario, feedback: str) -> dict[str, float]:
    action_skill = ACTION_SKILLS.get(action, scenario.target_skill)

    if feedback == "reward":
        return {action_skill: 0.05}
    if feedback == "praise":
        return {action_skill: 0.03}
    if feedback == "correct":
        updates = {scenario.target_skill: 0.03}
        if action != scenario.target_action:
            updates[action_skill] = updates.get(action_skill, 0.0) - 0.02
        return updates
    return {scenario.target_skill: -0.005}


def _memory_updates(action: str, scenario: Scenario, feedback: str) -> dict[str, float]:
    if feedback == "reward":
        return {
            scenario.name: 0.04,
            scenario.environment: 0.02,
            scenario.distraction: 0.01 if action == scenario.target_action else -0.02,
        }
    if feedback == "praise":
        return {
            scenario.name: 0.025,
            scenario.environment: 0.015,
        }
    if feedback == "correct":
        return {
            scenario.name: -0.02,
            scenario.distraction: -0.03,
        }
    return {scenario.name: -0.005}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return round(max(minimum, min(maximum, value)), 3)
