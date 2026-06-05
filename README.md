# Pawsona

[![PyPI version](https://img.shields.io/pypi/v/pawsona.svg)](https://pypi.org/project/pawsona/)

Train personalities, not commands.

Pawsona is a terminal-based pet personality and training simulator inspired by reinforcement learning, memory, adaptation, generalization, and overfitting.

The first public version focuses on dogs. The behavior model is intentionally simple: it is a small scoring engine for playable training loops, not a biologically realistic simulator.

## Current Status

This repository is in the early CLI phase. Pawsona can load built-in pet profiles, inspect their model state, create new YAML profiles, generate simple behavior-model actions, and persist trained skills and memory between CLI runs.

## Try It

After release, the main install command will be:

```bash
pip install pawsona
```

Primary CLI:

```bash
pawsona --help
```

Short alias:

```bash
paw --help
```

If `paw` conflicts with another command on your machine, use `pawsona`.

## Environment

Create and activate the conda environment:

```bash
conda create -n paw python=3.11 pip
conda activate paw
```

Install the project components from `requirements.txt`:

```bash
python -m pip install -r requirements.txt
pawsona --help
```

## Inspect A Pet

```bash
pawsona inspect hermes
pawsona inspect hera
```

Inspect only the raw base YAML profile:

```bash
pawsona inspect hermes --base
```

## Create A Pet

```bash
pawsona create
```

Trait questions use a `1` to `5` scale and are normalized into `0.0` to `1.0` YAML values.

## Generate An Action

```bash
pawsona act hermes
pawsona act hera
```

## Train In The Terminal

```bash
pawsona play hermes
pawsona play hera
```

Training sessions run for 10 rounds by default. Feedback options are `reward`, `praise`, `ignore`, and `correct`.

Training updates are saved to `saves/<pet>.json`. Base YAML profiles are not modified.

Run a temporary training session without writing a save file:

```bash
pawsona play hermes --no-save
```

## Project Shape

```text
pawsona/
  cli.py
  behavior.py
  pet.py
  simple_yaml.py
  state.py
  training.py
pets/
  hermes.yaml
  hera.yaml
  template.yaml
  community/
saves/
docs/
```
