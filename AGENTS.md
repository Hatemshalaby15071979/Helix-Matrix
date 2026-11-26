# AGENTS.md — Agent Charter & Ledger for Helix-Matrix

> **Read order (mandatory, every landing):** `AGENTS.md` → `CONSTITUTION.md` →
> `GOVERNANCE.md` → `README.md`. Then **sign in** to the ledger below, do the work,
> **sign out**. No entry, no trust: an unlogged session's work is treated as unverified
> until someone checks it.

## 1. Who agents are here

An "agent" is any entity that reads or writes this repository — an AI model, an
automation script, or a human acting as operator. There is exactly **one supreme
authority**: the repository owner (**Hatem Shalaby**). An agent acts only on the
owner's instruction and records every landing.

## 2. The mandatory sign-in / sign-out rule

Every agent, on **every landing** (a landing = one session that ends with the agent
stopping, whether the task is finished or not), must:

1. **SIGN IN** before any write action — who, why, what will be touched, sensitive or
   network actions planned, and the **date and time from the system clock**.
2. **SIGN OUT** when the landing's work is complete or stopped — what changed, why,
   the files touched, evidence of verification, and **the current status when leaving**,
   written so the next agent can continue without re-discovery.

Fail closed: if a task cannot be completed, still sign out and state exactly what is
incomplete. Never claim verification that did not happen.

### Entry format

```
## [YYYY-MM-DD HH:MM TZ] — <agent name / model>
Task: <what was assigned>
Touched: <files created / modified / deleted / moved>
Why: <the reasoning, not just the diff>
Verification: <what was actually checked and the observed result>
Left undone: <what is incomplete, needs review, or is deferred — or "nothing">
Sensitive: <any remote writes, secrets, or destructive actions, or "none">
```

## 3. Environment facts

- **Repo:** Helix-Matrix — local-first, offline, loopback-only operations & AI portfolio
  matrix: 20 mapped systems, day OS, 24-lesson learning path, portable learning history.
- **Owner account:** https://github.com/Hatemshalaby15071979
- **Default branch:** main
- **Where it runs:** `python3 server/os_server.py` → http://127.0.0.1:8765/ (loopback only)
- **Verification command:** `./scripts/verify.sh` (28 tests + compile + JS + JSON + version consistency)

## 4. Rules this agent must follow

- Read and obey **CONSTITUTION.md** (philosophy + clean-code policy). On conflict, it
  wins over this file.
- Follow **GOVERNANCE.md** for the repo map, documentation policy, and archiving rules.
- Keep `README.md` the single source of truth; landing pages and dashboards mirror it.
- Keep local and remote in harmony: after a sanctioned change, commit and push so the
  GitHub copy matches the working copy.
- Sign in and sign out every landing, with the real clock time.

## 5. Ledger (sign-in / sign-out)

**STATUS WHEN LAST LEFT:** v1.0.0 shipped 2026-11-26, CI green, tag v1.0.0;
learning-records/ is personal and git-ignored; project clones are read from a
sibling remotely-active/ folder.

## 2026-11-26 20:39 EET — CODEX subagent (uniform governance pass)
Task: apply the owner's uniform governance pass to this repository — add CONSTITUTION.md
at the root, create this AGENTS.md and a GOVERNANCE.md from the house templates, bring
README.md to the house README style (logo embed + section order) and app/index.html to
the house index style (brand bar sub-line, footer line, single-source logo URL).
Touched: CONSTITUTION.md (new), AGENTS.md (new), GOVERNANCE.md (new), README.md
(logo embed, house section order, repo-layout line corrected for the single-source logo),
app/index.html (.side-brand "by Hatem Shalaby" sub-line, .hs-brand logo switched to the
master-site raw URL, house footer line added, one stale brand data line corrected),
and the pre-existing uncommitted deletion of assets/img/helix-solutions-logo.svg was
staged (the master site is now the single image source).
Why: owner instruction 2026-11-26 — one unified governance text and one house style
across every repository.
Verification: `./scripts/verify.sh` green (28 tests + compile + JS syntax + JSON +
version consistency); CONSTITUTION.md md5-identical to the canonical template; plain
push to origin main.
Left undone: nothing.
Sensitive: plain `git push origin main` (explicitly authorised by the owner's
"Push all repos now" instruction); no force push, no PR/issue writes.
