# GOVERNANCE.md — Operating Policy & Repo Map for Helix-Matrix

> Companion to `CONSTITUTION.md` (the *why* — philosophy and clean-code policy, which
> this file enforces operationally) and `AGENTS.md` (the agent charter + ledger).
> Read all three before acting. This file may be updated by any agent **as a logged
> governance change** to keep the map and policy truthful; the CONSTITUTION itself is
> owner-only.

## 1. Repository map

Authoritative directory map for **Helix-Matrix**. Any file you add, move, rename, or
delete gets reflected here in the same landing.

| Path | What lives there |
|---|---|
| `app/index.html` | the dashboard: problem→tool matrix (20 systems), floor-symptom diagnostic, topology schematic, day OS control room, glossary, Sami panel |
| `assets/css/` | base.css, day-os.css, shell.css, sami.css |
| `assets/js/` | day-os.js, shell.js, sami.js |
| `lessons/` | 24 interactive lessons + INDEX.md |
| `reference/` | glossary.html + one local source note per lesson |
| `data/metacognition.json` | Sami's metacognitive memory (what it knows, what it recommends) |
| `learning-records/` | runtime personal data: answers, quiz attempts, day state, weekly reviews — **git-ignored, never published** |
| `server/` | `os_engine.py` (day logic) + `os_server.py` (the loopback-only server) |
| `tests/` | engine tests (28) |
| `scripts/` | `serve.sh`, `launch.sh`, `package.sh`, `verify.sh` |
| `deploy/` | systemd unit + desktop entry |
| `docs/` | quickstart, architecture, deployment, release |
| `.github/` | CI workflows |
| `README.md` | the single source of truth |
| `CHANGELOG.md` | dated user-visible changes |
| `LICENSE` | MIT |
| `VERSION` | the app's version string (checked by CI + verify.sh) |

## 2. Documentation policy (what belongs where)

**Root holds only the requested set** — nothing else:

| File | State | Purpose |
|---|---|---|
| `README.md` | required | The single source of truth: what this is, why it's here, how to use it — in simple English for a professional reader. Carries the Helix Solutions logo. |
| `AGENTS.md` | required | Agent charter + sign-in/out ledger. |
| `CONSTITUTION.md` | required | The owner's engineering philosophy and clean-code policy (unified across every repo). |
| `GOVERNANCE.md` | required | This file: repo map, documentation policy, sync policy, archiving rules. |
| `CHANGELOG.md` | standard | Dated user-visible changes. |
| `LICENSE` / `LICENSE.md` | standard | MIT, unless the repo states otherwise. |
| `SECURITY.md` | standard | Threat model, vulnerability reporting, secret handling. |
| `VERSION` | standard | The app's version string, kept in lockstep with CHANGELOG and CI. |

**Everything else lives in `docs/`** — reports, audit logs, execution plans, research
notes, ADRs, runbooks, anything dated or one-off. No stray `.md`/`.txt` at the root.
If a document at the root is not in the table above, move it to `docs/` (or
`docs/archive/` if it is historical) and record the move in the `AGENTS.md` ledger.

**Note on personal data:** the files under `learning-records/` (answers, quiz
attempts, term grades, day state, weekly reviews, decisions) are intentionally
git-ignored — they are the owner's personal learning history and are never
published. The one committed sample record
(`learning-records/0001-prior-knowledge-fail-closed-instinct.md`, shipped with v1.0.0
as a fixture showing the record format) is the only exception, and it is treated as
documentation, not personal data.

## 3. Synchronization & harmony policy

The owner's rule: **the repository's actual status must match its README at all times,
locally and remotely.**

1. `README.md` is the canonical account. Landing pages (`index.html`) and dashboards
   mirror it; they never fork it.
2. When reality changes, update `README.md` **first**, then mirror it to the pages.
3. Every sanctioned change is committed **and pushed** to the default branch, so the
   GitHub copy, the local working copy, and any local platform that reads the repo
   all show the same truth.
4. A number published anywhere (README, page, badge) must be reproducible from this
   repository. A stale figure is removed, not left to rot.
5. The workspace tool `readme-sync/` (in `Repos_Readmes`) verifies that every public
   repo's README matches its local clone. Keep this repo's README in a state it reports
   as matching.

## 4. Archiving rule

- Archive (move to `docs/archive/`), never delete: historical reports, superseded plans,
  dated audits, and one-off execution logs.
- Delete outright only regenerable artifacts: caches, build output, coverage files.
- Record every move in the `AGENTS.md` ledger with date and time.

## 5. Engineering philosophy & clean-code policy (operational summary)

The full text is `CONSTITUTION.md`. The operational reminders, enforced here:

- **Fail closed.** Missing input or missing authority is a refusal, never a default.
- **Evidence before claims.** Published numbers carry a command, a date, and an artifact.
- **No duplicates, no temp files, one file one job, every file explains itself.**
- **Secrets never enter the tree.**
- **Simple English** in code, docs, and UI, so a non-technical professional reader
  (recruiter, partner) can follow.
- **One brand mark:** the Helix Solutions logo, everywhere.

## 6. Definition of done

It works; it has a test or a documented manual check; the `AGENTS.md` ledger has an
entry; the docs reflect the new reality; no temporary file was left behind; and every
published number can be re-run to reproduce itself.
