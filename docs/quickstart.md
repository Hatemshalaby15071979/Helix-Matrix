# Quickstart

Helix-Matrix has no build step and no third-party dependencies.

## Run it

```bash
cd helix-matrix
python3 server/os_server.py
# open http://127.0.0.1:8765/ in a browser
```

The server uses only the Python standard library (3.9 or newer).

## Detached start (with its own log)

```bash
./scripts/serve.sh
# logs to /tmp/opencode/helix-matrix.log
# safe to run twice — it leaves an already-live server alone
```

## Open it in a browser

```bash
./scripts/launch.sh
```

## Point it at your project clones

The day OS reads project status files from a sibling `remotely-active/` folder, in this
order:

1. the `HELIX_MATRIX_PROJECTS` environment variable, if set;
2. `../remotely-active` relative to the app;
3. `../../remotely-active` relative to the app (the layout used inside the owner's workspace).

If none of those exist, the app starts anyway and shows the missing projects as honest
gaps rather than inventing a status.

```bash
HELIX_MATRIX_PROJECTS=/path/to/remotely-active python3 server/os_server.py
```

## Your data

Written answers, quiz attempts, graded terms, day state, weekly reviews and approved
decisions live under `learning-records/` on your machine. They are local by design and are
excluded from git by `.gitignore`. Export them at any time from the **Portable history**
section of the app.
