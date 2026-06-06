from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from pawsona.benchmark import benchmark_pet
from pawsona.behavior import DEFAULT_SCENARIO, choose_action
from pawsona.challenge import ChallengeError, list_challenges, load_challenge, start_challenge
from pawsona.dataset import DatasetError, load_jsonl_dataset, train_from_dataset
from pawsona.evaluation import evaluate_pet
from pawsona.pet import (
    SKILL_KEYS,
    TRAIT_KEYS,
    Pet,
    PetLoadError,
    describe_pet_source,
    load_pet,
    write_pet_profile,
)
from pawsona.state import LoadedState, StateError, apply_trained_state, save_trained_state
from pawsona.status import observe_status
from pawsona.tradeoff import analyze_tradeoff
from pawsona.training import normalize_feedback, scenario_for_round, train_once
from pawsona.twin import TwinError, export_twin, import_twin


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
    parser.add_argument(
        "--saves-dir",
        default="saves",
        help="Directory containing trained pet state JSON files.",
    )
    parser.add_argument(
        "--challenges-dir",
        default="challenges",
        help="Directory containing fixed public challenge definitions.",
    )

    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Load and display a pet definition.",
    )
    inspect_parser.add_argument("pet", help="Pet name, for example: hermes")
    inspect_parser.add_argument(
        "--base",
        action="store_true",
        help="Inspect the raw base profile without saved training state.",
    )

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

    status_parser = subparsers.add_parser(
        "status",
        help="Summarize observed behavior without changing state.",
    )
    status_parser.add_argument("pet", help="Pet name, for example: hermes")
    status_parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of simulated observations to run.",
    )

    eval_parser = subparsers.add_parser(
        "eval",
        help="Score behavior quality without changing state.",
    )
    eval_parser.add_argument("pet", help="Pet name, for example: hermes")

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Compare behavior scores across environments.",
    )
    benchmark_parser.add_argument("pet", help="Pet name, for example: hermes")

    tradeoff_parser = subparsers.add_parser(
        "tradeoff",
        help="Compare task performance against generalization.",
    )
    tradeoff_parser.add_argument("pet", help="Pet name, for example: hermes")

    train_parser = subparsers.add_parser(
        "train",
        help="Train a pet from a JSONL interaction dataset.",
    )
    train_parser.add_argument("pet", help="Pet name, for example: hera")
    train_parser.add_argument(
        "--data",
        required=True,
        help="Path to a JSONL interaction dataset.",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of times to replay the dataset.",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Export a pet profile and trained state.",
    )
    export_parser.add_argument("pet", help="Pet name, for example: hermes")
    export_parser.add_argument(
        "--out",
        required=True,
        help="Output .pawsona archive path.",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Import a .pawsona pet archive.",
    )
    import_parser.add_argument("archive", help="Path to a .pawsona archive.")

    challenge_parser = subparsers.add_parser(
        "challenge",
        help="Work with fixed public challenge checkpoints.",
    )
    challenge_subparsers = challenge_parser.add_subparsers(dest="challenge_command")
    challenge_subparsers.add_parser("list", help="List available challenges.")

    challenge_show_parser = challenge_subparsers.add_parser(
        "show",
        help="Show challenge details.",
    )
    challenge_show_parser.add_argument("challenge_id", help="Challenge id, for example: hera-chaos")

    challenge_start_parser = challenge_subparsers.add_parser(
        "start",
        help="Install a challenge base profile into the pets directory.",
    )
    challenge_start_parser.add_argument("challenge_id", help="Challenge id, for example: hera-chaos")

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
    play_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Run a temporary session without writing trained state.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return inspect_pet(
            args.pet,
            Path(args.pets_dir),
            Path(args.saves_dir),
            base=args.base,
        )
    if args.command == "create":
        return create_pet(Path(args.pets_dir), force=args.force)
    if args.command == "act":
        return act_pet(args.pet, Path(args.pets_dir), Path(args.saves_dir))
    if args.command == "status":
        return status_pet(
            args.pet,
            Path(args.pets_dir),
            Path(args.saves_dir),
            rounds=args.rounds,
        )
    if args.command == "eval":
        return eval_pet(args.pet, Path(args.pets_dir), Path(args.saves_dir))
    if args.command == "benchmark":
        return benchmark_cli_pet(args.pet, Path(args.pets_dir), Path(args.saves_dir))
    if args.command == "tradeoff":
        return tradeoff_pet(args.pet, Path(args.pets_dir), Path(args.saves_dir))
    if args.command == "train":
        return train_pet_from_dataset(
            args.pet,
            Path(args.pets_dir),
            Path(args.saves_dir),
            data_path=Path(args.data),
            epochs=args.epochs,
        )
    if args.command == "export":
        return export_pet(
            args.pet,
            Path(args.pets_dir),
            Path(args.saves_dir),
            out_path=Path(args.out),
        )
    if args.command == "import":
        return import_pet_archive(
            Path(args.archive),
            Path(args.pets_dir),
            Path(args.saves_dir),
        )
    if args.command == "challenge":
        return challenge_command(
            args.challenge_command,
            Path(args.challenges_dir),
            Path(args.pets_dir),
            Path(args.saves_dir),
            challenge_id=getattr(args, "challenge_id", None),
        )
    if args.command == "play":
        return play_pet(
            args.pet,
            Path(args.pets_dir),
            Path(args.saves_dir),
            rounds=args.rounds,
            no_save=args.no_save,
        )

    parser.print_help()
    return 0


