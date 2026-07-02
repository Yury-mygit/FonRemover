---
id: Idea_001
date: 2026-07-02
status: agreed
---

# Restated task

"Did I understand right that we need a tool that removes the background from
images (transparent PNG output), built and documented per the playbook, with
code + docs in one repo `Yury-mygit/FonRemover`?"

# Options considered

## Engine

- **A. rembg (local, U2-Net/ONNX)** — free, offline after a one-time model
  download, good quality / no API key. Adds a heavy dependency (onnxruntime).
- **B. remove.bg (cloud API)** — excellent quality, but paid, needs an API key,
  and requires internet on every request.
- **C. OpenCV (GrabCut/thresholding)** — no ML dependency, but noticeably worse
  quality on complex backgrounds.

## Interface

- **CLI + batch** — process one file or a whole folder; simple, scriptable.
- **Web app** — drag-and-drop UI with preview; nicer UX, more code.
- **CLI first, web later** — build the reusable core, wrap it later.

# Chosen direction

Engine **A (rembg, local)** + Interface **CLI with batch processing** — chosen
because it is free, offline, good quality, and the simplest scriptable base.
Confirmed by the user on 2026-07-02.

# Constraints from the user

- Code + docs in a single repository (`Yury-mygit/FonRemover`) — one-repo
  layout (playbook §12.2).
- Follow the ai-agent-playbook regulation.

# Open questions before Card

1. None — direction confirmed.
