# Helix-Matrix

**Operations & AI Portfolio Reference Matrix — the interactive day OS of the Helix Solutions portfolio.**

Helix-Matrix is a local-first, offline, loopback-only web application that cross-maps real
contact-centre operational friction to governed software systems, drives a daily learning
path through 24 lessons, and keeps a portable record of what you have answered, graded and
decided. It is extracted from the interactive glossary that ships in the
[Helix-Solutions master website](https://github.com/Hatemshalaby15071979/Helix-Solutions)
and now stands on its own as a maintainable, documented, CI-verified project.

> Local-first. Your answers live in `learning-records/` on your machine. Nothing here is
> published, and the server binds `127.0.0.1` only.

[![CI](https://github.com/Hatemshalaby15071979/Helix-Matrix/actions/workflows/ci.yml/badge.svg)](https://github.com/Hatemshalaby15071979/Helix-Matrix/actions/workflows/ci.yml)
[![version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![python](https://img.shields.io/badge/python-3.9%2B-green)](https://www.python.org)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)

---

## What it is

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

## How to run it

```bash
python3 server/os_server.py
# open http://127.0.0.1:8765/
```

Or:

```bash
./scripts/serve.sh    # start the server detached, with its own log
./scripts/launch.sh   # start it and open the browser
```

No dependencies. The server is the standard library; the lessons, glossary and matrix are
plain HTML/JS. The day OS reads the project clones that live in a sibling
`remotely-active/` folder (or a path you set with the `HELIX_MATRIX_PROJECTS` environment
variable) for live status lines; missing projects stay visibly missing.

## Repository layout

```
app/index.html            the dashboard (matrix, topology, glossary, day OS)
assets/css/               day-os.css, shell.css, sami.css, base.css
assets/js/                day-os.js, shell.js, sami.js
assets/img/               the canonical Helix Solutions logo
lessons/                  24 interactive lessons + INDEX.md
reference/                glossary.html + one local source note per lesson
data/metacognition.json   Sami's metacognitive memory
learning-records/         your answers, quiz attempts, day state (local data)
server/                   os_engine.py (day logic) + os_server.py (the server)
tests/                    engine tests
scripts/                  serve.sh, launch.sh, package.sh, verify.sh
deploy/                   systemd unit + desktop entry
docs/                     quickstart, architecture, deployment, release
.github/workflows/        ci.yml
```

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

## Licence

MIT — see [LICENSE](LICENSE).

© 2026 Hatem Shalaby / Helix Solutions · [github.com/Hatemshalaby15071979](https://github.com/Hatemshalaby15071979)
