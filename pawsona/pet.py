from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pawsona.simple_yaml import load_yaml_mapping, load_yaml_text, write_yaml_mapping


class PetLoadError(Exception):
    """Raised when a pet definition cannot be loaded."""


TRAIT_KEYS = (
    "energy",
    "confidence",
    "sociability",
    "attachment",
    "affection_seeking",
    "curiosity",
    "impulsivity",
    "self_control",
    "sensitivity",
    "trainability",
    "vigilance",
    "food_drive",
    "play_drive",
)

SKILL_KEYS = (
    "recall",
    "focus",
    "settle",
    "fetch",
)


@dataclass(frozen=True)
class Pet:
    name: str
    species: str
    breed: str
    age: int
    sex: str
    neutered: bool
    traits: dict[str, float]
    skills: dict[str, float]
    memory: dict[str, float]


def load_pet(name: str, pets_dir: Path) -> Pet:
    path = _find_pet_file(name, pets_dir)
    if path is not None:
        data = _read_yaml(path)
        return _parse_pet(data, path)

    data = _read_builtin_pet(name)
    if data is not None:
        return _parse_pet(data, f"built-in pet '{name}'")

    raise PetLoadError(f"could not find pet '{name}' in {pets_dir} or built-in pets")


def _find_pet_file(name: str, pets_dir: Path) -> Path | None:
    candidates = [
        pets_dir / f"{name}.yaml",
        pets_dir / "community" / f"{name}.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _read_builtin_pet(name: str) -> dict[str, Any] | None:
    resource = resources.files("pawsona").joinpath("builtin_pets", f"{name}.yaml")
    if not resource.is_file():
        return None
    try:
        return load_yaml_text(resource.read_text(encoding="utf-8"), source=str(resource))
    except ValueError as error:
        raise PetLoadError(str(error)) from error


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        return load_yaml_mapping(path)
    except ValueError as error:
        raise PetLoadError(str(error)) from error


def write_pet_profile(path: Path, profile: dict[str, Any]) -> None:
    write_yaml_mapping(path, profile)


def _parse_pet(data: dict[str, Any], path: Path | str) -> Pet:
    try:
        name = _require_string(data, "name")
        species = _require_string(data, "species")
        breed = _require_string(data, "breed")
        age = _require_int(data, "age")
        sex = _require_string(data, "sex")
        neutered = _require_bool(data, "neutered")
        traits = _require_number_map(data, "traits", required_keys=TRAIT_KEYS)
        skills = _require_number_map(data, "skills", required_keys=SKILL_KEYS)
        memory = _require_number_map(data, "memory")
    except PetLoadError as error:
        raise PetLoadError(f"{path}: {error}") from error

    return Pet(
        name=name,
        species=species,
        breed=breed,
        age=age,
        sex=sex,
        neutered=neutered,
        traits=traits,
        skills=skills,
        memory=memory,
    )


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PetLoadError(f"'{key}' must be a non-empty string")
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise PetLoadError(f"'{key}' must be an integer")
    if value < 0:
        raise PetLoadError(f"'{key}' must be zero or greater")
    return value


def _require_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise PetLoadError(f"'{key}' must be true or false")
    return value


def _require_number_map(
    data: dict[str, Any],
    key: str,
    required_keys: tuple[str, ...] = (),
) -> dict[str, float]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise PetLoadError(f"'{key}' must be a mapping")

    missing = [required_key for required_key in required_keys if required_key not in value]
    if missing:
        raise PetLoadError(f"'{key}' is missing: {', '.join(missing)}")

    result: dict[str, float] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise PetLoadError(f"'{key}' keys must be non-empty strings")
        if not isinstance(item_value, int | float) or isinstance(item_value, bool):
            raise PetLoadError(f"'{key}.{item_key}' must be a number")
        numeric_value = float(item_value)
        if numeric_value < -1.0 or numeric_value > 1.0:
            raise PetLoadError(f"'{key}.{item_key}' must be between -1.0 and 1.0")
        result[item_key] = numeric_value
    return result
