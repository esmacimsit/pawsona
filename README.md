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

## Observe Status

```bash
pawsona status hermes
pawsona status hera
```

Status runs simulated observations and summarizes behavior frequencies. It does not train the pet or write save files.

## Evaluate Behavior

```bash
pawsona eval hermes
pawsona eval hera
```

Evaluation scores repeatable task scenarios such as recall, focus, and calm greeting. It reads the effective trained state and does not write save files.

## Benchmark Generalization

```bash
pawsona benchmark hermes
pawsona benchmark hera
```

Benchmark compares familiar and transfer environments, then reports a generalization score. It reads the effective trained state and does not write save files.

## Check Training Tradeoffs

```bash
pawsona tradeoff hermes
pawsona tradeoff hera
```

Tradeoff compares the evaluation task score against benchmark generalization and reports a simple overfit score. It is read-only and does not write save files.

## Train From A Dataset

```bash
pawsona train hera --data examples/hera-calm.jsonl --epochs 3
```

Dataset training replays JSONL interaction samples, updates the same saved trained state used by `play`, and prints before/after evaluation, generalization, and overfit scores.

Each JSONL line should be an object like:

```json
{"scenario":"owner_arrives_home","environment":"home","cue":"greeting","distraction":"door_noise","action":"observe_calmly","feedback":"reward","target_skill":"settle"}
```

## Export A Digital Twin

```bash
pawsona export hermes --out hermes.pawsona
pawsona import hermes.pawsona
```

Exports preserve the base profile, trained state, and Pawsona package metadata in one `.pawsona` archive. Import writes trained state and keeps an existing base profile if one is already present.

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
examples/
  hera-calm.jsonl
pawsona/
  benchmark.py
  cli.py
  dataset.py
  behavior.py
  pet.py
  simple_yaml.py
  state.py
  status.py
  tradeoff.py
  twin.py
  evaluation.py
  training.py
pets/
  hermes.yaml
  hera.yaml
  template.yaml
  community/
saves/
docs/
```