def inspect_pet(name: str, pets_dir: Path, saves_dir: Path, base: bool = False) -> int:
    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir, use_saved=not base)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    print(f"Name: {pet.name}")
    print(f"Species: {pet.species}")
    print(f"Breed: {pet.breed}")
    print(f"Age: {pet.age}")
    print(f"Sex: {pet.sex}")
    print(f"Neutered: {str(pet.neutered).lower()}")
    _print_state_summary(base, loaded_state)
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


def eval_pet(name: str, pets_dir: Path, saves_dir: Path) -> int:
    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    report = evaluate_pet(pet)
    print(f"{pet.name} Evaluation")
    _print_state_summary(base=False, loaded_state=loaded_state)
    for result in report.results:
        print(f"{result.metric}: {result.score}%")
    print(f"Overall Score: {report.overall_score}%")
    return 0


def benchmark_cli_pet(name: str, pets_dir: Path, saves_dir: Path) -> int:
    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    report = benchmark_pet(pet)
    print(f"{pet.name} Benchmark")
    _print_state_summary(base=False, loaded_state=loaded_state)
    for environment_score in report.environment_scores:
        print(f"{environment_score.environment} Accuracy: {environment_score.score}%")
    print(f"Generalization Score: {report.generalization_score}")
    return 0


def tradeoff_pet(name: str, pets_dir: Path, saves_dir: Path) -> int:
    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    report = analyze_tradeoff(pet)
    print(f"Pawsona Tradeoff Report: {pet.name}")
    _print_state_summary(base=False, loaded_state=loaded_state)
    print(f"Task Score: {report.task_score}%")
    print(f"Generalization Score: {report.generalization_score}%")
    print(f"Overfit Score: {report.overfit_score}%")
    print("")
    print("Interpretation:")
    print(report.interpretation)
    return 0


