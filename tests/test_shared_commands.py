"""Tests for the shared IaC command skeletons (templates/iac/_shared/commands/).

These commands are written once and rendered per-tool by filling
``{{TOKEN}}`` placeholders from each tool's ``templates/iac/<tool>/profile.yaml``.
The key invariant — the one that makes drift structurally impossible — is that
**every token used by a skeleton is supplied by every tool's profile**. Add a
token to a skeleton without adding it to all profiles and this suite fails.
"""

import re

import pytest

from infrakit_cli.iac_config import IAC_CONFIG
from infrakit_cli.template_renderer import load_profile, render_command, templates_root

SHARED = templates_root() / "iac" / "_shared" / "commands"
TOOLS = ["terraform", "crossplane", "cloudformation"]
TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def _skeletons():
    return sorted(SHARED.glob("*.md")) if SHARED.is_dir() else []


def test_shared_commands_dir_has_skeletons():
    assert SHARED.is_dir(), f"missing shared commands dir: {SHARED}"
    assert _skeletons(), "no shared command skeletons found"


@pytest.mark.parametrize("skeleton", _skeletons(), ids=[p.stem for p in _skeletons()])
def test_skeleton_has_frontmatter_and_arguments(skeleton):
    text = skeleton.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skeleton.name} missing YAML frontmatter"
    assert "argument-hint:" in text, f"{skeleton.name} missing argument-hint"
    assert "$ARGUMENTS" in text, f"{skeleton.name} missing $ARGUMENTS placeholder"


@pytest.mark.parametrize("tool", TOOLS)
def test_every_skeleton_token_is_supplied_by_every_profile(tool):
    """The drift guard: a profile must define every token its skeletons use."""
    profile = load_profile(templates_root() / "iac" / tool)
    assert profile, f"{tool} has no profile.yaml"
    needed: set[str] = set()
    for sk in _skeletons():
        needed |= set(TOKEN_RE.findall(sk.read_text(encoding="utf-8")))
    missing = sorted(t for t in needed if t not in profile)
    assert not missing, f"{tool}/profile.yaml missing tokens used by shared skeletons: {missing}"


@pytest.mark.parametrize("tool", TOOLS)
def test_rendered_skeletons_have_no_unfilled_tokens(tool):
    profile = load_profile(templates_root() / "iac" / tool)
    for sk in _skeletons():
        rendered = render_command(
            sk.read_text(encoding="utf-8"),
            args_token="$ARGUMENTS",
            agent="claude",
            profile=profile,
        )
        leftover = TOKEN_RE.findall(rendered)
        assert not leftover, f"{tool} {sk.name}: unfilled tokens {leftover}"


def test_quick_fix_is_shared_and_not_per_tool():
    assert (SHARED / "quick_fix.md").is_file(), "quick_fix shared skeleton missing"
    for tool in TOOLS:
        per_tool = templates_root() / "iac" / tool / "commands" / "quick_fix.md"
        assert not per_tool.exists(), f"{tool} still has a per-tool quick_fix.md"
        assert "quick_fix" in IAC_CONFIG[tool]["iac_commands"]


@pytest.mark.parametrize(
    "tool,marker",
    [("terraform", "tofu"), ("crossplane", "crossplane render"), ("cloudformation", "cfn-lint")],
)
def test_quick_fix_renders_tool_specific_content(tool, marker):
    profile = load_profile(templates_root() / "iac" / tool)
    rendered = render_command(
        (SHARED / "quick_fix.md").read_text(encoding="utf-8"),
        args_token="$ARGUMENTS",
        agent="claude",
        profile=profile,
    )
    assert marker in rendered, f"{tool} quick_fix missing validator marker '{marker}'"
    assert profile["ENGINEER_PERSONA"] in rendered  # persona file reference
    assert profile["CREATE_CMD"] in rendered  # full-pipeline escalation
    assert "fast path" in rendered.lower()
    assert "MANDATORY gate" in rendered  # the validation hard gate (#10)
