<div align="center">
<img src="https://raw.githubusercontent.com/Hatemshalaby15071979/Helix-Solutions/main/assets/helix-solutions-logo.png"
     alt="Helix Solutions" width="72" height="72" style="margin-bottom:0.5rem">

# Helix-Matrix

**Operations & AI Portfolio Reference Matrix — the interactive day OS of the Helix Solutions portfolio.**

Helix-Matrix is a local-first, offline, loopback-only web application that cross-maps
real contact-centre operational friction to governed software systems, drives a daily
learning path through 24 lessons, and keeps a portable record of what you have
answered, graded and decided. It is extracted from the interactive glossary that ships
in the [Helix-Solutions master website](https://github.com/Hatemshalaby15071979/Helix-Solutions)
and now stands on its own as a maintainable, documented, CI-verified project.

*by Helix Solutions*

[![CI](https://github.com/Hatemshalaby15071979/Helix-Matrix/actions/workflows/ci.yml/badge.svg)](https://github.com/Hatemshalaby15071979/Helix-Matrix/actions/workflows/ci.yml)
[![version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![python](https://img.shields.io/badge/python-3.9%2B-green)](https://www.python.org)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)
</div>

---

## What this is and why it's here

I kept a running glossary of the friction I saw on the operational floor — a KPI that
decays, a gate that silently fails, a forecast nobody trusts — and of the software
systems that finally answer each one. The glossary grew into a matrix, the matrix grew
into a day OS with a learning path, and the day OS outgrew the page it lived on. So it
was extracted into this standalone project, with tests, a server, a changelog and CI.

The problem it solves is simple: a professional reader should be able to see, in one
place, which real operational symptom maps to which system, how that system fails
closed, and what is actually verified (with a number and a date) — without anyone
having to reconstruct the story from fourteen repositories.

> Local-first. Your answers live in `learning-records/` on your machine. Nothing here
> is published, and the server binds `127.0.0.1` only.

## What you get

A single-page dashboard served by a dependency-free Python server, made of:

| Area | What it does |
|---|---|
| **Problem → tool matrix** | 20 mapped systems (from the four 2026 precursors to Helix Codex, plus the account portfolio and master website) with term definitions, repository context, fail-closed mechanics and verified test counts. |
| **Floor symptom diagnostic** | Nine operational symptoms routed to the gate that handles each one, with lineage. |
| **Topology schematic** | An SVG contract-boundary map: precursors → governed core → live verticals and satellites. |
| **Today · control room** | A prayer-window task spine (Fajr–Isha, Cairo, computed offline), a focus card, quick capture with priorities, a body-double timer and a Maghrib shutdown ritual. |
| **Learning path** | 24 short lessons across four domains (Governance & Audit, Workforce Management, AI Runtimes, Tech Stack), each with a quiz, homework and a local source note. |
| **Adaptive loop** | Quiz results pick the next lesson; missed glossary terms return on a 1/3/7/14/30-day ladder; a competence map plots growth by domain and month. |
| **Weekly review** | A five-minute loop that writes what was recorded, what stayed open, and next week's focus, then rolls four weeks into a monthly trend. |
| **German v5 track** | A read-only reader of the 12 pilot listening lessons (A1–C2) from the `Mannschaft` repository, with its own six-term app glossary. |
| **n8n panel** | A live local health probe of the self-hosted n8n Production Starter. |
| **Portable history** | Export and import your learning records as plain JSON. |
| **Sami** | A voice companion with a metacognitive memory: it locates files, hands off web search, answers from recorded facts, and only records a decision when you approve it. |

## How to use it

```bash
python3 server/os_server.py
# then open http://127.0.0.1:8765/ — the whole dashboard, on your machine only
```

Or:

```bash
./scripts/serve.sh    # start the server detached, with its own log file
./scripts/launch.sh   # start it and open the browser for you
./scripts/verify.sh   # prove the repo still works: 28 tests + compile + JS + JSON checks
```

No dependencies. The server is the standard library; the lessons, glossary and matrix
are plain HTML/JS. The day OS reads the project clones that live in a sibling
`remotely-active/` folder (or a path you set with the `HELIX_MATRIX_PROJECTS`
environment variable) for live status lines; missing projects stay visibly missing —
a gap is shown, not invented.

## The rules we build by

This project obeys [CONSTITUTION.md](CONSTITUTION.md): fail closed (a missing input or
a missing authority is a refusal, never a guess), evidence before claims (every
published number carries a command, a date and an artifact), local-first and
loopback-only, a human always in charge, and honest about limits — simulated things are
labelled simulated, and nothing here pretends to be something it is not.

## Current status

**v1.0.0 shipped 2026-11-26 — CI green, tag `v1.0.0` pushed, 28 tests passing.**
What is *not* yet true: the project status lines in the matrix depend on the sibling
`remotely-active/` folder of clones being present; without it the day OS reports the
gap instead of showing stale data. The learning records in `learning-records/` are
personal and git-ignored — they never leave your machine.

## Where things live

```
app/index.html            the dashboard (matrix, topology, glossary, day OS)
assets/css/               day-os.css, shell.css, sami.css, base.css
assets/js/                day-os.js, shell.js, sami.js
lessons/                  24 interactive lessons + INDEX.md
reference/                glossary.html + one local source note per lesson
data/metacognition.json   Sami's metacognitive memory
learning-records/         your answers, quiz attempts, day state (local, git-ignored)
server/                   os_engine.py (day logic) + os_server.py (the server)
tests/                    engine tests (28)
scripts/                  serve.sh, launch.sh, package.sh, verify.sh
deploy/                   systemd unit + desktop entry
docs/                     quickstart, architecture, deployment, release
.github/workflows/        ci.yml
```

The Helix Solutions logo is embedded from the
[Helix-Solutions master site](https://github.com/Hatemshalaby15071979/Helix-Solutions)
raw URL — one image source for every repository and page on the account.

## Testing

```bash
python3 -m pytest tests/ -q
```

The suite covers the day engine: prayer-window maths, task generation, lesson choice,
answer records, portable export/import and the German reader.

## Security posture

- Binds `127.0.0.1` only; there is no public endpoint.
- No secrets, tokens or API keys are read, stored or transmitted.
- Web search is an explicit handoff to your browser, not a claim of having read a page.
- Learning records are personal and are excluded from publication by `.gitignore`.

## Licence & contact

MIT — see [LICENSE](LICENSE).

© 2026 Hatem Shalaby / Helix Solutions ·
[github.com/Hatemshalaby15071979](https://github.com/Hatemshalaby15071979) ·
[LinkedIn: Hatem Shalaby](https://www.linkedin.com/in/hatem-shalaby-202902127)