def train_pet_from_dataset(
    name: str,
    pets_dir: Path,
    saves_dir: Path,
    data_path: Path,
    epochs: int,
) -> int:
    try:
        pet, _loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
        samples = load_jsonl_dataset(data_path)
        trained_pet, report = train_from_dataset(pet, samples, epochs)
        save_path = save_trained_state(
            trained_pet,
            name,
            saves_dir,
            report.applied_updates,
            source_profile=describe_pet_source(name, pets_dir),
        )
    except (PetLoadError, StateError, DatasetError) as error:
        print(f"error: {error}")
        return 1

    print(f"Pawsona Dataset Training: {name}")
    print(f"Dataset: {data_path}")
    print(f"Epochs: {epochs}")
    print(f"Samples loaded: {report.samples_loaded}")
    print(f"Samples seen: {report.samples_seen}")
    print(f"Applied updates: {report.applied_updates}")
    print(f"Skipped samples: {report.skipped_samples}")
    print("")
    print("Before:")
    _print_metric_summary(report.before)
    print("")
    print("After:")
    _print_metric_summary(report.after)
    print("")
    print(f"Saved trained state: {save_path}")
    return 0


def export_pet(name: str, pets_dir: Path, saves_dir: Path, out_path: Path) -> int:
    try:
        base_pet = load_pet(name, pets_dir)
        trained_pet, loaded_state = apply_trained_state(base_pet, name, saves_dir)
        result = export_twin(
            base_pet,
            trained_pet,
            name,
            loaded_state,
            out_path,
            source_profile=describe_pet_source(name, pets_dir),
        )
    except (PetLoadError, StateError, TwinError) as error:
        print(f"error: {error}")
        return 1

    print(f"Exported Pawsona twin: {result.path}")
    print(f"Pet Key: {result.pet_key}")
    print(f"Rounds Trained: {result.rounds_trained}")
    return 0


def import_pet_archive(archive_path: Path, pets_dir: Path, saves_dir: Path) -> int:
    try:
        result = import_twin(archive_path, pets_dir, saves_dir)
    except (StateError, TwinError) as error:
        print(f"error: {error}")
        return 1

    print(f"Imported Pawsona twin: {archive_path}")
    print(f"Pet Key: {result.pet_key}")
    profile_action = "written" if result.wrote_profile else "kept existing"
    print(f"Base Profile: {profile_action} at {result.profile_path}")
    print(f"Trained State: written at {result.state_path}")
    print(f"Rounds Trained: {result.rounds_trained}")
    return 0


def challenge_command(
    command: str | None,
    challenges_dir: Path,
    pets_dir: Path,
    saves_dir: Path,
    challenge_id: str | None = None,
) -> int:
    if command is None:
        print("error: challenge requires a subcommand: list, show, or start")
        return 1
    if command == "list":
        return list_challenge_command(challenges_dir)
    if command == "show" and challenge_id is not None:
        return show_challenge_command(challenge_id, challenges_dir)
    if command == "start" and challenge_id is not None:
        return start_challenge_command(challenge_id, challenges_dir, pets_dir, saves_dir)
    print(f"error: unknown challenge subcommand '{command}'")
    return 1


def list_challenge_command(challenges_dir: Path) -> int:
    try:
        challenges = list_challenges(challenges_dir)
    except ChallengeError as error:
        print(f"error: {error}")
        return 1

    if not challenges:
        print("No challenges found.")
        return 0

    print("Available Challenges:")
    for challenge in challenges:
        print(f"  {challenge.id}: {challenge.name} ({challenge.difficulty})")
    return 0


def show_challenge_command(challenge_id: str, challenges_dir: Path) -> int:
    try:
        challenge = load_challenge(challenge_id, challenges_dir)
    except ChallengeError as error:
        print(f"error: {error}")
        return 1

    print(f"Challenge: {challenge.name}")
    print(f"ID: {challenge.id}")
    print(f"Difficulty: {challenge.difficulty}")
    print(f"Version: {challenge.version}")
    print(f"Goal: {challenge.goal}")
    print(f"Base Pet: {challenge.base_pet}")
    print("Focus:")
    for item in challenge.focus:
        print(f"  {item}")
    print("Metrics:")
    for item in challenge.metrics:
        print(f"  {item}")
    print("Training Scenarios:")
    for item in challenge.training_scenarios:
        print(f"  {item}")
    print("Benchmark Environments:")
    for item in challenge.benchmark_environments:
        print(f"  {item}")
    return 0


