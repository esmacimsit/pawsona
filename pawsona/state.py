from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pawsona.pet import Pet


class StateError(Exception):
    """Raised when trained state cannot be loaded or saved."""


@dataclass(frozen=True)
class LoadedState:
    path: Path
    rounds_trained: int
    last_updated: str | None
    source_profile: str | None


def pet_key(name: str) -> str:
    key = "".join(character.lower() if character.isalnum() else "_" for character in name)
    return "_".join(part for part in key.split("_") if part)


def state_path(name: str, saves_dir: Path) -> Path:
    return saves_dir / f"{pet_key(name)}.json"


def apply_trained_state(pet: Pet, name: str, saves_dir: Path) -> tuple[Pet, LoadedState | None]:
    path = state_path(name, saves_dir)
    if not path.exists():
        return pet, None

    data = _read_state(path)
    skills = dict(pet.skills)
    skills.update(_number_map(data.get("skills", {}), path, "skills"))

    memory = dict(pet.memory)
    memory.update(_number_map(data.get("memory", {}), path, "memory"))

    loaded_state = LoadedState(
        path=path,
        rounds_trained=_rounds_trained(data, path),
        last_updated=_optional_string(data.get("last_updated"), path, "last_updated"),
        source_profile=_optional_string(data.get("source_profile"), path, "source_profile"),
    )
    return replace(pet, skills=skills, memory=memory), loaded_state


def save_trained_state(
    pet: Pet,
    name: str,
    saves_dir: Path,
    rounds_completed: int,
    source_profile: str,
) -> Path:
    path = state_path(name, saves_dir)
    existing_rounds = 0
    if path.exists():
        existing_rounds = _rounds_trained(_read_state(path), path)

    data = {
        "pet": pet.name,
        "pet_key": pet_key(name),
        "rounds_trained": existing_rounds + rounds_completed,
        "last_updated": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_profile": source_profile,
        "skills": dict(sorted(pet.skills.items())),
        "memory": dict(sorted(pet.memory.items())),
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StateError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(data, dict):
        raise StateError(f"{path}: state must be a JSON object")
    return data


def _number_map(value: Any, path: Path, key: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise StateError(f"{path}: '{key}' must be an object")

    result: dict[str, float] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise StateError(f"{path}: '{key}' keys must be non-empty strings")
        if not isinstance(item_value, int | float) or isinstance(item_value, bool):
            raise StateError(f"{path}: '{key}.{item_key}' must be a number")
        result[item_key] = float(item_value)
    return result


def _rounds_trained(data: dict[str, Any], path: Path) -> int:
    value = data.get("rounds_trained", 0)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise StateError(f"{path}: 'rounds_trained' must be a non-negative integer")
    return value


def _optional_string(value: Any, path: Path, key: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise StateError(f"{path}: '{key}' must be a string")
    return value
