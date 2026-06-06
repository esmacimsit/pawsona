from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pawsona.breeds import BreedPriorError, validate_breed_priors
from pawsona.challenge import ChallengeError, list_challenges
from pawsona.pet import PetLoadError, load_pet


@dataclass(frozen=True)
class ValidationReport:
    checked_pets: int
    checked_challenges: int
    checked_breed_priors: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_content(pets_dir: Path, challenges_dir: Path) -> ValidationReport:
    errors: list[str] = []
    checked_pets = 0
    checked_challenges = 0
    checked_breed_priors = 0

    for pet_name in _pet_names(pets_dir):
        checked_pets += 1
        try:
            load_pet(pet_name, pets_dir)
        except PetLoadError as error:
            errors.append(str(error))

    try:
        challenges = list_challenges(challenges_dir)
    except ChallengeError as error:
        challenges = ()
        errors.append(str(error))

    for challenge in challenges:
        checked_challenges += 1
        try:
            load_pet(challenge.base_pet.stem, challenge.base_pet.parent)
        except PetLoadError as error:
            errors.append(str(error))

    try:
        checked_breed_priors = len(validate_breed_priors())
    except BreedPriorError as error:
        errors.append(str(error))

    return ValidationReport(
        checked_pets=checked_pets,
        checked_challenges=checked_challenges,
        checked_breed_priors=checked_breed_priors,
        errors=tuple(errors),
    )


def _pet_names(pets_dir: Path) -> tuple[str, ...]:
    names: set[str] = set()
    if pets_dir.exists():
        for path in sorted(pets_dir.glob("*.yaml")):
            if path.name == "template.yaml":
                continue
            names.add(path.stem)
    community_dir = pets_dir / "community"
    if community_dir.exists():
        for path in sorted(community_dir.glob("*.yaml")):
            names.add(path.stem)
    return tuple(sorted(names))
