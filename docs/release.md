# Release process

Helix-Matrix is versioned with a single source of truth and a small, repeatable release
path.

## Version source of truth

- The current version is written in `VERSION` (semver).
- The server reports it as the `Server` header value (`HelixMatrix/<version>`).
- Keep all three in lockstep when you bump: the `VERSION` file, any user-facing version
  text, and the release tag.

## Creating a release

1. **Bump `VERSION`.**
2. **Update `CHANGELOG.md`** with the new version, date and the user-facing changes.
3. **Run the checks** so the release is verified, not assumed:

   ```bash
   ./scripts/verify.sh
   ```

   This runs the test suite, byte-compiles the server, syntax-checks the JavaScript,
   validates the JSON data files and confirms the version strings agree.

4. **Tag and push** (the owner's normal release flow on this account):

   ```bash
   git tag -a v$(cat VERSION) -m "v$(cat VERSION)"
   git push origin main --tags
   ```

5. **Optional GitHub release.** A tag is enough for this local-first tool; a GitHub release
   note summarising the changelog entry is a nice touch but not required for use.

## Packaging for distribution

```bash
./scripts/package.sh
# writes dist/helix-matrix-<version>.tar.gz
```

The tarball contains the app, assets, lessons, docs, scripts and server — everything needed
to run — plus the committed sample learning records, but no `__pycache__` and no local
`learning-records/` state (which is personal and git-ignored).

## Release checklist

- [ ] `VERSION` bumped and consistent with the changelog and the server header.
- [ ] `./scripts/verify.sh` is green.
- [ ] The tag is pushed.
- [ ] Personal `learning-records/` state was not committed (`.gitignore` covers it).
- [ ] No secrets or local paths leaked into committed files.
