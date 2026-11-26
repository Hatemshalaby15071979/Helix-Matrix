# Architecture

## Two halves

The application is deliberately split into a **deterministic engine** and a **thin server**,
so the interesting logic is testable without a running process.

### `server/os_engine.py` — the day engine

Pure functions over plain data. It owns:

- **Offline prayer-time maths.** Fajr, Dhuhr, Asr, Maghrib and Isha for Cairo are computed
  from the Egyptian General Authority of Survey angles (Fajr 19.5°, Isha 17.5°) using a
  mean-solar-time approximation. No network.
- **Task generation.** A short day of tasks, one per prayer window, built from the lesson
  plan, the German track, the glossary drill, the project status and a day check.
- **Adaptive lesson choice.** The next lesson is picked from real quiz signal (the weakest
  unrecorded concept) rather than calendar order; a recorded-but-failed lesson becomes a
  must-priority review task.
- **Spaced repetition.** Missed glossary terms are scheduled on a 1/3/7/14/30-day ladder.
- **Portable history.** Export is a plain-JSON snapshot of answers, quiz attempts, term
  grades, day state, weekly reviews and decisions; import validates before it merges.
- **German reader.** Read-only access to the 12 pilot listening lessons in the `Mannschaft`
  repository.
- **Honest gaps.** A project with no status file is reported as a gap; the engine never
  invents a status a file does not contain.

### `server/os_server.py` — the thin server

An `http.server`-based application, standard library only, that binds `127.0.0.1:8765` and
serves:

- the dashboard (`app/index.html`) and static assets;
- the lessons, the glossary and the source-note JSON;
- JSON endpoints: `/api/day`, `/api/week`, `/api/competence`, `/api/german`, `/api/meta`,
  `/api/n8n`, `/api/export`, `/api/import/validate`, `/api/approve`, `/api/files`;
- the answer form (`/record/<lesson>`) and the day note form (`/note/<date>`);
- read-only project-file access (`/file/...`) restricted to plain-text files inside
  `remotely-active/`.

The server keeps no state of its own; all durable state is written atomically (write to a
`.tmp` file, then rename) under `learning-records/`.

## Data flow

```
lessons/ + reference/ + data/metacognition.json   (committed)
                │
                ▼
       os_engine.py  ────────────────────────────────┐
                │                                     │
   read-only: remotely-active/* status files          │
                │                                     ▼
                └────────────────────►  os_server.py (127.0.0.1:8765)
                                            │
                                            ▼
                        learning-records/   (local, git-ignored)
```

## Design rules

- **Local-first, offline.** No cloud, no third-party Python packages, no secrets.
- **Loopback only.** The process binds `127.0.0.1`; there is no public surface.
- **Evidence before claims.** The engine surfaces what the source files contain and marks
  everything else as an explicit gap.
- **Personal data stays personal.** `learning-records/` is excluded from git and is never
  published.
