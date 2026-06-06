from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pawsona.pet import TRAIT_KEYS
from pawsona.simple_yaml import load_yaml_mapping, load_yaml_text


class BreedPriorError(Exception):
    """Raised when a breed prior cannot be loaded or validated."""


@dataclass(frozen=True)
class BreedPrior:
    breed: str
    adjustments: dict[str, float]
    source: str


def normalize_breed_name(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "_" for character in value)
    return "_".join(part for part in slug.split("_") if part)


def load_breed_prior(breed: str, breeds_dir: Path | None = None) -> BreedPrior:
    key = normalize_breed_name(breed)
    if not key:
        key = "mixed"

    if breeds_dir is not None:
        prior = _load_prior_from_path(breeds_dir / f"{key}.yaml")
        if prior is not None:
            return prior
        fallback = _load_prior_from_path(breeds_dir / "mixed.yaml")
        if fallback is not None:
            return fallback

    prior = _load_packaged_prior(key)
    if prior is not None:
        return prior
    fallback = _load_packaged_prior("mixed")
    if fallback is not None:
        return fallback
    return BreedPrior(breed="mixed", adjustments={}, source="fallback:no-op")


def apply_breed_prior(traits: dict[str, float], prior: BreedPrior) -> dict[str, float]:
    adjusted = dict(traits)
    for trait, delta in prior.adjustments.items():
        adjusted[trait] = _clamp(adjusted.get(trait, 0.0) + delta)
    return adjusted


def validate_breed_priors(breeds_dir: Path | None = None) -> tuple[BreedPrior, ...]:
    priors = []
    seen: set[str] = set()

    if breeds_dir is not None and breeds_dir.exists():
        for path in sorted(breeds_dir.glob("*.yaml")):
            prior = _parse_prior(load_yaml_mapping(path), str(path))
            priors.append(prior)
            seen.add(prior.breed)
        return tuple(priors)

    resource_root = resources.files("pawsona").joinpath("knowledge", "breeds")
    for resource in sorted(resource_root.iterdir(), key=lambda item: item.name):
        if resource.is_file() and resource.name.endswith(".yaml"):
            data = load_yaml_text(resource.read_text(encoding="utf-8"), source=str(resource))
            prior = _parse_prior(data, str(resource))
            priors.append(prior)
            seen.add(prior.breed)

    missing = {"pug", "border_collie", "golden_retriever", "mixed"} - seen
    if missing:
        raise BreedPriorError(f"missing breed priors: {', '.join(sorted(missing))}")
    return tuple(priors)


def _load_prior_from_path(path: Path) -> BreedPrior | None:
    if not path.exists():
        return None
    try:
        return _parse_prior(load_yaml_mapping(path), str(path))
    except ValueError as error:
        raise BreedPriorError(str(error)) from error


def _load_packaged_prior(key: str) -> BreedPrior | None:
    resource = resources.files("pawsona").joinpath("knowledge", "breeds", f"{key}.yaml")
    if not resource.is_file():
        return None
    data = load_yaml_text(resource.read_text(encoding="utf-8"), source=str(resource))
    return _parse_prior(data, str(resource))


def _parse_prior(data: dict[str, Any], source: str) -> BreedPrior:
    breed = data.get("breed")
    if not isinstance(breed, str) or not breed.strip():
        raise BreedPriorError(f"{source}: 'breed' must be a non-empty string")

    key = normalize_breed_name(breed)
    adjustments = data.get("adjustments")
    if not isinstance(adjustments, dict):
        raise BreedPriorError(f"{source}: 'adjustments' must be a mapping")

    parsed: dict[str, float] = {}
    for trait, delta in adjustments.items():
        if trait not in TRAIT_KEYS:
            raise BreedPriorError(f"{source}: unknown trait '{trait}'")
        if not isinstance(delta, int | float) or isinstance(delta, bool):
            raise BreedPriorError(f"{source}: adjustment '{trait}' must be a number")
        numeric_delta = float(delta)
        if numeric_delta < -0.1 or numeric_delta > 0.1:
            raise BreedPriorError(f"{source}: adjustment '{trait}' must be between -0.1 and 0.1")
        parsed[trait] = numeric_delta

    return BreedPrior(breed=key, adjustments=parsed, source=source)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)
