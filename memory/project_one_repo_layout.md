---
name: Single repo for code + docs
description: One-repo layout; push target is Yury-mygit/FonRemover
type: project
---

FonRemover uses the playbook's **one-repo layout** (§12.2): code
(`src/`, `tests/`, `pyproject.toml`) and docs (`CLAUDE.md`, `MEMORY.md`,
`memory/`, `ideas/`, `notes/`, `templates/`) live in **one** git repo.
`push_enable = true`, remote `git@github.com:Yury-mygit/FonRemover.git`.

**Why.** The user explicitly asked for code and docs in a single repository, so
there is no separate context repo — the same remote is both.

**How to apply.** Commit code and docs together; one push target. Don't propose
splitting into `docs/` + `code/` repos unless the user asks.
