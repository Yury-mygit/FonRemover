---
id: Idea_001
date: 2026-07-02
type: feature
status: closed
title: CLI background remover (rembg)
---

# Context

First feature of the project. See Idea.md (request) and Decision.md (rembg +
CLI). Bootstraps the repo per playbook §12.5 (one-repo layout) and ships a
working `fonremover` CLI.

# Stages

## Stage 1 — Bootstrap repo structure (playbook §12.5)

- [x] 1.1. Create one-repo layout: `notes/` (vendored playbook), `templates/`,
  `memory/`, `ideas/`, `samples/`.
- [x] 1.2. `CLAUDE.md` thin handbook linking to the playbook.
- [x] 1.3. `project.ini.template` (committed) + `project.ini` (gitignored) +
  `.gitignore` per §5b.1.
- [x] 1.4. `MEMORY.md` index + initial memory entries.
- [x] 1.5. Move the provided sample to `samples/example.png`.

## Stage 2 — Implement the CLI (rembg)

- [x] 2.1. `src/fonremover/core.py` — `BackgroundRemover` wrapping rembg.
- [x] 2.2. `src/fonremover/cli.py` — argparse CLI, single + batch modes.
- [x] 2.3. `pyproject.toml` with `fonremover` console entry point + deps.
- [x] 2.4. `tests/test_cli.py` — parsing / output-path unit tests.
- [x] 2.5. `README.md` — install + usage.

## Stage 3 — Testing (agent zone, §3.4)

- [x] 3.1. `pip install -e .` succeeds in a venv.
- [x] 3.2. `fonremover --version` / `--help` answer without crash.
- [x] 3.3. `pytest` green (3 passed).
- [x] 3.4. Smoke: `samples/example.png` -> RGBA PNG with alpha (verified).

## Stage 4 — User-zone testing (deferred)

- [ ] 4.1. User runs the CLI on their own real photos and confirms quality.

## Stage 5 — Commit + push + close

- [x] 5.1. Every code-side [x] above.
- [x] 5.2. `status: closed` in this Card.md frontmatter.
- [x] 5.3. Update CLAUDE.md (stack + active-work index).
- [x] 5.4. `git init`, first commit, push to `Yury-mygit/FonRemover`.
- [x] 5.5. "Open questions" empty.

# Open questions

(none)

# Resolved questions

- Engine + interface choice → resolved in Decision.md (rembg + CLI), confirmed
  by the user 2026-07-02.
- Does the remote already exist? → yes, `FonRemover.git` exists and is empty, so
  a fresh history can be pushed directly (no unrelated-histories).
