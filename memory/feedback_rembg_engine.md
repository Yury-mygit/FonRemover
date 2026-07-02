---
name: rembg engine choice
description: Background removal uses local rembg (U2-Net), CLI-first
type: feedback
---

The background-removal engine is **rembg** (local, U2-Net/ONNX) and the primary
interface is a **CLI with batch processing**. Chosen over the remove.bg cloud
API and plain OpenCV. See `ideas/Idea_001/Decision.md`.

**Why.** The user wanted free, offline, good-quality removal without an API key;
rembg fits. CLI-first keeps the core reusable for a possible later web UI.

**How to apply.** Build features on top of the rembg engine and the `fonremover`
CLI. Before switching engines (e.g. to a cloud API) or adding a web UI, return
to Point 2 (Decision) and confirm with the user.
