# Pawsona Project Brief

Last updated: 2026-06-05

## Short Summary

Pawsona is now a working early-stage Python CLI project for a tiny trainable pet behavior model framework.

The project can currently:

- run as a Python package
- expose `pawsona` as the primary CLI command
- expose `paw` as a short CLI alias
- load dog profiles from YAML
- inspect built-in pets
- create new pet profiles from a questionnaire
- score actions from pet traits, skills, memory, and scenario state
- run a 10-round interactive training loop in the terminal
- install into a dedicated conda environment named `paw`
- install from PyPI with `pip install pawsona`

The current implementation covers the practical foundation for milestones M0 through M4.

The initial alpha PyPI release has been published as `pawsona==0.1.0a1`.

The first public version focuses on dogs. The broader project language still uses "pet" because future versions may expand beyond dogs.

## Release Status

Status: published.

Release:

- PyPI package: `pawsona`
- Version: `0.1.0a1`
- Primary CLI: `pawsona`
- Short alias: `paw`
- Python import package: `pawsona`
- License: MIT
- Author: `esmacimsit`
- Maintainer: `esmacimsit`
- Git tag: `v0.1.0a1`
- Release commit: `ed8ae9f Release 0.1.0a1`

Published package:

```bash
pip install pawsona
```

Project URL:

```text
https://pypi.org/project/pawsona/
```

Post-publish smoke test was run in a clean virtual environment under `/tmp/pawsona-test`.

Verified from PyPI:

```bash
pip install pawsona
pawsona --help
paw --help
pawsona inspect hermes
pawsona inspect hera
pawsona act hermes
pawsona act hera
```

All commands passed. Built-in Hermes and Hera profiles load correctly after installing from PyPI, so packaged pet data is included and usable.

## Original Direction

The project vision is:

> Train personalities, not commands.

Pawsona treats pets as trainable personality models rather than static game entities. Breed, personality traits, skills, memory, feedback, and environment are all part of the model state.

The first version intentionally avoids LLMs. The core experience is terminal-based gameplay and model updates.

## Current Milestone Status

### M0 - Project Bootstrap

Status: implemented.

Done:

- created Python package structure under `pawsona/`
- added CLI entrypoint
- added `pyproject.toml`
- added `README.md`
- added `requirements.txt`
- added built-in pet YAML files:
  - `pets/hermes.yaml`
  - `pets/hera.yaml`
- added `saves/` directory placeholder
- added `pets/community/` directory placeholder
- verified CLI help works

Verification command:

```bash
conda run -n paw pawsona --help
```

### M1 - Pet Profiles

Status: implemented.

Done:

- created `Pet` model in `pawsona/pet.py`
- defined required profile fields:
  - `name`
  - `species`
  - `breed`
  - `age`
  - `sex`
  - `neutered`
  - `traits`
  - `skills`
  - `memory`
- added schema validation for required identity fields
- added validation for all required trait keys
- added validation for all required skill keys
- added numeric range validation for traits, skills, and memory values
- added YAML loading
- added readable profile output via `pawsona inspect`
- supports built-in pets and community pets

Verification commands:

```bash
conda run -n paw pawsona inspect hermes
conda run -n paw pawsona inspect hera
```

### M2 - Profile Creator

Status: implemented.

Done:

- added `pawsona create`
- asks identity questions:
  - name
  - breed
  - age
  - sex
  - neutered
- asks trait questions using a 1-5 scale
- normalizes 1-5 answers into 0.0-1.0 values
- initializes skills to `0.0`
- initializes memory to `{}`
- writes output to `pets/<name>.yaml`
- added `--force` to overwrite an existing generated profile

Example command:

```bash
conda run -n paw pawsona create
```

### M3 - First Behavior Model

Status: implemented.

Done:

- added `pawsona/behavior.py`
- defined `Scenario`
- added default scenario:
  - `owner_arrives_home`
  - environment: `home`
  - cue: `greeting`
  - distraction: `door_noise`
  - target action: `observe_calmly`
  - target skill: `settle`
- added action scoring
- action scores use:
  - traits
  - skills
  - memory
  - environment
  - distraction
- added `pawsona act <pet>`
- Hermes and Hera produce different behavior under the same scenario

Current action space:

- `observe_calmly`
- `jump_excitedly`
- `bark_at_noise`
- `bring_toy`
- `return_to_owner`

Verification commands:

```bash
conda run -n paw pawsona act hermes
conda run -n paw pawsona act hera
```

Observed behavior:

- Hermes tends toward `observe_calmly`
- Hera tends toward `jump_excitedly`

### M4 - Interactive Training Loop

Status: implemented.

Done:

