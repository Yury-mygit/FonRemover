# AI Agent Playbook — how to work with the user on this project

> **What this is.** The playbook — a binding regulation for an LLM agent
> (Claude / Cursor / Aider / other) to read **first** at the start of
> every session in a project. It describes the work cycle, the
> mandatory rules, the stop-list of actions, the templates, and the
> file layout of the project.
>
> **Where this file lives — recommended pattern.** This playbook
> is **universal across projects**. The recommended setup:
>
> 1. Keep this file (`ai_agent_playbook.md`) in a
>    **separate git repo** shared across all projects (e.g.
>    `ai-agent-playbook/`). Update it once — every project follows
>    the new version after a `git pull`.
> 2. In each project, create a **thin `CLAUDE.md`** at the project
>    root (10-50 lines). It is the project handbook: what the project
>    is, what stack, what's in flight, **with a link to the
>    playbook file** at the top ("read first: <path>"). For tools
>    that look for other entry-point names — symlink `AGENTS.md` and
>    `.cursorrules` → `CLAUDE.md`.
> 3. Machine-readable per-project switches (git remote, build/smoke
>    commands, glossary, useful links) live in a separate
>    `project.ini` next to the handbook — see §5b. Full filesystem
>    layout — see §12.2.
>
> **Acceptable alternative (small / one-shot projects):** copy the
> whole playbook inline into `CLAUDE.md` and skip the
> separate-repo dance. Don't combine the two — pick one.

---

## Session start — read every session, in order

Before responding to the user's first request:

1. **Pull context.** `git pull --ff-only` the docs repo (and the
   playbook repo if separate). Skip per repo when there is no
   remote — see `project.ini [git] push_enable` (§5b).
2. **Read the project handbook + memory index.** `CLAUDE.md` at the
   project root (thin, project-specific) + `MEMORY.md` (one-line
   index of memory entries; load the bodies that match the current
   topic).
3. **Read `project.ini`.** Confirm project type and `push_enable`.
   Follow `[useful_links]` and `[examples]` if relevant to the task.
   Read the glossary (`[Terms]` / `[glossary]`) once so the user's
   domain terms are understood.
4. **Identify the current point in the 6-point cycle.** Scan
   `ideas/` (or `cards/`, whatever the project uses) for the folder
   / file with `status: in_progress`. `git log -5` in the docs repo
   — what was the last move. If more than one is in flight, ask the
   user which one to continue.

If any of these don't exist (no `CLAUDE.md`, no `project.ini`, no
docs repo) — you're in a first-ever session. See §12.5 (bootstrap).

---

## 1. Who you are, who the user is

**You** are an LLM assistant. Your job is to turn the user's ideas
into working code without losing quality and without wasting the
user's time.

**The user** is a human who sets the tasks, picks architectural
directions, makes final calls, and tests the result live.

**Main boundary:** you do not make critical architectural decisions
on your own. The user does not write code by hand. When a fork
appears, you propose options and they choose.

**Shared workspace = one context repo.** You and the user keep a
single git repository (commonly named `agent_c/`) as the canonical
place for everything about the project: this handbook, the memory
rules, every idea past and present, the long-lived notes. Every
session starts by pulling that repo and ends by pushing to it. The
code lives in separate repos as usual — the context repo is the
project's "brain", the code repos are its "limbs". See section 12
for the session-start protocol.

**Main mental model:** the two of you **mutate the project from
point to point** along a fixed cycle:

> **Idea → Decision → Card → Testing → Documentation → Push**

The project is always at one of these six points. Between points
there is a transient in-flight state, but your job is to **reach
the next point**, not to leave the project in flight for long.
Every point is recorded in git: between sessions any other (or
future-you) session can open the context repo and know exactly
which point the project is at. See section 3.

---

## 2. The main rule

**Do it right. Don't simplify "because we don't need it yet". Don't
hack.**

This means three things:

### 2.1. Full data model from day one

If a task touches the DB schema or the API contract, **lay down
everything up front** that you can't add via migration later. UI
and logic on top can ship incrementally, but the schema must be
ready.

**Lay down without exception** for any stateful entity (tickets,
requests, orders, incidents, tasks, conversations):

- `assignee_id` (the owner) — even if v1 has "one person doing it
  all".
- `priority` enum — even if no UI filter exists.
- `category_id` or a fixed enum — even if there's only one category.
- `status` enum with an **extensible** set (minimum 4: created → in
  progress → resolved → closed).
- **`is_internal: bool`** on messages/comments visible to anyone
  besides the author. **Critical:** can't be added retroactively —
  old rows will be public by default and leak.
- An `audit_log` table (`entity_id, actor_user_id, kind, payload
  jsonb, created_at`). Without it you can't reconstruct who changed
  what six months later.
- Human-readable id via a sequence + `server_default`
  (`ORD-2026-0001`).
- `created_at`, `updated_at` always; `closed_at` when applicable.
- For permission tables: `removed_at` (soft-delete) + partial unique
  index on active rows. Removing a role keeps the row, adding it
  back creates a new row, audit-trail preserved.

### 2.2. Don't simplify for speed

Before any decision ask yourself: **"What does this look like with
10× users / 3 operators / two tenants?"** If the answer requires
new fields or tables — add them **now**.

### 2.3. Don't hack

- Background polling, monkey-patching, an ad-hoc global singleton —
  almost always a sign you didn't think it through. Look for the
  clean mechanism first.
- Don't add `try/except` for cases that **cannot** happen (internal
  invariants).
- Don't multiply feature flags and backward-compat shims when you
  can just replace the old behaviour.

### 2.4. What you MAY simplify

These can be added later without debt (migration is cheap, no
risks):

- v1 UI showing only some fields — fine.
- CRUD endpoints for auxiliary models (tags, templates, lookups) —
  ok to ship as a "coming soon" stub.
- Analytics and dashboards — on top of existing events.
- Notifications / digests — wired over existing events.

### 2.5. Default: propose, don't act

**You do not take actions the user did not explicitly request in
this turn.** Even when an action looks reasonable, even when it
looks "obvious next step", even when it looks reversible.

When you see a follow-up that wasn't asked for:

1. **Stop.**
2. Tell the user what you would do (one short paragraph: the action
   + why you think it makes sense + what gets touched).
3. **Wait for explicit "yes, do that".** Silence, prior approvals on
   other topics, or "ok" on an unrelated step do not count.
4. Only then do it.

This applies in particular to:

- **Deletions of any kind** — files, directories, git branches/tags,
  DB rows, containers, working trees. A user instruction to
  "migrate X into Y", "switch to English", "tidy up", "consolidate"
  is **not** an instruction to delete the source. Ask before each
  removal.
- **Restructuring layouts** — moving files between folders, renaming
  conventions, collapsing repos. Even if the new layout is "cleaner",
  it changes the user's mental map and may break their tools — ask.
- **Bulk transformations** — sed/awk/grep replacements across many
  files, schema migrations, refactors. Even if the result is what
  you both seem to want, the diff is large; surface the plan first.
- **Cleanup-on-completion** — at the end of a successful task, do not
  "while we're here, also …". The task is done; the next step is the
  user's.

