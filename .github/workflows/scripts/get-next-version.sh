#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Resolve the release version. pyproject.toml is the source of truth: whatever
# version it declares is the version we release. A release only actually fires
# if no GitHub Release exists for that version yet (see check-release-exists.sh),
# so bumping `version` in pyproject.toml — in a normal PR — is what cuts a
# release; merges that leave it untouched are no-ops.
#
# Outputs (GitHub Actions):
#   new_version  the version to release, e.g. v1.0.0 (from pyproject.toml)
#   latest_tag   the most recent existing tag, used only to bound the
#                release-notes commit range (latest_tag..HEAD)
# Usage: get-next-version.sh

# Read the project version from pyproject.toml (the first `version = "..."`).
PYPROJECT_VERSION=$(grep -m1 -E '^version = "' pyproject.toml | sed -E 's/^version = "(.+)"/\1/')

if [ -z "$PYPROJECT_VERSION" ]; then
  echo "ERROR: could not read 'version' from pyproject.toml" >&2
  exit 1
fi

NEW_VERSION="v$PYPROJECT_VERSION"

# Most recent existing tag — for the release-notes range only. v0.0.0 if none.
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT
echo "Releasing $NEW_VERSION (from pyproject.toml); latest existing tag: $LATEST_TAG"
