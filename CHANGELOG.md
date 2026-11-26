# Changelog

All notable changes to this project are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-11-26

### Added
- First standalone release of Helix-Matrix, extracted from the interactive glossary that
  ships in the Helix-Solutions master website.
- Professional repository layout: `app/`, `assets/`, `lessons/`, `reference/`, `data/`,
  `server/`, `tests/`, `scripts/`, `deploy/`, `docs/`.
- 20-system problem → tool matrix, including the account portfolio and the master website.
- Day OS: offline Cairo prayer-window task spine, focus card, quick capture, body-double
  timer, Maghrib shutdown ritual.
- Learning path: 24 lessons across four domains with quizzes, homework and one local
  source note each.
- Adaptive loop: quiz-driven lesson choice, 1/3/7/14/30-day spaced glossary repetition,
  competence map, weekly review rolled into a monthly trend.
- German v5 read-only track (12 pilot lessons A1–C2) and its six-term app glossary.
- n8n Production Starter live local health panel.
- Portable history: JSON export/import of answers, quiz, grades, reviews and decisions.
- Sami voice companion with a metacognitive memory that only records a decision when
  approved.
- CI workflow, packaging and verify scripts, systemd unit and desktop entry.

### Changed
- Server path layer rewritten for the new layout; project clones are read from a sibling
  `remotely-active/` folder (overridable via `HELIX_MATRIX_PROJECTS`).
- Server reports its identity as `HelixMatrix/<version>`.

## [0.x] - 2026-11-19 … 2026-11-22

Development history while the app lived inside the Repos_Readmes workspace as the
`cockpit/` day OS and the `Operations___AI_Glossary_Reference_Matrix.html` page: dark
theme, sidebar index, planning control room, Sami panel, the five recommendation loops,
the n8n and German tracks, and the rebrand to Helix-Matrix.
