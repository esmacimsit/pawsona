from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from pawsona.behavior import DEFAULT_SCENARIO, choose_action
from pawsona.pet import SKILL_KEYS, TRAIT_KEYS, PetLoadError, load_pet, write_pet_profile
from pawsona.training import normalize_feedback, scenario_for_round, train_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pawsona",
        description="Train personalities, not commands.",
    )
    parser.add_argument(
        "--pets-dir",
        default="pets",
        help="Directory containing pet YAML definitions.",
    )

    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Load and display a pet definition.",
    )
    inspect_parser.add_argument("pet", help="Pet name, for example: hermes")

    create_parser = subparsers.add_parser(
        "create",
        help="Create a pet YAML profile through a short questionnaire.",
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing pet YAML file.",
    )

    act_parser = subparsers.add_parser(
        "act",
        help="Generate an action from a pet profile.",
    )
    act_parser.add_argument("pet", help="Pet name, for example: hermes")

    play_parser = subparsers.add_parser(
        "play",
        help="Run an interactive training session.",
    )
    play_parser.add_argument("pet", help="Pet name, for example: hermes")
    play_parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of training rounds to run.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return inspect_pet(args.pet, Path(args.pets_dir))
    if args.command == "create":
        return create_pet(Path(args.pets_dir), force=args.force)
    if args.command == "act":
        return act_pet(args.pet, Path(args.pets_dir))
    if args.command == "play":
        return play_pet(args.pet, Path(args.pets_dir), rounds=args.rounds)

    parser.print_help()
    return 0


def inspect_pet(name: str, pets_dir: Path) -> int:
    try:
        pet = load_pet(name, pets_dir)
    except PetLoadError as error:
        print(f"error: {error}")
        return 1

    print(f"Name: {pet.name}")
    print(f"Species: {pet.species}")
    print(f"Breed: {pet.breed}")
    print(f"Age: {pet.age}")
    print(f"Sex: {pet.sex}")
    print(f"Neutered: {str(pet.neutered).lower()}")
    print("Traits:")
    for trait, value in sorted(pet.traits.items()):
        print(f"  {trait}: {value}")
    print("Skills:")
    for skill, value in sorted(pet.skills.items()):
        print(f"  {skill}: {value}")
    print("Memory:")
    for memory, value in sorted(pet.memory.items()):
        print(f"  {memory}: {value}")
    return 0


def create_pet(pets_dir: Path, force: bool = False) -> int:
    print("Create a Pawsona dog profile")
    name = _ask_text("Name")
    slug = _slugify(name)
    path = pets_dir / f"{slug}.yaml"
    if path.exists() and not force:
        print(f"error: {path} already exists. Re-run with --force to overwrite.")
        return 1

    profile = {
        "name": name,
        "species": "dog",
        "breed": _ask_text("Breed"),
        "age": _ask_int("Age", minimum=0),
        "sex": _ask_choice("Sex", {"female", "male", "unknown"}),
        "neutered": _ask_bool("Neutered"),
        "traits": {
            trait: _normalize_scale(_ask_int(_trait_prompt(trait), minimum=1, maximum=5))
            for trait in TRAIT_KEYS
        },
        "skills": {skill: 0.0 for skill in SKILL_KEYS},
        "memory": {},
    }

    write_pet_profile(path, profile)
    print(f"created: {path}")
    return 0


def act_pet(name: str, pets_dir: Path) -> int:
    try:
        pet = load_pet(name, pets_dir)
    except PetLoadError as error:
        print(f"error: {error}")
        return 1

    action, scores = choose_action(pet)
    print(f"Scenario: {DEFAULT_SCENARIO.name}")
    print(f"{pet.name} action: {action}")
    print("Scores:")
    for score_name, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        print(f"  {score_name}: {score}")
    return 0


def play_pet(name: str, pets_dir: Path, rounds: int) -> int:
    if rounds < 1:
        print("error: --rounds must be 1 or greater")
        return 1

    try:
        pet = load_pet(name, pets_dir)
    except PetLoadError as error:
        print(f"error: {error}")
        return 1

    print(f"Training {pet.name} for {rounds} rounds")
    print("Feedback: 1 reward, 2 praise, 3 ignore, 4 correct, q quit")

    completed_rounds = 0
    for round_index in range(rounds):
        scenario = scenario_for_round(round_index)
        action, scores = choose_action(pet, scenario)

        print("")
        print(f"Round {round_index + 1}/{rounds}")
        print(f"Scenario: {scenario.name}")
        print(f"Environment: {scenario.environment}")
        print(f"Goal: {scenario.goal}")
        print(f"Distraction: {scenario.distraction}")
        print(f"{pet.name} action: {action}")
        print(f"Top score: {scores[action]}")

        feedback = _ask_feedback()
        if feedback is None:
            break

        pet, updates = train_once(pet, scenario, feedback)
        completed_rounds += 1
        print("Updates:")
        for key, delta in updates.items():
            print(f"  {key} {delta:+.3f}")

    print("")
    print(f"Completed rounds: {completed_rounds}/{rounds}")
    return 0


def _ask_text(prompt: str, input_fn: Callable[[str], str] = input) -> str:
    while True:
        value = input_fn(f"{prompt}: ").strip()
        if value:
            return value
        print("Please enter a value.")


def _ask_int(
    prompt: str,
    minimum: int,
    maximum: int | None = None,
    input_fn: Callable[[str], str] = input,
) -> int:
    while True:
        raw_value = input_fn(f"{prompt}: ").strip()
        try:
            value = int(raw_value)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if value < minimum:
            print(f"Please enter {minimum} or greater.")
            continue
        if maximum is not None and value > maximum:
            print(f"Please enter {maximum} or lower.")
            continue
        return value


def _ask_bool(prompt: str, input_fn: Callable[[str], str] = input) -> bool:
    while True:
        value = input_fn(f"{prompt} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _ask_choice(
    prompt: str,
    choices: set[str],
    input_fn: Callable[[str], str] = input,
) -> str:
    options = "/".join(sorted(choices))
    while True:
        value = input_fn(f"{prompt} [{options}]: ").strip().lower()
        if value in choices:
            return value
        print(f"Please choose one of: {options}.")


def _ask_feedback(input_fn: Callable[[str], str] = input) -> str | None:
    while True:
        try:
            value = input_fn("Your feedback: ").strip().lower()
        except EOFError:
            print("")
            return None
        if value in {"q", "quit", "exit"}:
            return None
        feedback = normalize_feedback(value)
        if feedback is not None:
            return feedback
        print("Please choose 1, 2, 3, 4, or q.")


def _normalize_scale(value: int) -> float:
    return round((value - 1) / 4, 2)


def _slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "_" for character in value)
    return "_".join(part for part in slug.split("_") if part)


def _trait_prompt(trait: str) -> str:
    label = trait.replace("_", " ")
    return f"{label} (1-5)"
