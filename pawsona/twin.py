from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pawsona import __version__
from pawsona.challenge import Challenge
from pawsona.pet import Pet, write_pet_profile
from pawsona.state import LoadedState, pet_key, save_trained_state_snapshot
from pawsona.tradeoff import TradeoffReport


class TwinError(Exception):
    """Raised when a Pawsona twin archive cannot be exported or imported."""


@dataclass(frozen=True)
class TwinExportResult:
    path: Path
    pet_key: str
    rounds_trained: int
    is_challenge_submission: bool
    final_score: int | None = None


@dataclass(frozen=True)
class TwinImportResult:
    pet_key: str
    profile_path: Path
    state_path: Path
    wrote_profile: bool
    rounds_trained: int


def export_twin(
    base_pet: Pet,
    trained_pet: Pet,
    name: str,
    loaded_state: LoadedState | None,
    out_path: Path,
    source_profile: str,
    challenge: Challenge | None = None,
    challenge_metrics: TradeoffReport | None = None,
) -> TwinExportResult:
    key = pet_key(name)
    rounds_trained = loaded_state.rounds_trained if loaded_state is not None else 0
    last_updated = loaded_state.last_updated if loaded_state is not None else None

    archive = {
        "format": "pawsona.twin",
        "format_version": 1,
        "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "package": {
            "name": "pawsona",
            "version": __version__,
        },
        "pet_key": key,
        "source_profile": source_profile,
        "base_profile": _pet_to_profile(base_pet),
        "trained_state": {
            "pet": trained_pet.name,
            "pet_key": key,
            "rounds_trained": rounds_trained,
            "last_updated": last_updated,
            "source_profile": source_profile,
            "skills": dict(sorted(trained_pet.skills.items())),
            "memory": dict(sorted(trained_pet.memory.items())),
        },
    }

    if challenge is not None and challenge_metrics is not None:
        archive["challenge_submission"] = {
            "challenge_id": challenge.id,
            "challenge_name": challenge.name,
            "challenge_version": challenge.version,
            "difficulty": challenge.difficulty,
            "base_version": challenge.version,
            "metrics": {
                "eval_overall_score": challenge_metrics.task_score,
                "generalization_score": challenge_metrics.generalization_score,
                "overfit_score": challenge_metrics.overfit_score,
                "final_score": _final_score(challenge_metrics),
            },
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(archive, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return TwinExportResult(
        path=out_path,
        pet_key=key,
        rounds_trained=rounds_trained,
        is_challenge_submission=challenge is not None,
        final_score=_final_score(challenge_metrics) if challenge_metrics is not None else None,
    )


def import_twin(
    archive_path: Path,
    pets_dir: Path,
    saves_dir: Path,
) -> TwinImportResult:
    archive = _read_archive(archive_path)
    key = _required_string(archive, "pet_key", archive_path)
    if pet_key(key) != key:
        raise TwinError(f"{archive_path}: 'pet_key' must be a normalized pet key")
    base_profile = _required_mapping(archive, "base_profile", archive_path)
    trained_state = _required_mapping(archive, "trained_state", archive_path)
    challenge_submission = _optional_mapping(archive.get("challenge_submission"), archive_path)
    profile_name = key
    if challenge_submission is not None:
        profile_name = _required_string(challenge_submission, "challenge_id", archive_path)

    profile_path = pets_dir / f"{profile_name}.yaml"
    wrote_profile = False
    if not profile_path.exists():
        write_pet_profile(profile_path, base_profile)
        wrote_profile = True

    rounds_trained = _required_non_negative_int(trained_state, "rounds_trained", archive_path)
    last_updated = _optional_string(trained_state.get("last_updated"), archive_path, "last_updated")
    source_profile = _optional_string(
        trained_state.get("source_profile"),
        archive_path,
        "source_profile",
    ) or f"import:{archive_path}"

    pet = _profile_and_state_to_pet(base_profile, trained_state, archive_path)
    state_path = save_trained_state_snapshot(
        pet,
        profile_name,
        saves_dir,
        rounds_trained=rounds_trained,
        source_profile=source_profile,
        last_updated=last_updated,
    )

    return TwinImportResult(
        pet_key=profile_name,
        profile_path=profile_path,
        state_path=state_path,
        wrote_profile=wrote_profile,
        rounds_trained=rounds_trained,
    )


def _read_archive(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise TwinError(f"{path}: archive file does not exist")
    if not path.is_file():
        raise TwinError(f"{path}: archive path is not a file")
    try:
        archive = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TwinError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(archive, dict):
        raise TwinError(f"{path}: archive must be a JSON object")
    if archive.get("format") != "pawsona.twin":
        raise TwinError(f"{path}: unsupported archive format")
    if archive.get("format_version") != 1:
        raise TwinError(f"{path}: unsupported archive format_version")
    return archive


def _pet_to_profile(pet: Pet) -> dict[str, Any]:
    return {
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age": pet.age,
        "sex": pet.sex,
        "neutered": pet.neutered,
        "traits": dict(sorted(pet.traits.items())),
        "skills": dict(sorted(pet.skills.items())),
        "memory": dict(sorted(pet.memory.items())),
    }


def _final_score(metrics: TradeoffReport) -> int:
    raw_score = (
        metrics.task_score * 0.45
        + metrics.generalization_score * 0.45
        - metrics.overfit_score * 0.10
    )
    return round(max(0.0, min(100.0, raw_score)))


def _profile_and_state_to_pet(
    base_profile: dict[str, Any],
    trained_state: dict[str, Any],
    archive_path: Path,
) -> Pet:
    skills = dict(_required_mapping(base_profile, "skills", archive_path))
    skills.update(_number_map(trained_state.get("skills", {}), archive_path, "trained_state.skills"))

    memory = dict(_required_mapping(base_profile, "memory", archive_path))
    memory.update(_number_map(trained_state.get("memory", {}), archive_path, "trained_state.memory"))

    return Pet(
        name=_required_string(base_profile, "name", archive_path),
        species=_required_string(base_profile, "species", archive_path),
        breed=_required_string(base_profile, "breed", archive_path),
        age=_required_non_negative_int(base_profile, "age", archive_path),
        sex=_required_string(base_profile, "sex", archive_path),
        neutered=_required_bool(base_profile, "neutered", archive_path),
        traits=_number_map(base_profile.get("traits", {}), archive_path, "base_profile.traits"),
        skills=skills,
        memory=memory,
    )


def _required_mapping(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise TwinError(f"{path}: '{key}' must be an object")
    return value


def _optional_mapping(value: Any, path: Path) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TwinError(f"{path}: optional archive section must be an object")
    return value


def _required_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TwinError(f"{path}: '{key}' must be a non-empty string")
    return value.strip()


def _optional_string(value: Any, path: Path, key: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TwinError(f"{path}: '{key}' must be a string")
    return value


def _required_bool(data: dict[str, Any], key: str, path: Path) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise TwinError(f"{path}: '{key}' must be true or false")
    return value


def _required_non_negative_int(data: dict[str, Any], key: str, path: Path) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TwinError(f"{path}: '{key}' must be a non-negative integer")
    return value


def _number_map(value: Any, path: Path, key: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise TwinError(f"{path}: '{key}' must be an object")
    result: dict[str, float] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise TwinError(f"{path}: '{key}' keys must be non-empty strings")
        if not isinstance(item_value, int | float) or isinstance(item_value, bool):
            raise TwinError(f"{path}: '{key}.{item_key}' must be a number")
        result[item_key] = float(item_value)
    return result