def start_challenge_command(
    challenge_id: str,
    challenges_dir: Path,
    pets_dir: Path,
    saves_dir: Path,
) -> int:
    try:
        result = start_challenge(challenge_id, challenges_dir, pets_dir, saves_dir)
    except ChallengeError as error:
        print(f"error: {error}")
        return 1

    print(f"Started Challenge: {result.challenge.name}")
    print(f"Challenge ID: {result.challenge.id}")
    action = "written" if result.wrote_profile else "kept existing"
    print(f"Base Profile: {action} at {result.profile_path}")
    if result.has_saved_state:
        print(f"Saved State: existing at {result.save_path}")
    else:
        print("Saved State: clean")
    print(f"Next: pawsona play {result.challenge.id} --rounds 30")
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


def act_pet(name: str, pets_dir: Path, saves_dir: Path) -> int:
    try:
        pet, _loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    action, scores = choose_action(pet)
    print(f"Scenario: {DEFAULT_SCENARIO.name}")
    print(f"{pet.name} action: {action}")
    print("Scores:")
    for score_name, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        print(f"  {score_name}: {score}")
    return 0


def status_pet(name: str, pets_dir: Path, saves_dir: Path, rounds: int) -> int:
    if rounds < 1:
        print("error: --rounds must be 1 or greater")
        return 1

    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    observation = observe_status(pet, rounds=rounds)
    print(f"{pet.name} Status")
    _print_state_summary(base=False, loaded_state=loaded_state)
    print(f"Observed Rounds: {observation.rounds}")
    print("Behavior Frequencies:")
    for action, count in observation.action_counts.most_common():
        print(f"  {action}: {count}/{observation.rounds}")
    print("Scenario Observations:")
    for scenario_name, counts in observation.scenario_counts.items():
        if not counts:
            continue
        action, count = counts.most_common(1)[0]
        print(f"  {scenario_name}: {action} {count}/{sum(counts.values())}")
    return 0


def play_pet(
    name: str,
    pets_dir: Path,
    saves_dir: Path,
    rounds: int,
    no_save: bool = False,
) -> int:
    if rounds < 1:
        print("error: --rounds must be 1 or greater")
        return 1

    try:
        pet, loaded_state = _load_cli_pet(name, pets_dir, saves_dir)
    except (PetLoadError, StateError) as error:
        print(f"error: {error}")
        return 1

    print(f"Training {pet.name} for {rounds} rounds")
    if loaded_state is not None:
        print(f"Loaded saved state: {loaded_state.path}")
        print(f"Rounds trained: {loaded_state.rounds_trained}")
    if no_save:
        print("Save mode: off")
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
    if completed_rounds > 0 and not no_save:
        try:
            path = save_trained_state(
                pet,
                name,
                saves_dir,
                completed_rounds,
                source_profile=describe_pet_source(name, pets_dir),
            )
        except StateError as error:
            print(f"error: {error}")
            return 1
        print(f"Saved trained state: {path}")
    elif no_save:
        print("Saved trained state: skipped")
    return 0


def _load_cli_pet(
    name: str,
    pets_dir: Path,
    saves_dir: Path,
    use_saved: bool = True,
) -> tuple[Pet, LoadedState | None]:
    pet = load_pet(name, pets_dir)
    if not use_saved:
        return pet, None
    return apply_trained_state(pet, name, saves_dir)


def _print_state_summary(base: bool, loaded_state: LoadedState | None) -> None:
    if base:
        print("State: base")
        return
    if loaded_state is None:
        print("State: base")
        return
    print("State: trained")
    print(f"Save File: {loaded_state.path}")
    print(f"Rounds Trained: {loaded_state.rounds_trained}")
    if loaded_state.last_updated is not None:
        print(f"Last Updated: {loaded_state.last_updated}")


def _print_metric_summary(report) -> None:
    print(f"  Eval Overall: {report.task_score}%")
    print(f"  Generalization: {report.generalization_score}%")
    print(f"  Overfit: {report.overfit_score}%")


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