- added `pawsona/training.py`
- added `pawsona play <pet>`
- default session length is 10 rounds
- added `--rounds` option for shorter or longer sessions
- generates scenarios per round
- generates model actions per scenario
- collects terminal feedback
- updates skills and memory in the active session
- prints small training updates after each round
- handles EOF cleanly during piped/non-interactive input

Training updates are session-only until M5. They are intentionally not persisted yet.

Feedback options:

- `1` or `reward`
- `2` or `praise`
- `3` or `ignore`
- `4` or `correct`
- `q`, `quit`, or `exit`

Current training scenarios:

- `owner_arrives_home`
- `recall_from_yard`
- `fetch_at_park`
- `focus_near_food`
- `settle_during_noise`

Verification commands:

```bash
conda run --no-capture-output -n paw pawsona play hermes
conda run --no-capture-output -n paw pawsona play hera
```

Scripted 10-round tests were also run successfully for both Hermes and Hera.

## Environment Work Completed

A conda environment named `paw` was created.

Created with:

```bash
conda create -n paw python=3.11 pip
```

Installed with:

```bash
conda run -n paw python -m pip install -r requirements.txt
```

Verified:

```bash
conda run -n paw python --version
conda run -n paw python -m pip show pawsona
conda run -n paw python -c 'import yaml; print(yaml.__version__)'
```

Current environment facts:

- env name: `paw`
- Python version: `3.11.15`
- PyYAML version: `6.0.3`
- Pawsona is installed editable from this repo

## Requirements

`requirements.txt` now contains:

```text
PyYAML>=6.0.2
-e .
```

Why:

- `PyYAML` provides the normal `import yaml` path.
- `-e .` installs the local project in editable mode so code changes are immediately reflected in the CLI.

`pyproject.toml` also declares:

```toml
dependencies = [
  "PyYAML>=6.0.2",
]
```

This keeps package metadata and requirements aligned.

## Packaging Fix

Editable install initially failed because setuptools saw multiple top-level folders in the flat project layout:

- `pawsona`
- `pets`
- `saves`

The fix was to explicitly tell setuptools to package only `pawsona*`.

Added to `pyproject.toml`:

```toml
[tool.setuptools.packages.find]
include = ["pawsona*"]
```

## Files Added Or Changed

### Project And Packaging

`pyproject.toml`

- defines package metadata
- defines Python requirement
- defines dependency on `PyYAML`
- defines alpha version `0.1.0a1`
- defines MIT license metadata
- defines author and maintainer as `esmacimsit`
- defines CLI scripts:

```toml
pawsona = "pawsona.cli:main"
paw = "pawsona.cli:main"
```

- restricts setuptools package discovery to `pawsona*`
- includes packaged built-in pet data:

```toml
[tool.setuptools.package-data]
pawsona = ["builtin_pets/*.yaml"]
```

`requirements.txt`

- installs `PyYAML`
- installs project editable with `-e .`

`.gitignore`

- ignores macOS metadata
- ignores local milestone notes
- ignores Python caches
- ignores virtual environments
- ignores build outputs
- ignores generated save files while keeping `saves/.gitkeep`

The save ignore rule is:

```gitignore
saves/*
!saves/.gitkeep
```

Important ignored files/directories:

- `.DS_Store`
- `milestones.md`
- `__pycache__/`
- `.venv/`
- `.conda/`
- `.pytest_cache/`
- `dist/`
- `build/`
- `*.egg-info/`
- `saves/*`
- `!saves/.gitkeep`

### CLI And Runtime Code

`pawsona/__init__.py`

- package marker
- defines version `0.1.0a1`

`pawsona/__main__.py`

- allows:

```bash
python -m pawsona
```

`pawsona/cli.py`

- main CLI parser
- commands:
  - `inspect`
  - `create`
  - `act`
  - `play`
- includes input helpers for text, numbers, booleans, choices, and feedback

`pawsona/pet.py`

- `Pet` dataclass
- `PetLoadError`
- trait and skill key definitions
- YAML pet loading
- profile writing
- schema validation
- built-in pet fallback loading from package data

`pawsona/simple_yaml.py`

- YAML read/write helper
- uses `PyYAML` when available
- keeps a small fallback parser/writer for simple mappings
- fallback supports the simple project YAML shape

`pawsona/behavior.py`

- `Scenario` dataclass
- default scenario
- action scoring
- action selection

`pawsona/training.py`

- training scenarios
- feedback normalization
- action-to-skill mapping
- single-round training update logic
- memory update logic
- value clamping

`pawsona/builtin_pets/hermes.yaml`

- packaged Hermes profile used after `pip install pawsona`
- mirrors the current built-in Hermes profile

