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

## 2026-11-27 04:58 EET — sami (Claude), portfolio governance subagent
STATUS: SIGN-IN

Task: Mirror the root-document assertion the owner approved in Assay on 2026-11-27
(`scripts/check-scaffold.py`) across the governance repositories, then fix what it finds.
Sign in before any write to Helix-Matrix.

Touched (planned): `scripts/check_root_docs.py` (new); `LICENSE` (new — the GOVERNANCE.md
section 2 table lists it, README.md already links to it, and the link is currently broken);
`SECURITY.md` (new — same table); `scripts/verify.sh` and `.github/workflows/ci.yml` (the
gate runs in both, so local and CI agree); `AGENTS.md` (this entry and the sign-out).

Why: GOVERNANCE.md section 2 says "No stray `.md`/`.txt` at the root", but nothing asserted
the *absence* direction — only that the known documents were present. A one-way check
cannot enforce a "nothing else at the root" rule, which is how the 2026-11-26 pass could
archive reports while the root set still looked satisfied.

Sensitive: `git push origin main` (owner's instruction in chat, 2026-11-27). No force push,
no PR or issue writes, no secrets.

## 2026-11-27 05:06 EET — sami (Claude), portfolio governance subagent
STATUS: SIGN-OUT (landing complete)

Task: Mirror Assay's root-document assertion (approved by the owner 2026-11-27) into
Helix-Matrix, then fix what it found. Done.

Touched: `scripts/check_root_docs.py` (new — byte-identical to the copy landed in Assay,
createlee, Helix-Codex and Helix-Solutions); `LICENSE` (new, MIT, byte-identical to
Assay's); `SECURITY.md` (new); `scripts/verify.sh` (new "root-document hygiene" step);
`.github/workflows/ci.yml` (same step, so local and CI agree); `AGENTS.md` (this entry and
the sign-in above). No file moved, renamed or deleted.

Why: GOVERNANCE.md section 2 says "No stray `.md`/`.txt` at the root", but nothing asserted
the *absence* direction — only that the known documents were present, which is how the
2026-11-26 pass could archive reports while the root set still looked satisfied. The gate
now asserts both directions: every root document the section 2 table names exists, and
nothing unlisted sits beside them. The allowed set is parsed out of GOVERNANCE.md, so the
policy keeps one source of truth.

The gate found two real gaps, both now closed. The section 2 table lists `LICENSE` and
`SECURITY.md`; neither existed, and `README.md` has linked to `LICENSE` since the house
README landed — that link was broken on GitHub until this landing. `LICENSE` is the MIT
text the repository already declares in README.md and in the GOVERNANCE.md section 1 repo
map, so nothing new is being asserted here. `SECURITY.md` states the posture, the threat
model (including that `HELIX_MATRIX_HOST` can widen the loopback default and that the
server is unauthenticated by design), the containment guards on `/file/`, `/project/` and
the static handler, and the honest non-goals.

Verification: `bash scripts/verify.sh` → ALL CHECKS PASSED: 27 tests passed, 1 skipped;
byte-compile, JS syntax, JSON and version-consistency all green; and the new step prints
"check_root_docs: OK -- Helix-Matrix/ holds only the GOVERNANCE.md section 2 set" followed
by "check_root_docs: self-test OK -- 7/7 cases behaved" (a planted `STRAY-NOTE.md` and a
planted `NOTES.txt` each stop the gate; a missing required document stops it;
`requirements.txt` at the root is acknowledged as a non-document; a stray under `docs/` is
ignored; an unparsable section 2 fails closed). CI on the pushed commits is the record of
the same steps on a clean runner.

Left undone: nothing failing.

Sensitive: plain `git push origin main` (owner's instruction in chat, 2026-11-27); no force
push, no PR/issue writes, no secrets.
