# FonRemover — project handbook

> **Read first:** `notes/ai_agent_playbook.md` — the binding regulation for how
> to work in this project (6-point cycle, propose-don't-act, cards, git gating).
> Then read `MEMORY.md` and `project.ini`.

## What this is

A tool to **remove backgrounds from images** — makes the background transparent
and saves a PNG. Engine: [`rembg`](https://github.com/danielgatis/rembg)
(U2-Net, ONNX), running locally/offline after a one-time model download.
Interface: a `fonremover` CLI with single-file and batch (folder) modes.

## Stack

- Python ≥3.9, packaged via `pyproject.toml` (`fonremover` console script).
- Deps: `rembg[cpu]` (onnxruntime), `pillow`.
- Code in `src/fonremover/` (`core.py` = engine, `cli.py` = CLI). Tests in
  `tests/`.

## Layout (one-repo, playbook §12.2)

Code and docs share this single repo:

- `src/fonremover/`, `tests/`, `pyproject.toml`, `README.md` — the code.
- `CLAUDE.md`, `MEMORY.md`, `memory/`, `ideas/`, `notes/`, `templates/` — docs.
- `samples/` — example input images.

## Testing (agent zone, §3.4)

- Build/install: `pip install -e .`
- Lint/smoke: `fonremover --help`, `fonremover --version`
- Unit: `pytest`
- Smoke on a real image: `fonremover samples/example.png`

## Active work

- `ideas/Idea_001/` — **CLI background remover (rembg)** — closed. First
  feature; bootstrapped the repo and shipped the `fonremover` CLI.

## Git

- One repo. `project.ini [git] push_enable = true`,
  `git_repo = git@github.com:Yury-mygit/FonRemover.git`.
- Commit per stage, push after context changes and at card close (§6).
