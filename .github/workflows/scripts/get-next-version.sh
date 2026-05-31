#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Resolve the version to release and emit GitHub Actions outputs (latest_tag,
# new_version — both with a leading "v").
#
# Rule:
#   - If pyproject.toml declares a version NEWER than the latest git tag, release
#     that exact version. This is how a maintainer cuts a minor or major bump:
#     edit `version` in pyproject.toml and merge — no manual tag required.
#   - Otherwise, auto-increment the patch component of the latest tag (the normal
#     "every merge ships a patch" path).

# Latest tag reachable from HEAD, or v0.0.0 if there are no tags.
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "latest_tag=$LATEST_TAG" >> "$GITHUB_OUTPUT"
TAG_VERSION=${LATEST_TAG#v}

# Version declared in pyproject.toml (the first `version = "..."`).
PYPROJECT_VERSION=$(grep -m1 -E '^version = "' pyproject.toml | sed -E 's/^version = "([^"]+)".*/\1/')

# Treat pyproject as authoritative when it is strictly newer than the latest tag
# (version-sorted). Equal or older falls through to the patch bump.
if [[ -n "$PYPROJECT_VERSION" && "$PYPROJECT_VERSION" != "$TAG_VERSION" \
      && "$(printf '%s\n%s\n' "$TAG_VERSION" "$PYPROJECT_VERSION" | sort -V | tail -1)" == "$PYPROJECT_VERSION" ]]; then
  NEW_VERSION="v$PYPROJECT_VERSION"
  echo "pyproject.toml ($PYPROJECT_VERSION) is ahead of latest tag ($LATEST_TAG) — releasing $NEW_VERSION."
else
  IFS='.' read -ra VERSION_PARTS <<< "$TAG_VERSION"
  MAJOR=${VERSION_PARTS[0]:-0}
  MINOR=${VERSION_PARTS[1]:-0}
  PATCH=${VERSION_PARTS[2]:-0}
  PATCH=$((PATCH + 1))
  NEW_VERSION="v$MAJOR.$MINOR.$PATCH"
  echo "Auto-incrementing patch from $LATEST_TAG."
fi

echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
echo "New version will be: $NEW_VERSION"