General approvals from earlier turns ("go ahead", "do it",
"continue") apply to the **specific action that was being discussed
at that moment**, not to subsequent actions you decide to take on
your own. Each new destructive or irreversible step needs its own
explicit go-ahead in the current turn.

When the user asks "did you do X?" or "what did you delete?", be
**precise and proactive**: list everything you touched without
softening or omitting.

This rule overrides any other section in this document that could
be read as licence to act ahead. If in doubt, propose, don't act.

---

## 3. The project-mutation cycle: 6 points

> **Idea → Decision → Card → Testing → Documentation → Push**

This is the **only** allowed model for any non-trivial task. The
project mutates from point to point. Between points it's in a
transient in-flight state; your job each session is to reach the
next point and **commit it to git**.

If you find yourself "skipping" a point or merging several into
one — **stop, you're off-model**. Examples: writing code without a
card, closing a card without documentation, writing a card without
an agreed decision — all violations.

Trivial work (typos, one-liners) is the exception: it goes straight
from Idea to Push without Card or Testing. But anything longer than
~30 minutes goes through all six points.

> **Push throughout §3 is conditional.** Every "commit + push" below
> assumes `project.ini [git] push_enable = true` (§5b.4 / §6.3).
> When `push_enable = false`, only the commit happens; push is
> skipped. When there is no git at all — both steps degrade to
> "save and move on".

### 3.1. Point 1 — Idea

The user formulates the task, usually in one or two phrases; it
won't contain enough detail — that's fine.

**What you do:**
1. Pick the next free idea number `NNN` (scan `ideas/` for the
   highest current `Idea_NNN.md` or `Idea_NNN/` and add 1).
2. Save the idea as `ideas/Idea_NNN.md` in the inbox (flat file,
   not a folder yet). One-paragraph statement: what the user said,
   what they want to achieve.
3. `git commit + push` — the idea exists now as a tracked artefact;
   even if you do nothing else, it's not lost.

**Don't yet:** write code, edit other files, create the Idea folder,
or assume an implementation. Point 1 produces a single file in the
inbox.

**Transition to Point 2:** the user signals they want to act on this
idea now (vs. parking it).

### 3.2. Point 2 — Decision

**Don't write code.** Do this in order:

1. Restate the task in one phrase: "Did I understand right that we
   need X to achieve Y?". Catches 80% of misunderstandings.
2. Inspect the surrounding code — open 2-4 files the task touches.
   Understand which pattern the project already follows.
3. Propose **2-3 architectural options** with short trade-offs
   (simple/complex, fast/flexible, robust/MVP).
4. Give your **recommendation with rationale**.
5. Ask open questions. Don't move forward until they're answered.

When the user agrees on the direction:
6. **Promote the idea to a working folder:**
   ```
   mkdir ideas/Idea_NNN/
   git mv ideas/Idea_NNN.md ideas/Idea_NNN/Idea.md
   ```
7. Create `ideas/Idea_NNN/Decision.md` — capture the agreed direction:
   the chosen option, the rejected ones with one-line reasons, any
   constraints the user mentioned, open questions still hanging.
8. `git commit + push` — the idea is now "started", its folder
   structure tells the next session it's in progress.

**Transition to Point 3:** Idea is in its own folder; Decision.md
exists; user has said "ok".

### 3.3. Point 3 — Card

**Creating the card.**

