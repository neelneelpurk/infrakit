# Releasing InfraKit

This document covers how InfraKit ships releases to PyPI and GitHub, and what to do when a release misbehaves.

## TL;DR

> **`pyproject.toml` is the source of truth for the version. Bump it, merge to `main`, and the release ships itself: PyPI upload, GitHub Release, and tag — all in one workflow run.**

A merge to `main` that changes the version cuts a release of that exact version (patch, minor, or major). A merge that leaves the version untouched is a no-op — the workflow runs but stops at the "release already exists" guard. The contract is: the version in `pyproject.toml` is the version on PyPI.

## The release pipeline

The full pipeline lives in a single workflow — [`.github/workflows/release.yml`](./.github/workflows/release.yml). Every push to `main` runs it. Each run does, in order:

1. **Read the version** from `pyproject.toml` (e.g. `1.0.0` → `v1.0.0`). This is the version that will be released — CI does not compute or bump it.
2. **Skip if the release already exists.** If a GitHub Release for that version is already published, every remaining step is skipped. This is the idempotency guard: merges that don't touch the version do nothing, and a half-finished run can be re-run safely.
3. **Build wheel + sdist** with `uv build`. Templates are force-included into the wheel via `[tool.hatch.build.targets.wheel.force-include]`.
4. **`twine check --strict`** against the built artifacts. Catches malformed README, broken `long_description_content_type`, missing license, etc. before they reach PyPI.
5. **Generate release notes** from the commits since the last tag.
6. **Publish to PyPI** via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (PEP 740 / OIDC). No API token in the repo.
7. **Create GitHub Release** with the wheel + sdist attached. `gh release create --target main` creates the tag server-side against the commit on `main` at the same time.

CI never writes to `pyproject.toml` and never pushes a commit back to `main` — the released version is exactly what the merging PR set. If any step fails, subsequent steps are skipped, so the next CI run retries from the same version number. PyPI publish + GitHub Release + tag therefore ship atomically: either all three or none.

## One-time setup (already done)

These steps were performed once when the project was first published. They're documented here for reference and disaster recovery.

### 1. Reserve the project name on PyPI

```bash
# Local
uv build
uvx twine upload dist/*
```

This is the only time a maintainer uploads from a laptop. Once the project exists on PyPI, switch to Trusted Publishing for all subsequent releases.

### 2. Configure Trusted Publishing on PyPI

1. Go to <https://pypi.org/manage/project/infrakit-cli/settings/publishing/>.
2. Click **Add a new pending publisher** (or **Add a new publisher** if `0.1.0` is already uploaded).
3. Fill in:
   - **PyPI Project Name:** `infrakit-cli`
   - **Owner:** `neelneelpurk`
   - **Repository name:** `infrakit`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Save.

### 3. Configure the `pypi` environment in GitHub

1. Go to <https://github.com/neelneelpurk/infrakit/settings/environments>.
2. Create environment named `pypi`.
3. (Optional but recommended) Add a required reviewer for the environment — a small friction that prevents accidental releases from rebase-merges that touched the wrong paths.

After these three steps, the workflow's `pypa/gh-action-pypi-publish` step authenticates against PyPI via OIDC. No tokens stored anywhere.

## What triggers a release

**Any merge to `main` that bumps the version in `pyproject.toml`.** The workflow runs on every push to main, but only the runs where `pyproject.toml`'s version has no existing GitHub Release actually publish — the rest stop at the idempotency guard.

This is a deliberate choice. Tying the release to the version in `pyproject.toml` means the version on PyPI always matches the version in the repo at that commit — no CI-side computation, no version-bump commit pushed back to main, no drift between the tag and the package metadata. The trade-off versus auto-bumping every merge is that you have to remember to bump the version when you want to ship; the idempotency guard makes forgetting harmless (no duplicate release), and the CHANGELOG entry is the natural place to notice.

To land changes *without* a release — in-progress doc cleanup, a refactor that isn't worth a version — just don't touch `version`; the merge is a no-op for the release pipeline.

### Manual / on-demand runs

You can fire the workflow by hand (e.g. to re-run after a transient failure):

```bash
gh workflow run release.yml --ref main
```

It reads the current `pyproject.toml` version and releases it if that version hasn't been released yet — same outcome as a merge. Running it when the version already has a release is a safe no-op.

## Versioning

InfraKit follows [Semantic Versioning](https://semver.org/). The version lives in `pyproject.toml` and is the single source of truth for both PyPI and the git tag.

To cut any release — patch, minor, or major — edit `version` in `pyproject.toml`, add a CHANGELOG entry, and merge to `main`:

```toml
# pyproject.toml
[project]
name = "infrakit-cli"
version = "1.0.1"   # was 1.0.0 — this single edit is the whole release
```

There is no separate `git tag` step — the workflow creates the matching tag (`v1.0.1`) when it publishes. Breaking changes are flagged with `!` in the commit subject (e.g. `feat(packaging)!:`) and warrant a minor or major bump.

## Local sanity checks before pushing

```bash
# Build + render check
uv build
uvx twine check --strict dist/*

# Confirm templates are inside the wheel
unzip -l dist/infrakit_cli-*.whl | grep templates | head

# Run the full test suite + ruff (CI parity)
uv run pytest
uvx ruff check src/

# Offline e2e: install the wheel into a fresh venv and run infrakit init
uv venv /tmp/release-check
uv pip install --python /tmp/release-check/bin/python dist/infrakit_cli-*.whl
mkdir -p /tmp/release-check-project && cd /tmp/release-check-project
/tmp/release-check/bin/infrakit init demo --ai claude --iac terraform \
    --script sh --no-git --ignore-agent-tools
test -f demo/.claude/commands/infrakit:setup.md
```

If all of those pass, your change is safe to merge — the CI will rerun the same checks under `twine check --strict` before publishing.

## Disaster recovery

### Released a broken version to PyPI

PyPI does **not** allow re-uploading the same version. Options:

1. **Yank the broken release** at <https://pypi.org/manage/project/infrakit-cli/release/X.Y.Z/>. Yanked versions remain installable by exact `==X.Y.Z` but no longer satisfy version ranges.
2. **Cut a new patch version** with the fix. This is the normal path — yanking + bumping is much easier than trying to recover the broken version.

### PyPI publish step failed mid-way

No GitHub Release is created until *after* PyPI publish succeeds, so a failed publish leaves no release for that version. Re-run the workflow (`gh workflow run release.yml --ref main`) — it reads the same version from `pyproject.toml`, finds no existing release, and retries from the top.

### GitHub Release was created but PyPI publish failed

Unusual ordering, but possible if you re-run a partially-completed workflow. Delete the GitHub release manually:

```bash
gh release delete vX.Y.Z --yes
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

Then re-trigger the workflow.

## Manual emergency release from a laptop

Only do this if Trusted Publishing is broken or PyPI's OIDC verification is down. Requires a PyPI API token with upload permission for `infrakit-cli`.

```bash
git checkout main && git pull
uv build
uvx twine check --strict dist/*
uvx twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

Then create the corresponding tag + GitHub release manually so the workflow doesn't try to re-release the same version.