`pawsona/builtin_pets/hera.yaml`

- packaged Hera profile used after `pip install pawsona`
- mirrors the current built-in Hera profile

### Pet Data

`pets/hermes.yaml`

- built-in Hermes profile
- current source of truth should be the user-edited version
- do not overwrite casually

`pets/hera.yaml`

- built-in Hera profile
- designed to behave differently from Hermes

`pets/template.yaml`

- template for future community pet profiles

`pets/community/.gitkeep`

- keeps community directory in git

### Save Data

`saves/.gitkeep`

- keeps save directory in git

Generated save files should be ignored. Persistence is planned for M5.

### Docs

`README.md`

- project overview
- environment setup
- install commands
- inspect/create/act/play usage
- project structure

`docs/vision.md`

- original project vision

`docs/contributing-pets.md`

- early community pet contribution notes

`docs/brief.md`

- this file

## Current CLI Commands

Show help:

```bash
pawsona --help
```

Inspect a pet:

```bash
pawsona inspect hermes
pawsona inspect hera
```

Create a pet profile:

```bash
pawsona create
```

Generate one action:

```bash
pawsona act hermes
pawsona act hera
```

Train interactively:

```bash
pawsona play hermes
pawsona play hera
```

Train for a custom number of rounds:

```bash
pawsona play hermes --rounds 3
```

## Verified Commands

These commands have been run successfully:

```bash
conda run -n paw pawsona --help
conda run -n paw pawsona inspect hermes
conda run -n paw pawsona inspect hera
conda run -n paw pawsona act hermes
conda run -n paw pawsona act hera
conda run -n paw python -m compileall pawsona
conda run -n paw python -c 'import yaml; print(yaml.__version__)'
```

Scripted play tests were also run:

```bash
printf '1\n2\n4\n3\n1\n2\n4\n3\n1\n2\n' | conda run --no-capture-output -n paw pawsona play hermes
printf '4\n1\n2\n1\n3\n4\n1\n2\n1\n3\n' | conda run --no-capture-output -n paw pawsona play hera
```

Both completed:

```text
Completed rounds: 10/10
```

## Current Git State Notes

Expected tracked/untracked project files include:

- `.gitignore`
- `README.md`
- `docs/contributing-pets.md`
- `docs/brief.md`
- `docs/vision.md`
- `pawsona/`
- `pets/`
- `pyproject.toml`
- `requirements.txt`
- `saves/.gitkeep`

Expected ignored local/generated files include:

- `.DS_Store`
- `dist/`
- `milestones.md`
- `pawsona.egg-info/`
- `pawsona/__pycache__/`

`milestones.md` is intentionally ignored because it is being used as a local planning/checklist file.

`dist/` is intentionally ignored because build artifacts can be regenerated with:

```bash
conda run -n paw python -m build
```

The alpha release artifacts that were checked before publishing were:

```text
dist/pawsona-0.1.0a1-py3-none-any.whl
dist/pawsona-0.1.0a1.tar.gz
```

`twine check dist/*` passed before upload.

## Known Design Decisions

### No Persistence Yet

Training updates currently live only during the active `play` session.

This is intentional. Persistent trained state belongs to M5.

Planned M5 shape:

- keep YAML base profile unchanged
- write trained state to JSON under `saves/`
- load saved JSON state when available
- make `inspect` show effective state after applying saved training

### Hermes And Hera Are User-Owned Data

Hermes and Hera are built-in pets, but their exact YAML content may be edited by the user.

Future code changes should avoid overwriting these profiles unless the task explicitly says to edit them.

For PyPI installs, copies of Hermes and Hera also live under `pawsona/builtin_pets/` as packaged data. If the root `pets/` profiles change intentionally, update the packaged copies before the next release.

### YAML Loading

The project now depends on PyYAML, so normal YAML loading is available.

`simple_yaml.py` still contains a small fallback parser/writer. This keeps the project resilient, but PyYAML is the real dependency path.

### Behavior Model Is Simple On Purpose

The current behavior model is not meant to be biologically realistic.

It is a small scoring engine that makes the project playable and gives later milestones something concrete to evaluate, benchmark, and persist.

## Next Recommended Step

Next milestone: M5 - Persistence.

Recommended implementation path:

1. Add `pawsona/state.py`.
2. Save trained state to `saves/<pet>.json`.
3. Keep YAML as immutable base profile.
4. Merge saved state into loaded pet during `inspect`, `act`, and `play`.
5. Add `--no-save` or `--reset` later if needed.

The most important M5 acceptance test:

```bash
pawsona play hermes
pawsona inspect hermes
```

After restarting the CLI, trained skill and memory changes should still appear.
