from __future__ import annotations

from dataclasses import dataclass

from pawsona.pet import Pet


@dataclass(frozen=True)
class Scenario:
    name: str
    environment: str
    cue: str
    distraction: str
    goal: str
    target_action: str
    target_skill: str


DEFAULT_SCENARIO = Scenario(
    name="owner_arrives_home",
    environment="home",
    cue="greeting",
    distraction="door_noise",
    goal="stay calm when the owner arrives",
    target_action="observe_calmly",
    target_skill="settle",
)


def choose_action(pet: Pet, scenario: Scenario = DEFAULT_SCENARIO) -> tuple[str, dict[str, float]]:
    scores = score_actions(pet, scenario)
    action = max(scores, key=scores.get)
    return action, scores


def score_actions(pet: Pet, scenario: Scenario = DEFAULT_SCENARIO) -> dict[str, float]:
    traits = pet.traits
    skills = pet.skills
    memory = pet.memory

    home_bias = memory.get(scenario.environment, 0.0)
    distraction_bias = memory.get(scenario.distraction, 0.0)

    scores = {
        "observe_calmly": (
            traits["self_control"] * 0.35
            + skills["settle"] * 0.30
            + traits["confidence"] * 0.15
            + home_bias * 0.10
            - traits["impulsivity"] * 0.20
        ),
        "jump_excitedly": (
            traits["energy"] * 0.25
            + traits["affection_seeking"] * 0.25
            + traits["attachment"] * 0.20
            + traits["impulsivity"] * 0.20
            - skills["settle"] * 0.15
        ),
        "bark_at_noise": (
            traits["vigilance"] * 0.35
            + traits["sensitivity"] * 0.20
            + max(distraction_bias, 0.0) * 0.15
            - traits["confidence"] * 0.10
        ),
        "bring_toy": (
            skills["fetch"] * 0.35
            + traits["play_drive"] * 0.25
            + traits["sociability"] * 0.10
            + memory.get("toy", 0.0) * 0.10
        ),
        "return_to_owner": (
            skills["recall"] * 0.35
            + skills["focus"] * 0.20
            + traits["trainability"] * 0.25
            - traits["curiosity"] * 0.10
        ),
    }
    return {action: round(score, 3) for action, score in scores.items()}
