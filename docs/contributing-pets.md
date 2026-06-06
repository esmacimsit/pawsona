# Contributing Public Content

Personal pets do not need a Pull Request. Use `pawsona create` for local pets and keep the generated profile on your machine.

Pull Requests are for curated public content:

- example dogs under `pets/community/`
- official or community challenge checkpoints under `challenges/`
- benchmark scenarios, datasets, docs, and evaluation improvements

## Community Pets

Community pet profiles live in `pets/community/`.

Start from `pets/template.yaml`, fill every identity field, and use numeric trait and skill values from `0.0` to `1.0`.

For the first public version, pet profiles should describe dogs only.

Before opening a Pull Request, run:

```bash
pawsona inspect your_pet_name
pawsona validate
```

## Community Challenges

Community challenge profiles live in `challenges/community/<challenge-id>/`.

Use the same shape as:

```text
challenges/hera-chaos/
  base.yaml
  challenge.yaml
```

The challenge id must match the folder name and the `id` field in `challenge.yaml`.

Before opening a Pull Request, run:

```bash
pawsona challenge show your-challenge-id
pawsona validate
```

## Pull Request Checklist

- The content is intended as a public example or public challenge.
- Personal/private pet data has been removed or anonymized.
- Pet profiles use valid trait, skill, and memory values.
- Challenge metadata includes id, name, difficulty, version, goal, focus, metrics, scenarios, and environments.
- `pawsona validate` passes.
- No generated save files, build artifacts, or local `.pawsona` exports are included.

## Reminder

You do not need a Pull Request to use Pawsona with your own pet. PRs are optional and only for content you want to make public.
