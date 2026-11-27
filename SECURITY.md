# Helix-Matrix — Security

## The security posture in one line

**Everything stays on your machine.** The app serves one loopback address, reads no
secrets, calls no model service, and keeps your learning history in local files that
`.gitignore` excludes from publication.

## Threat model (summary)

| Threat | Mitigation |
|---|---|
| Reaching the app from another machine | `server/os_server.py` binds `127.0.0.1` by default (loopback only). `HELIX_MATRIX_HOST` can override that; setting it to a routable address publishes an **unauthenticated** server, so treat it as a deliberate, temporary act, never a setting to leave behind. |
| A local process reading or changing your records | There is no authentication by design — this is a single-user local app. Any process running as you can already read the same files directly, so the API adds no exposure; it does mean another account on a shared machine should not be given access to this one. |
| Path traversal through the read endpoints | `/file/…`, `/project/…` and the static handler reject `..`, leading-dot names and backslashes, then resolve the target and confirm it stays inside its configured root (`inside()`), and serve only an allowlisted set of suffixes. A request that escapes is answered `404`. |
| Personal data leaking into the repository | Answers, quiz attempts, term grades, day state, day notes and metacognition decisions live under `learning-records/` and are git-ignored. The single committed record is an intentional format fixture, not personal data. |
| Secrets in the tree | None are read, stored or transmitted. There is no API key, token or credential anywhere in the server path. |
| Supply chain | The server and engine use the Python standard library only — no third-party runtime dependency, so there is no dependency tree to poison. |
| Outbound calls | The only outbound requests are loopback health probes to `127.0.0.1:8766` and `127.0.0.1:5678`. Web search is an explicit handoff to your own browser, never a claim to have read a page. |
| Eavesdropping on the wire | The server speaks plain HTTP, which is appropriate for loopback and inappropriate beyond it. Do not expose it to a network without putting a TLS-terminating proxy in front. |

## Non-goals (honest)

- This is **not** a hardened multi-user service. It has no accounts, no sessions, no
  authorization layer, and it does not need them for one person on one machine.
- The "live" indicators for sibling services are health probes, not verified integrity:
  a reachable service is reported as reachable, nothing more.
- It is not a backup system. `export_history` writes a portable copy on demand; keeping
  that copy somewhere safe is your job.

## Reporting Security Issues

Please do **not** open a public issue for a security problem.

1. Open the **Security** tab of this repository.
2. Choose **Report a vulnerability** (GitHub Security Advisories).
3. Describe the issue, the endpoint or file affected, and how to reproduce it.

The report is visible only to the maintainers, and you get a reply in the advisory thread
once it has been triaged.

## Supported versions

`main` is the only supported line. Fixes land there; older branches are not maintained.
