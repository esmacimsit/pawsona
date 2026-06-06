from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pawsona.pet import write_pet_profile
from pawsona.simple_yaml import load_yaml_mapping
from pawsona.state import state_path


class ChallengeError(Exception):
    """Raised when a challenge cannot be loaded or started."""


@dataclass(frozen=True)
class Challenge:
    id: str
    name: str
    difficulty: str
    version: str
    goal: str
    base_pet: Path
    focus: tuple[str, ...]
    metrics: tuple[str, ...]
    training_scenarios: tuple[str, ...]
    benchmark_environments: tuple[str, ...]


@dataclass(frozen=True)
class ChallengeStartResult:
    challenge: Challenge
    profile_path: Path
    save_path: Path
    wrote_profile: bool
    has_saved_state: bool


def list_challenges(challenges_dir: Path) -> tuple[Challenge, ...]:
    if not challenges_dir.exists():
        return ()
    if not challenges_dir.is_dir():
        raise ChallengeError(f"{challenges_dir}: challenges path is not a directory")

    challenges = []
    for child in sorted(challenges_dir.iterdir()):
        if child.is_dir() and (child / "challenge.yaml").exists():
            challenges.append(load_challenge(child.name, challenges_dir))
    return tuple(challenges)


def load_challenge(challenge_id: str, challenges_dir: Path) -> Challenge:
    challenge_dir = challenges_dir / challenge_id
    metadata_path = challenge_dir / "challenge.yaml"
    if not metadata_path.exists():
        raise ChallengeError(f"unknown challenge '{challenge_id}'")

    try:
        data = load_yaml_mapping(metadata_path)
    except ValueError as error:
        raise ChallengeError(str(error)) from error

    declared_id = _required_string(data, "id", metadata_path)
    if declared_id != challenge_id:
        raise ChallengeError(f"{metadata_path}: id must match directory name '{challenge_id}'")

    base_pet_name = _required_string(data, "base_pet", metadata_path)
    base_pet_path = challenge_dir / base_pet_name
    if not base_pet_path.exists():
        raise ChallengeError(f"{metadata_path}: base pet file does not exist: {base_pet_name}")

    return Challenge(
        id=declared_id,
        name=_required_string(data, "name", metadata_path),
        difficulty=_required_string(data, "difficulty", metadata_path),
        version=_required_string(data, "version", metadata_path),
        goal=_required_string(data, "goal", metadata_path),
        base_pet=base_pet_path,
        focus=_list_value(data, "focus", metadata_path),
        metrics=_list_value(data, "metrics", metadata_path),
        training_scenarios=_list_value(data, "training_scenarios", metadata_path),
        benchmark_environments=_list_value(data, "benchmark_environments", metadata_path),
    )


def start_challenge(
    challenge_id: str,
    challenges_dir: Path,
    pets_dir: Path,
    saves_dir: Path,
) -> ChallengeStartResult:
    challenge = load_challenge(challenge_id, challenges_dir)
    profile_path = pets_dir / f"{challenge.id}.yaml"
    wrote_profile = False

    if not profile_path.exists():
        try:
            base_profile = load_yaml_mapping(challenge.base_pet)
        except ValueError as error:
            raise ChallengeError(str(error)) from error
        write_pet_profile(profile_path, base_profile)
        wrote_profile = True

    save_path = state_path(challenge.id, saves_dir)
    return ChallengeStartResult(
        challenge=challenge,
        profile_path=profile_path,
        save_path=save_path,
        wrote_profile=wrote_profile,
        has_saved_state=save_path.exists(),
    )


def _required_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ChallengeError(f"{path}: '{key}' must be a non-empty string")
    return value.strip()


def _list_value(data: dict[str, Any], key: str, path: Path) -> tuple[str, ...]:
    value = data.get(key)
    if isinstance(value, str):
        items = tuple(item.strip() for item in value.split(",") if item.strip())
    elif isinstance(value, list):
        items = tuple(str(item).strip() for item in value if str(item).strip())
    else:
        raise ChallengeError(f"{path}: '{key}' must be a comma-separated string or list")
    if not items:
        raise ChallengeError(f"{path}: '{key}' must not be empty")
    return items