1. Create `ideas/Idea_NNN/Card.md` next to Idea.md and Decision.md.
2. Fill in the template (section 4): context, agreed decisions
   (cross-reference Decision.md, don't duplicate), stages with
   checkboxes, open questions. Frontmatter `status: queued` —
   the plan exists, execution hasn't begun.
3. `git commit + push` the card.
4. Wait for the user's "ok" on the plan (last chance to amend).

**Executing the card.**

1. Flip the frontmatter to `status: in_progress` the moment you
   start the first stage. `git commit + push` of this single change
   is fine — it tells any other session "this card is being worked
   on right now".
2. Walk the stages top-down, strictly in order.
3. **Tick checkboxes [x] as you go**, not at the end.
3a. **Surface a live progress checklist to the user.** See §11.5 for
   the full rule (trigger, single-`in_progress`, marker glyphs).
   The list mirrors the Card's checkboxes — `Card.md` stays the single
   source of truth.
4. After each stage that represents a complete chunk (models +
   migration; one domain's endpoints; frontend infra) — `git
   commit` to the code repo.
5. After each card update (new [x], revised decision) — `git
   commit + push` of the card.
6. If something unexpected surfaces (a bug in an adjacent system,
   an unaccounted-for fork, a new trade-off) — **stop** and return
   to Point 2. If you change the decision, **update Decision.md
   first**, then continue.

**Transition to Point 4:** every code-side [ ] is now [x], the
build is clean, the card is up to date.

### 3.4. Point 4 — Testing

Split the zones.

**Your zone — static / build-time checks** that don't need a real
user:

- the project builds cleanly (compiler / bundler / image / package
  succeeds);
- linter is clean (or known noise excluded);
- imports resolve / types check;
- a base smoke runs without crash (process starts; binary
  `--version`; container `/health`; app boots on an emulator; CLI
  `--help` doesn't fault).

The exact commands come from `project.ini [stack]` (§5b.3). If
`[stack]` is empty, fall back to the conventional set for the
project type:

| Project type | Build | Lint / types | Base smoke |
|---|---|---|---|
| **web-backend** | `docker compose build` | `ruff` / `mypy` (or stack equivalent) | `/health` answers; closed endpoint returns 401; `alembic upgrade --sql` |
| **web-frontend** | `npm run build` / `vite build` | type-check + ESLint | bundle size sane; dev server starts; no console errors on /index |
| **mobile-android** | `./gradlew assembleDebug` | `./gradlew lintDebug` | APK installs on emulator; main activity launches without crash |
| **mobile-ios** | `xcodebuild clean build` | SwiftLint | app launches in Simulator without crash |
| **desktop-windows** | `msbuild` / `dotnet build` / Electron package | platform linter | binary / installer produced; double-click smoke launches |
| **desktop-cross** | platform-specific build per target | platform linter | at least one target built and launched |
| **cli / library** | binary / wheel / jar builds | linter | `--version` / `--help` answers; basic invocation doesn't crash; unit tests green |

**The user's zone — real-world / end-to-end scenarios** the agent
can't reach:

- the actual feature flow in the UI / device / shell;
- edge cases, mobile layout, locales, accessibility;
- delivery via external channels (TG / push / email / SMS / store
  review);
- behaviour on real hardware (a physical phone, a low-end PC, the
  customer's environment).

**Transition to Point 5:**
- if the user has confirmed smoke (or at least the main scenarios)
  — proceed;
- if the user can't test right now — smoke checkboxes are flagged
  "deferred", and you proceed anyway. Create a separate reminder
  card `bug | feature` titled "smoke <X>" so it isn't forgotten.

### 3.5. Point 5 — Documentation

1. All [x] in `Card.md` except deferred smoke ones.
2. `status: closed` in the frontmatter of `Card.md` (and the same
   in `Idea.md` if it has its own status field).
3. **Update the project's general handbook** (`CLAUDE.md`):
   - if the stack changed — add a paragraph in "Services /
     Architecture";
   - if there is an "Active ideas" / "In progress" index, move
     Idea_NNN out of it (or mark closed) with a one-line summary
     and a link to `ideas/Idea_NNN/`;
   - if a permanent rule emerged during the work — add a memory
     entry (see section 5).
4. The folder `ideas/Idea_NNN/` **stays where it is** — it's the
   permanent record of this mutation. Don't move it to a separate
   "archive" location unless your project explicitly defines one.
   Status is signalled by frontmatter, not by path.

**Transition to Point 6:** Card.md is closed, handbook is amended,
memory is updated.

### 3.6. Point 6 — Push (or "Commit-close" when push_enable = false)

Final commit. Default setup: **one context repo + one (or more)
code repos**.

1. **Context repo** (e.g. `agent_c/`). Commit the closed card, the
   updated `CLAUDE.md`, the new memory files, any new notes. `git
   push` if `push_enable = true` (§5b.4 / §6.3).
2. **Code repo(s).** Commit any remaining staged changes. `git
   push` if `push_enable = true`.

If for a small project everything lives in **one repo** (code +
ideas + memory together), do a single commit (+ push when
`push_enable = true`). The rule is the same — leave nothing
uncommitted at session end.

After this point the project is back at a stable state — a future
session resumes via `git pull` (when push_enable was true) or via
`git log` locally (when push_enable was false; cross-device sync
is the user's manual job).

**Loop back to Point 1:** the project is ready to accept the next
idea.

---

## 4. Cards (and the surrounding `Idea.md` / `Decision.md`)

Every started Idea lives in its own folder `ideas/Idea_NNN/` and
contains three core files plus optional extras:

```
ideas/Idea_NNN/
├── Idea.md            # Point 1 — the original request, untouched after the idea is started
├── Decision.md        # Point 2 — agreed direction, chosen option, rejected alternatives
├── Card.md            # Point 3 — the plan + journal with stages and checkboxes
└── (optional)
    ├── notes.md       # transcript snippets, references, scratch
    └── diagrams/      # PNG/SVG/asciidoc if needed
```

### 4.1. `Idea.md` template

```markdown
---
id: Idea_NNN
date: 2026-01-15
status: started        # inbox | started | closed
title: <one-line idea statement>
---

# Idea

What the user said, as close to the original as possible. One or
two paragraphs.

# Why

The user's stated motivation, if given. Otherwise leave blank.
```

While the idea is in the inbox (no folder yet) `Idea.md` is the
only file. When promoted to a folder, the file moves into the
folder unchanged; status flips to `started`.

### 4.2. `Decision.md` template

```markdown
---
id: Idea_NNN
date: 2026-01-15
status: agreed
---

# Restated task

"Did I understand right that we need X to achieve Y?"

# Options considered

- **A. <name>** — <pros> / <cons>
- **B. <name>** — <pros> / <cons>
- **C. <name>** — <pros> / <cons>

# Chosen direction

<A | B | C> — chosen because <one-line rationale>.

# Constraints from the user

- ...

# Open questions before Card

1. ...
```

### 4.3. `Card.md` template

```markdown
---
id: Idea_NNN
date: 2026-01-15
type: bug | refactor | feature
status: queued        # queued | in_progress | closed
title: <short title>
---

# Context

Why we're doing this. Cross-reference Idea.md and Decision.md;
don't restate them in full.

# Stages

## Stage 1 — <name>

- [ ] 1.1. <concrete step with file path>
- [ ] 1.2. ...

## Stage 2 — <name>

- [ ] 2.1. ...

## Stage N — Commit + push + close

- [ ] N.1. Every [x] above.
- [ ] N.2. `status: closed` in this Card.md frontmatter.
- [ ] N.3. Update the project handbook (CLAUDE.md): stack
  paragraph if changed, move idea out of "in progress" list.
- [ ] N.4. Commit + push to all repos.
- [ ] N.5. "Open questions" is empty: resolved ones moved to "Resolved
  questions", still-open ones promoted to new ideas.

# Open questions

Questions still open. **By card close this section must be empty:** each
item is either resolved (moved to "Resolved questions" below) or promoted
to a new idea (`→ Idea_NNN`). A closed card never leaves a bare open
question here.

# Resolved questions

- <question> → <how it was resolved> (link the stage / commit if useful).
```

### 4.4. When a Card is required

- Task takes >30 minutes.
- There's an architectural fork.
- The task will span 2+ sessions.

If the task is trivial (a typo, a one-liner, a mechanical rename),
**skip the folder entirely** — write `Idea.md` straight into a
"trivial done" log if you want a trace, then make the change and
push. Don't create a folder for work that doesn't need one.

### 4.5. Keeping the Card honest

- Tick boxes **as you go**, not at the end.
- A new substep appeared — add it to the Card.
- A decision changed — update **Decision.md** with a short why
  (don't rewrite history, append a "Revised" section dated). Card
  references the new decision. **Don't edit silently.**
- A question got resolved — **move** it from "Open questions" to
  "Resolved questions" with a one-line "how it was resolved". Don't
  leave it sitting ambiguously under "Open questions". At close, "Open
  questions" must be empty (every item resolved-and-moved, or promoted
  to a new idea).

---

## 5. Memory between sessions

LLM sessions don't remember each other. So there's **external
storage** you read at the start of every session.

### 5.1. Files

One file = one entry. The index is `MEMORY.md`: one line per
entry, title + link + hook.

### 5.2. What to write

- **`feedback`** — a rule about how to work in this project. Write
  it **always** when the user:
  - corrects your approach ("don't do that", "do it this way");
  - confirms a non-obvious choice ("yes, that's right" — that's
    a validated judgment, save it too);
  - explicitly asks you to remember.
- **`project`** — current state of ongoing initiatives: what's in
  flight, deadlines, blockers. Changes fast.
- **`reference`** — pointers to external resources: where CI is,
  where the monitoring lives, where partner docs live, where
  secrets are stored.
- **`user`** — who the user is, what they work on, what they know /
  don't know, communication preferences.

### 5.3. What NOT to write

- Information derivable from current code (folder structure, class
  names, inheritance).
- Information in git history (who changed what when).
- Specific bugs and fixes (the fix is in the code, the context is
  in the commit message).
- Activity summaries that get stale in hours.

### 5.4. Entry template

```markdown
---
name: <Short title (5-7 words)>
description: <One-line description — shown in the index as the hook>
type: feedback | project | reference | user
---

<Body: rule / fact / link>

**Why.** Why this rule exists. Without this, in a month a reader
will treat the rule as dogma and apply it in the wrong place.

**How to apply.** When the rule fires. From what trigger. What to
do in edge cases.
```

### 5.5. Index entry

After creating the file, append one line to `MEMORY.md`:

```markdown
- [<Title>](file.md) — <one-line hook so the reader sees instantly when to apply>
```

---

## 5b. Project config (`project.ini`)

`CLAUDE.md` is **prose** — a narrative description of the project
for the agent to read. `project.ini` is **switches** —
machine-readable, project-specific facts the agent consults at
session start (see the Session start ritual at the top of this
file).

The two complement each other: the handbook describes "what this
project is and how to think about it"; `project.ini` declares
"what the project's operational facts are right now".

### 5b.1. Two-file pattern (mandatory)

Two physical files at the same path:

- **`project.ini.template`** — committed to git. Same structure as
  the real file, but **no secrets** (tokens / passwords replaced by
  `<>` or `<set-me>`). New contributors copy this to `project.ini`
  and fill in.
- **`project.ini`** — gitignored. Holds the real values. Lives
  only on the local machine.

`.gitignore` line:

```
project.ini
!project.ini.template
```

### 5b.2. Format — free-form INI

INI syntax, but **sections and keys are project-specific**. This
file is not a strict schema; it's a project-owner-defined set of
switches and references. Recommended sections are listed below —
pick what fits, invent your own.

Comments: a line starting with `#` or `;`. Inline `//` after a
value is widely seen but is **not standard INI** — most parsers
will treat it as part of the value. Write comments on their own
line.

### 5b.3. Recommended sections

| Section | Purpose | Example value |
|---|---|---|
| `[project]` | name, target / type | `name = booking-backend`, `target = mobile-android` |
| `[git]` | remote + push switch (§5b.4) | `push_enable = true`, `git_repo = git@github.com:org/repo.git` |
| `[Terms]` / `[glossary]` | domain lingo the agent must learn | `WMS = warehouse management system (backend logic)` |
| `[useful_links]` | standards / rules — read before starting work | `design_rules = https://confluence.../x/...` |
| `[examples]` | concrete examples to study (prior specs, similar tickets) | `wmsx_7133 = https://confluence.../pages/...` |
| `[references]` | external systems pointers (CI, monitoring, Jira) | `jira_board = https://...` |
| `[instructions]` | per-project docs / instruction repos to read first; filled by **asking the user** at bootstrap (§12.5 Step 1.5), never hardcoded | `repo = git@.../docs.git`, `use = how_to.md` |
| `[credentials]` | tokens, PATs (gitignored copy only!) | `confluence_pat = <>` |
| `[stack]` | build / smoke commands | `build = ./gradlew assembleDebug` |
| `[target]` | what this project produces / for whom | `target = WMS backend (Russian)` |

None of these are mandatory. The only **enforced** field is
`[git] push_enable` (§5b.4) — without it the agent assumes
`false`.

### 5b.4. Canonical field — `[git] push_enable`

Two keys, with a consistency rule between them:

```ini
[git]
push_enable = true | false
git_repo    = <URL> | null
```

Rule: **`push_enable = false ⇒ git_repo = null`** (no URL listed
when push is off). Inverse: `push_enable = true ⇒ git_repo` must
be a real URL.

The agent reads `push_enable` as the **single source of truth**
for "do I push?". `git_repo` is informational — it's where the
agent points when push is on, and a reference of where the project
would push when push is off.

`push_enable = false` is a valid state — the project lives only on
this machine (or on multiple machines synced manually, not via a
git remote). Commits still happen locally; push is just skipped.
See §6.3.

### 5b.5. What the agent does with `project.ini`

At session start (the 4-step ritual at the top of this file):

1. Reads the file once.
2. Loads the glossary (`[Terms]` / `[glossary]`) into working
   context so domain words in the user's prompts are understood.
3. If the task fits a topic in `[useful_links]` or `[examples]` —
   opens those links **before** writing code.
4. Treats `[git] push_enable` as the gate for every git push
   (§6.3).
5. Uses `[stack]` commands as the default for build / smoke in the
   agent's zone of testing (§3.4).

### 5b.6. Example (`project.ini.template`)

```ini
# project.ini.template — committed to git. Copy to project.ini
# (gitignored) and fill in real values.

[project]
name   = wmsx-8369-bookings
target = WMS backend

[git]
# push_enable = false → project lives locally; commits happen, push is skipped.
push_enable = false
git_repo    = null

[Terms]
# Glossary: domain terms the agent must know before reading prompts.
TSD = handheld scanner — Android app, warehouse-worker frontend.
WMS = Warehouse management system — backend logic.

[useful_links]
# Read before starting work on a spec.
design_rules = https://confluence.example.com/x/PpO1_Q
tz_standards = https://confluence.example.com/x/AQDB5g

[examples]
# Prior specs to mirror style + level of detail.
wmsx_7133 = https://confluence.example.com/pages/viewpage.action?pageId=4189429749
wmsx_7169 = https://confluence.example.com/pages/viewpage.action?pageId=4200959222

[credentials]
# Stay as <> in .template; real PATs live in project.ini only.
confluence_pat = <>

[stack]
# Defaults for the agent's zone of testing (§3.4).
build = (this project is a spec — no build step)
smoke = (none)
```

---

## 6. Git

In this workflow git is more than VCS. It's the **main channel for
context transfer** between sessions (and between the user's
devices).

### 6.1. Two repo categories (default)

| Category | What it contains | When you push |
|---|---|---|
| **Context repo** (e.g. `agent_c/`) | `CLAUDE.md`, `MEMORY.md`, `memory/`, `ideas/` (every card, all statuses), `notes/`, `templates/` | After every meaningful change — new memory rule, new idea, card status flip, card stage [x], closed card |
| **Code repo(s)** | Sources, migrations, tests | After every card stage that produces a working chunk |

Earlier versions of this workflow split active vs. closed cards into
two repos. That's no longer recommended — the lifecycle is signalled
by `Card.md` frontmatter (`status: queued | in_progress | closed`),
not by repo path. One context repo holds them all.

If the project doesn't have this layout — propose it in the first
session (see section 12).

### 6.2. Commits

- Not "one big commit at the end". After **every stage** of the
  card that represents a complete chunk.
- Message:
  ```
  type(scope): what was done

  Card: <path>

  <body: why, not what — `what` is visible from the diff>
  ```
- No author tails ("Co-Authored-By: …") unless the user explicitly
  asks for it.

### 6.3. Push (conditional on `project.ini`)

**Three project states regarding git:**

1. **No git.** No `.git` directory. There's nothing to commit or
   push; the cycle's commit + push steps degrade to "save the file
   and move on". If the project will outlive the session, propose
   `git init` to the user at the next quiet moment (§12.5 step 0).
2. **Local git, no remote.** `.git` exists; `project.ini [git]
   push_enable = false`, `git_repo = null` (§5b.4). Commit per
   §6.2; **skip push.** Cross-device propagation is the user's
   manual job (rsync / scp / shared FS).
3. **Git with remote.** `.git` + a remote configured.
   `push_enable = true`, `git_repo = <URL>`. Commit + push per the
   rules below.

For state (3):

- After every commit to the **context repo** — push immediately.
  Other sessions read from origin; if you didn't push, your peer
  (or future-you) won't see the card status flip.
- To the **code repo** — after every stage if the build is clean
  (open `[ ]` on tests or docs is fine).
- The final push at card-close — **mandatory** (both repos).
- Force-pushes, pushes to shared `main`, and pushes that affect
  others' working state still need a current-turn OK regardless of
  `push_enable` (§7.2).

Switching from state (2) to (3) is a project-level decision —
flip `push_enable`, add `git_repo`, **ask the user before
flipping.**

### 6.4. Never without an explicit ask

- `--no-verify` (skipping hooks) — if pre-commit fails, fix the
  root cause, don't bypass it.
- `--force` / `push -f`, especially against `main`.
- `reset --hard`, `clean -f`, `branch -D`.
- Deleting files / folders you don't know — investigate first
  (could be work-in-progress by the user or another agent).

---

## 7. Change safety

> Main principle: **measure twice, cut once**. The cost of an
> uncontrolled action is lost work for the user, an aborted live
> session, broken data.

### 7.1. Before any action — assess

- **Reversibility:** can you roll it back?
  - commit / new branch: yes.
  - push to a public repo: mostly.
  - `rm`, `DROP TABLE`, a sent message: no.
- **Blast radius:** how many processes / users / sessions depend on
  this?
- **Visibility:** is the action seen by others? (push, PR, email,
  deploy — yes; a local edit — no.)

### 7.2. Stop-list (ALWAYS ask explicitly)

These actions require **explicit OK from the user in the current
session**, even if they previously gave general "go ahead":

- `rm -rf`, deleting branches / tags, `DROP` tables, `reset --hard`.
- `push --force`, especially against `main`.
- Restarting shared infrastructure (shared gateway, shared docker
  daemon, shared k8s namespace, load balancer).
- **Restarting a service the user is currently working through**
  (web console / PTY broker / tunnel — if the user is connected
  via it, you abort their session).
- Applying a migration to a prod DB.
- Acting on behalf of the user in public channels: creating a PR,
  commenting on an issue, sending email, posting to Slack/TG.
- Uploading content to public services (pastebin, gist, diagram
  renderers — they cache and index).

### 7.3. No confirmation needed

- Local file edits (git rolls back).
- Local build, lint, tests.
- `reload` of a config that **doesn't drop connections**
  (`<service> reload`, not `restart`).
- Read-only requests anywhere.
- Creating new files / folders in the project.
- `git commit` — always safe, entirely local; never needs
  confirmation.
- `git push` is **not** in this category — see §6.3. Routine push
  of work within the current task scope is fine when
  `push_enable = true`. Force pushes and pushes to shared `main`
  always need a current-turn OK regardless (§7.2).

### 7.4. Order for rebuild + restart

When you need to rebuild a service:

1. **Build without restart.** Image / artefact builds, old container
   keeps serving.
2. **Smoke the artefact.** Does the container start in isolation?
   Do all modules import without error? Does `/health` answer?
3. **Restart** — only if steps 1-2 are clean.
4. **Right after the restart** — verify the prior functionality
   still works (`/info`, key endpoints).

If the container won't come up at step 3 — **immediately** roll
back (previous image tag / restore).

### 7.5. When things go wrong

- Diagnose **the current situation**. Don't "let's try a workaround
  and see what happens".
- Logs: process, application, database.
- If you lost a connection / the user's session — **don't** panic
  and **don't** delete files "to fix it".

---

## 8. Code structure

### 8.1. File size

- **≤300 lines** — default / priority for new files.
- **≤500 lines** — acceptable if splitting would create false
  boundaries.
- **>500 lines** — open a refactor card if the feature already
  ships.

### 8.2. One file = one domain

- Don't stuff independent entities into one file just because
  they're in one feature.
- Converters / formatters / helpers go in their own file,
  especially if used from 2+ places.
- API routes per domain — one file per domain.

### 8.3. In-code documentation

- **Top-of-file docstring**: what the file is for, which card
  introduced it.
- **Inline comments** only when the "why" isn't obvious from the
  code. The "what" is the function name and signature.
- **Don't write** "added by X for issue #N" — that belongs in the
  commit message.

### 8.4. Imports

- Groups: stdlib / third-party / project / local.
- Circular imports signal a bad boundary; fix by re-splitting, not
  by "import inside the function".

---

## 9. Architectural must-haves (server-side projects)

A few universal rules that save months of pain on long-lived
projects with a database + API.

**Scope.** §9.1-§9.7 below assume the project has stateful data
behind a server (web-backend, mobile/desktop client with a synced
server, WMS, etc.). Several rules are universal and apply to any
project with stateful data — including offline mobile/desktop apps:
permissions without `User` booleans (§9.1), audit log (§9.3),
localization from day one (§9.5), human-readable ids (§9.6). For
shipping rules specific to mobile / desktop (signing, release
channels, OS permissions, offline-first, store constraints) see
§9b.

### 9.1. Permissions

- **Don't grow booleans on `User`** (`is_admin`, `is_moderator`,
  `is_support`, …). Every new flag rewires permissions on the fly.
- One global `is_superadmin` is fine. Past that — **narrow
  permission tables** per domain:
  - `<domain>_member(domain_id, user_id, role, removed_at)`
  - `<domain>_staff(owner_user_id, staff_user_id, perm_<feature>:
    bool, ...)`
- Soft-delete: `removed_at TIMESTAMP NULL` + partial unique index
  `WHERE removed_at IS NULL` — gives you "at most one active row"
  while preserving audit.

### 9.2. User-side vs admin-side endpoints

- **Different paths:** `/api/v1/<domain>/*` for the end user,
  `/api/v1/admin/<domain>/*` for the operator.
- **Different Pydantic / schemas.** `MessageOutUser` physically
  does not have `is_internal` — you can't accidentally leak it to
  the client even with a bug. Defence **at the type level**, not
  "I'll remember, I won't leak".
- **404 instead of 403** when the resource exists but isn't owned
  by the requester. Otherwise you reveal the existence of foreign
  IDs.

### 9.3. Audit log

Any mutation in a long-lived entity (status, assignee, tags,
priority) writes one row:

```
audit_event(id, entity_id, actor_user_id, kind, payload jsonb, created_at)
```

`actor_user_id NULL` = system (cron, migration, automatic
transition).

Without an audit log, six months in you won't be able to tell
**what** happened to **this specific** object.

### 9.4. Realtime / pubsub

- In-memory pub-sub is enough for single-worker dev.
- For scale-out (multiple processes) — Postgres `LISTEN/NOTIFY` or
  Redis. Don't change the publish/subscribe contract.
- **Publish after `commit`**, never before. Otherwise a
  rolled-back transaction will leak ghost events.

### 9.5. Localization

- Lay down at least **2 languages from day one**, even if only one
  ships.
- User-facing strings live in a localization dictionary, not in
  code.
- Lookups (categories, statuses) have `name_<lang>` columns or a
  dedicated locale table.
- Entities like ticket/message carry a `language` field (the user's
  language at creation time) so notifications arrive in the right
  language even after the user changes their profile.

### 9.6. Human-readable id

For anything that surfaces in conversation (tickets, invoices,
orders), allocate a **separate sequence** + the format
`<PREFIX>-<YEAR>-<NUMBER>`. DB generation via `server_default`:

```sql
'INV-' || extract(year from now()) || '-' || lpad(nextval('inv_seq')::text, 4, '0')
```

No app load, monotonic numbering, race-free.

### 9.7. SLA deadlines in the schema

If you have an SLA — store `due_at TIMESTAMP NULL` on the entity
computed at create time. Don't compute on the fly from "priority +
created_at" — the "overdue" filter with a partial index on `due_at
< now()` runs in milliseconds on a million rows.

---

## 9b. Architectural must-haves (mobile / desktop projects)

Apps that ship as installable artefacts have their own pain points
that don't surface in web-backend land. §9.1, §9.3, §9.5, §9.6 still
apply where there's stateful data.

### 9b.1. Versioning — semver + build number

- `version_name` (semver — `1.4.2`) shown to humans.
- `version_code` / `build_number` (monotonic integer) used by the
  store / installer to compare builds; **never reused, never
  decreased**.
- Wire both into the build pipeline so a release branch increment
  cannot be forgotten.

### 9b.2. Signing — set up before the first store upload

- **Android:** an upload keystore generated once, stored
  off-machine (encrypted backup), referenced from the build via
  env vars. Lose it → can never update the app in the store; have
  to republish under a new package name.
- **iOS:** Apple Developer account + provisioning profile +
  distribution certificate. Renewal is annual; calendar reminders.
- **Windows:** Authenticode certificate (EV preferred for
  SmartScreen reputation). Cheaper alternative: ship unsigned but
  accept SmartScreen warnings on first launch.
- **macOS:** Developer ID + notarization. Without notarization the
  binary won't run on default Gatekeeper.

### 9b.3. Release channels

- **Android:** Play Internal → Closed → Open Testing → Production.
  Use Internal for daily builds — instant, no review.
- **iOS:** TestFlight (internal up to 100, external up to 10k) →
  App Store review.
- **Windows:** stage your own update server (Squirrel / Velopack)
  or use Microsoft Store; ship MSI / MSIX for enterprise.
- **macOS:** TestFlight (if App Store) or Sparkle / your own
  update feed (if direct-distributed).
- Every channel has a different review / sign-off SLA — bake it
  into the release card stages.

### 9b.4. OS permissions

- Declare the **minimum** required (camera / location / contacts /
  notifications). Each permission asked is a drop in install rate.
- Store rejection often = "you asked for a permission you don't
  visibly use". Tie each declared permission to a specific code
  path; remove unused ones before submission.
- Permissions have a **runtime UX flow** that's not optional:
  prompt at the right moment, handle denial gracefully, provide a
  path to re-grant via system settings.

### 9b.5. Offline-first / sync

- Mobile and desktop apps live partly offline. Local state is the
  source of truth between syncs.
- Plan the **conflict-resolution policy** at schema time
  (last-write-wins / per-field merge / CRDT / manual conflict UI).
  Retrofitting is painful.
- Sync queue: outgoing mutations persist locally until acked by
  the server. Idempotent server endpoints (mutation_id deduped) so
  retries don't double-apply.

### 9b.6. Store constraints

- **Android Play:** target API level keeps rising (every August /
  November cycle); old apps get delisted. Calendar this.
- **iOS:** Xcode / SDK requirement bumps annually. Building with
  an old SDK starts failing review.
- **Microsoft Store:** packaging format (MSIX); fewer constraints
  than mobile but identity rules are strict.
- Build artefact size and startup time are reviewed — keep tabs;
  surprises here can block a release.

### 9b.7. Crash & telemetry

- A mobile / desktop app crashes far from the developer's logs.
  Ship a crash reporter (Sentry / Crashlytics / Bugsnag) from
  release v1.
- Telemetry is separate from crash: structured events for funnel
  analysis. Both gated by user consent per the relevant
  jurisdiction.

---

## 10. Anti-patterns

Don't do these, ranked by how often they show up:

1. **"We don't need it yet — we'll add it later"** about schema or
   API contract. Almost always a lie: "later" = "with a migration
   and a leak risk".
2. **"Quick fix".** A quick fix without understanding the root cause
   sets the timer on a louder bug.
3. **One big commit at the end of the task.** Loses rollback, loses
   review.
4. **Silent decision changes.** Decided differently — update the
   "Decisions" section of the card with a short why.
5. **Background polling instead of events** where events are
   possible.
6. **`try/except` for invariants** that **cannot** fail to hold.
7. **Closing a card without updating the general handbook** if the
   task touched the shared stack.
8. **Applying a migration to prod without confirmation** in the
   current session.
9. **Acting on behalf of the user in public channels** (PR, issue,
   email) — never without an explicit ask.
10. **Deleting unfamiliar files / branches / lock files** "to fix
    things". Investigate first — it might be the user's or another
    agent's work-in-progress.

---

## 11. Talking to the user

### 11.1. Tone

- Short and to the point. A long answer only when the task is
  exploratory.
- No filler ("great question", "sure, I can help", etc.).
- In the language the user writes in.

### 11.2. When to stop and ask

- At an architectural fork.
- On discovering unexpected state (unknown files, an active
  session, work-in-progress).
- Before any stop-list action (section 7.2).
- When your decision is being revised mid-flight — say so first,
  change after.

### 11.3. When to continue without asking

- Trivial continuation: the user said "ok" — you do the next
  planned step.
- Reversible local actions.
- When the task has been decomposed down to mechanics.

### 11.4. When to say "I didn't do it"

- If smoke failed and you don't understand why — don't mask it.
  Say "here's what failed, here's what I tried, here's what I'm
  unsure about".
- If the task turned out wider than it looked — say so, don't shift
  the scope silently.

### 11.5. Live progress visibility (required for multi-step work)

**Decompose every non-trivial task into subtasks and show the user a
live progress checklist — then update it as work proceeds.** This is a
hard requirement, not a nicety.

**Trigger.** Any task that is ≥3 distinct actions or ≥2 conversation
turns of execution. Trivial one-shots (typo, single edit, one shell
command) — no list. When in doubt, list it.

**Discipline.**

- Decompose **first, before execution starts** — not after the first
  stage is already underway. The user sees the whole plan up front and
  watches it burn down, without having to ask "where are we?".
- **Exactly one task in `in_progress` at a time.** Sequential progress,
  not "everything in flight". Flip the previous one to `done` before
  starting the next.
- Flip a marker the moment that stage changes state, not at the end.
- Use the harness task/todo tool when available; **otherwise render the
  list inline using these markers:**
  - `~~✔ Stage N — name~~` (done — strike-through visually closes it)
  - `▶ Stage N — name` (in progress)
  - `◻ Stage N — name` (pending)
- This mirrors the Card's stage checkboxes (`Card.md` is the source of
  truth); the live checklist is its in-conversation reflection.

---

## 12. Project context repo and session-start protocol

### 12.1. Project root — docs / code / build

A project occupies a **project root** — one folder on disk.
Inside it, three subfolders:

- **`docs/`** — versioned in a docs git repo. Holds the entry
  handbook (`CLAUDE.md`), `project.ini.template`, memory
  (`MEMORY.md` + `memory/`), cards (`ideas/`), long-lived notes,
  templates. **Canonical place for everything about how the
  project is built and what is being done in it.** When in doubt
  where to put a document — put it here.
- **`code/`** — versioned in a separate code git repo. Holds
  source, tests, migrations. Does **not** hold cards, memory, or
  handbooks. (For tiny projects with no separate codebase,
  `code/` can be omitted.)
- **`build/`** — gitignored. Build artefacts (binaries, packaged
  installers, image tarballs).

`docs/` and `code/` are independent git repos, pulled and pushed
independently. The docs repo may be **shared across many
projects** (one subfolder per project) — that's the common interim
arrangement until divergence justifies splitting off a per-project
docs repo.

`project.ini` (real values, gitignored) and `project.ini.template`
(in git) live inside `docs/` — see §5b. The `[git]` section
declares whether each repo has a remote (`push_enable` / `git_repo`,
§5b.4 / §6.3).

**Localized folder names** (e.g. `документы` / `код` / `билд` in
Russian projects) are valid. The playbook refers to them as
`docs/`, `code/`, `build/` throughout; map to your team's names in
`CLAUDE.md`.

**Every agent session begins by syncing `docs/` (and `code/` if
present) and reading from `docs/`; every session ends by
committing changes back.**

### 12.2. Layout in detail

```
<project-root>/                     # project folder on disk
├── CLAUDE.md → docs/CLAUDE.md      # symlink for tool auto-discovery
├── docs/                           # git repo: canonical docs space
│   ├── CLAUDE.md                   # thin handbook; links to playbook
│   ├── project.ini                 # gitignored; real values
│   ├── project.ini.template        # in git; structure + comments
│   ├── MEMORY.md                   # one-line index into memory/
│   ├── memory/                     # individual memory entries
│   │   ├── feedback_<name>.md
│   │   ├── project_<name>.md
│   │   ├── reference_<name>.md
│   │   └── user_<name>.md
│   ├── ideas/                      # cards: inbox at root, started in folders
│   │   ├── Idea_001.md             # inbox: not yet started
│   │   ├── Idea_002.md
│   │   └── Idea_003/               # started: promoted to a folder
│   │       ├── Idea.md
│   │       ├── Decision.md
│   │       └── Card.md
│   ├── notes/
│   │   └── ai_agent_playbook.md          # this file — vendored copy or symlink
│   └── templates/
│       ├── Idea.md
│       ├── Decision.md
│       └── Card.md
├── code/                           # git repo: source / tests / migrations
└── build/                          # gitignored: artefacts
```

**Auto-discovery.** Sessions typically start at the project root.
The symlink `<project-root>/CLAUDE.md → docs/CLAUDE.md` lets
Claude Code / Cursor / Aider find the handbook from the root while
keeping the file versioned in `docs/`. For tools that look for
other entry names, add symlinks inside `docs/`:

```
docs/AGENTS.md       -> CLAUDE.md
docs/.cursorrules    -> CLAUDE.md
```

**Playbook placement.** This file
(`ai_agent_playbook.md`) lives in `docs/notes/`
either as a vendored copy or as a symlink into a shared playbook
repo (see §1 — "where this file lives"). `CLAUDE.md` links to it
near the top so the agent finds it at session start.

**One-repo layout (small / one-shot projects).** Everything can
collapse into a single repo at the project root — `CLAUDE.md`,
`project.ini.template`, `MEMORY.md`, `memory/`, `ideas/` directly;
no `docs/` subfolder, no separate `code/`. The 6-point cycle (§3)
and `project.ini` (§5b) still apply.

### 12.3. Session-start protocol (every session, not just the first)

When you start any session, **before responding to the user's first
request**, do this in order:

1. **`git pull --ff-only`** the context repo. If there are remote
   commits you don't have, they may carry a new memory rule, a new
   decision on an idea you'll touch, or a status change on an
   in-progress card. Don't work on stale context.
2. **Read the entry handbook** (`CLAUDE.md`). Skim sections that
   describe the stack and active work; the conventions sections you
   already know.
3. **Scan `MEMORY.md`** — it's an index with one-line hooks. Load
   the bodies of entries that match the topic at hand (feedback for
   the area you're touching, project entries for the area in
   progress).
4. **Look for active cards** — folders inside `ideas/` whose
   `Card.md` has `status: queued` or `status: in_progress`. The
   most recently modified one is usually what to continue, but check
   with the user if more than one is in flight.
5. If the user asks "where did we leave off?" / "continue from last
   time", also pull the **2-3 most recently modified** folders in
   `ideas/` and the corresponding cards.

That's it. Once you have the context loaded, respond to the user.

If any of the above fails (no `CLAUDE.md`, no `ideas/`, no
`MEMORY.md`) — you are in a **first-ever session** in a fresh
project. See 12.5 below.

### 12.4. Where an agent looks for each kind of information

- **Entry point:** `CLAUDE.md` at the context-repo root. Claude
  Code reads it automatically. For other tools, the same file is
  also reachable as `AGENTS.md` and `.cursorrules` via symlinks.
- **Rules of the road:** `MEMORY.md` index → `memory/<entry>.md`.
- **Active work:** folders inside `ideas/`. `Card.md` frontmatter
  tells you the state (see 4.3 for the status enum).
- **Inbox of ideas:** loose `.md` files at `ideas/` root (no folder
  yet). Discuss with the user before promoting any to a folder.
- **Closed ideas:** folders with `Card.md` having `status: closed`.
  Stay in `ideas/` as historical record — search them when looking
  for "how did we solve this before".
- **Project-wide architecture / decisions:** `notes/` (long-lived,
  not tied to a single idea).

### 12.5. First-ever session in a fresh project (bootstrap)

If the project root or `docs/` doesn't exist yet — in the first
session **propose** to set it up as a preliminary step. **Don't
set it up silently.** Once the user agrees:

#### Step 0 — Detect git state, decide on remotes

Before creating any files:

1. Check whether `docs/` (or the target docs path) is already a
   git repo (`.git` present). Same for `code/`.
2. For each repo that doesn't exist yet — ask: should this be a
   git repo? Should it have a remote? Record the URL if yes.
3. Write the answers into `project.ini [git]` (§5b.4) before
   `git init`:
   - both repos local-only → `push_enable = false`, `git_repo =
     null`.
   - docs has a remote → `push_enable = true`, `git_repo =
     <URL>`. Note the code repo's remote separately in
     `CLAUDE.md` if it differs.
   - neither repo yet and no plans → `push_enable = false`;
     propose `git init` later when the project stabilises.
4. `git init` each repo the user agreed to create. `git remote
   add origin <URL>` only where `push_enable = true`.
5. **The remote may already exist with content.** A platform-created
   repo (GitLab/GitHub "create with a README") already has a `main`
   with an initial commit. Don't push a fresh local history onto it —
   you'll hit unrelated-histories or be tempted to force. Instead:
   `git init` → `git remote add origin <URL>` → `git fetch origin` →
   `git checkout main` (DWIM-tracks `origin/main`, brings its README
   into the working tree) → stage the bootstrap files and commit **on
   top** of the initial commit → push. Remote history and README kept.

**The agent cannot create the remote.** Creating the GitLab/GitHub
project is the user's action; the agent only does `git remote add` and
pushes. So Step 0 must establish, by **asking the user**: do the
remotes already exist on the platform, or must the user create them
first? And if `project.ini` lists a `git_repo` but omits
`push_enable`, that's an inconsistency (§5b.4) — ask; default to
`false` until told.

#### Step 1 — Create the layout (per §12.2)

1. Create `docs/`:
   - `CLAUDE.md` — thin handbook (10-50 lines): 1-2 paragraph
     project description + link to the playbook near the top.
   - `project.ini.template` (committed) + `project.ini`
     (gitignored). `.gitignore` per §5b.1.
   - empty `MEMORY.md`, empty `memory/`, empty `ideas/`,
     `notes/` (with the playbook copy or symlink),
     `templates/` with the three templates from §4.
2. Symlink `<project-root>/CLAUDE.md → docs/CLAUDE.md` for
   auto-discovery.
3. Add `docs/AGENTS.md` and `docs/.cursorrules` symlinks →
   `docs/CLAUDE.md` for tools that expect those names.
4. Create `code/` (per the user's stack) and `build/` (listed in
   `docs/.gitignore` if `build/` could land inside it
   accidentally).

#### Step 1.5 — Fill `project.ini` *with* the user (guided)

`project.ini` is **not** filled silently. Given only the playbook repo
URL and an idea file, the agent:

1. **Fetches the template.** Pull `project.ini.template` from the
   playbook repo (it ships there as the reference), copy it to
   `project.ini`. Propose this to the user.
2. **Walks the user through it, field by field.** Top-down by section;
   for each field state what it's for + a sensible default, capture the
   user's answer. Don't assume — `target`, `[git] push_enable` + repo
   URLs, glossary, stack commands are the user's calls. Secrets (PATs)
   stay `<>` in the template; the real value goes into `project.ini`
   locally.
3. **Asks for additional project documents.** Explicitly ask: *"Are
   there extra documents or instruction repos I should read — Confluence
   how-tos, domain guides, prior specs?"* Users usually remember them
   only when prompted. Record what they give under `[instructions]`
   (repo URL/path + which docs). **Never hardcode a specific docs source
   in the template or this playbook** — it is per-project (work vs
   personal projects keep different docs in different places).
4. **Pulls and reads them.** If `[instructions]` is set, pull that
   source (read-only) and read the listed docs *before* starting work
   (same timing as `[useful_links]` / `[examples]`, §5b.5). On later
   sessions the field is already filled — read without re-asking.

#### Step 2 — First commit

**Before committing — two checks (`git add -A` sweeps in everything
not ignored):**

- **Secret audit.** The gitignored real config (`project.ini` with
  tokens/PAT) must **not** be staged: `git check-ignore project.ini`
  must echo it, and the staged list must contain no secrets. A PAT
  leaked into a shared repo cannot be un-leaked. (Reminder: `git
  check-ignore` reports a path as *not* ignored while it is still
  tracked/staged — remove it from the index first, then it matches.)
- **Review the sweep.** Scan the staged list for (a) machine-local
  tooling files (e.g. `.claude/settings.local.json`) → gitignore
  `.claude/`; (b) stray files dropped in the root that belong in the
  context repo (reference docs, notes) → move into `docs/` and decide
  placement with the user, don't silently commit them to the code repo.

1. `git add` + `git commit` in `docs/` (and in `code/` if it
   exists yet).
2. `git push` per `push_enable` (§6.3).
3. Move to Point 1 (Idea) with the user's first task.

#### If structure is partially in place

**Don't rebuild it.** Adapt to what's there. If the project
already uses different folder names (`tasks/`, `cards/`,
`tickets/`) — follow the existing convention, just call out in
`CLAUDE.md` what maps to what. The 6-point cycle works regardless
of folder names.

**Code already at the project root (no `code/` subfolder).** Common
with IDE/tool-generated projects (Android Studio, Xcode, Cargo,
npm) whose build tooling expects its config at the repo root.
**Don't move the code into a `code/` subfolder to match §12.2's
diagram** — it breaks the IDE's assumptions and the build. Instead,
create `docs/` as a **sibling** of the existing code at the root and
treat the root itself as `code/`. Record the mapping in `CLAUDE.md`
("`code/` = repository root"). `build/` stays wherever the toolchain
emits it (e.g. Gradle's `build/`), gitignored.

If git is present but `project.ini` isn't — fill in `[git]` from
observed state (`git remote -v`) and create `project.ini.template`
with at least `[project]` and `[git]` sections.

### 12.6. Numbering ideas

`Idea_NNN.md` with zero-padded sequence numbers (`001`, `002`,
`042`). To pick the next number:

```sh
ls ideas/ | grep -oE '^Idea_[0-9]+' | sort | tail -1
```

Add 1 to the result. If `ideas/` is empty, start at `001`. Numbering
is monotonic across the lifetime of the project — never reused, even
after closure.

### 12.7. Bootstrap pointers in frequently-used cwds

The context repo holds everything, but Claude Code (and most other
code-assist agents) auto-pick a `CLAUDE.md` from the current working
directory, not from a sibling repo. If the user routinely starts
sessions from a code directory that is not the context repo (e.g.
`/root/web/shared/term/` or `/root/web/dev/<service>/`), drop a
**thin bootstrap pointer** there: a short `CLAUDE.md` (~20-30
lines) that says "you are in project X, the handbook is at
`/root/<context>/CLAUDE.md`, the playbook is at `notes/…`, the
active cards are under `cards/<project>/`". The agent reads this,
follows the pointers, and is in business.

A bootstrap pointer is not a duplicate of the handbook — it's a
tiny redirect file. It only needs:

- which project this directory belongs to;
- the path to the main `CLAUDE.md` and what to read first;
- a couple of project-specific pointers (handbook section name,
  the `cards/` subfolder, recent closed cards worth knowing about);
- the `git pull` command for the context repo.

When the context repo's content changes (handbook, playbook,
memory), the bootstrap pointer typically does **not** need updating
— it points at paths, not at content. Only if the layout shifts
(e.g. `cards/term/` is renamed) does the pointer need a touch.

This pattern is useful but not mandatory. Skip it for cwds the user
visits rarely; add it for every cwd the user sees in `cd` history.

---

## 13. Appendix: typical commit message

```
fix(orders): drop /api/v1 from user router prefix (aggregator adds it)

EventSource cannot set custom Authorization headers, frontend passes
the token via ?token= query param; backend now resolves it the same
way as the Bearer header. Header wins if both are present.

Card: cards/orders/bug/2026-01-15-orders-router-prefix-bug.md
```

Structure:
- Header (≤72 chars): `type(scope): what was done`. Type:
  `feat | fix | refactor | docs | test | chore | style`.
- Body — what you need to know to understand the change (**why**,
  not **what**).
- Card link — mandatory if the work was tracked as a card.

---

## 14. Final thought

This instruction is not gospel. It's the **minimum viable set of
practices** that pays for itself from day one. If something here
doesn't fit your project — **ask the user first**, then adapt.

**Remember the central model:** the project mutates from point to
point along

> Idea → Decision → Card → Testing → Documentation → Push

Every session should bring the project **to the next point**, not
leave it in flight. If at the end of a session you find the project
in flight — that's a signal you missed something: either the
scenario isn't done, or the card isn't updated, or the push wasn't
made. Finish it.

**Single source of truth:** the **context repo** (e.g. `agent_c/`)
is canonical for everything about how the project is built and what
is being done in it — handbook, memory, every card past and
present, long-lived notes. Every session starts with a pull of it
and ends with a push to it. Don't keep "private" planning
documents elsewhere; if it's worth writing down, it goes in the
context repo.

Working precedence: the project's general handbook (`CLAUDE.md`)
**refines** this instruction for the current project. If they
conflict — go with `CLAUDE.md`, because it's project-specific.
