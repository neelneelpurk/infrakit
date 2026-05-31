"""Mechanical scorer for InfraKit-generated IaC.

This is the deterministic, headless half of the eval harness. It inspects a
directory of *generated* infrastructure code (Terraform `.tf`, Crossplane YAML,
or a CloudFormation template) and scores it against the **secure-defaults** that
InfraKit's personas and coding-style standards promise:

- the output validates (when a validator binary is available),
- encryption at rest is set,
- public access is blocked,
- the required tags are present,
- no secret is hardcoded,
- TLS / secure transport is enforced (storage),
- versioning is enabled (storage),
- deletion safety is set.

It is intentionally heuristic — it reads the code as text and checks whether the
secure-default *made it into the output*. That is exactly the signal we want: a
hallucinated-away `storage_encrypted` or a dropped `block_public_acls` shows up
as a failing check, whatever the surrounding prose says.

The scorer is the reusable, CI-runnable piece. Pair it with a *generator* (today:
the committed example deliverables; tomorrow: the live LLM pipeline — see
``run.py``) to get a full eval.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

PASS, FAIL, NA = "pass", "fail", "na"


@dataclass
class CheckResult:
    check: str
    status: str  # PASS | FAIL | NA
    detail: str = ""


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

_GLOBS = {
    "terraform": ["*.tf"],
    "crossplane": ["*.yaml", "*.yml", "examples/*.yaml"],
    "cloudformation": ["template.yaml", "template.yml", "*.template", "*.yaml"],
}


def _strip_comments(text: str) -> str:
    """Drop comments so checks score actual code, not prose. A fixture whose
    comment says 'no versioning' must not match the versioning check.

    Handles HCL ``/* ... */`` blocks and ``#`` line/inline comments (used by both
    HCL and YAML). Leaves ``//`` alone so URLs (``https://``) survive.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            out.append("")
            continue
        idx = line.find(" #")
        out.append(line[:idx] if idx != -1 else line)
    return "\n".join(out)


def _load(iac: str, directory: Path) -> str:
    """Concatenate the relevant source files for an IaC tool, comments stripped."""
    seen: set[Path] = set()
    parts: list[str] = []
    for pattern in _GLOBS.get(iac, ["*"]):
        for p in sorted(directory.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.add(p)
                parts.append(p.read_text(encoding="utf-8"))
    return _strip_comments("\n".join(parts))


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _matches_any(content: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(content) for p in patterns)


# ---------------------------------------------------------------------------
# Detection patterns (whitespace-tolerant regexes; matched case-insensitively).
# Booleans require the secure value (e.g. `storage_encrypted = true`), so a
# `... = false` doesn't pass the check by mere keyword presence.
# ---------------------------------------------------------------------------

_ENCRYPTION = _compile([
    r"server_side_encryption", r"ServerSideEncryptionConfiguration",
    r"storage_encrypted\s*=\s*true", r"storageEncrypted\s*:\s*true",
    r"sse_algorithm", r"kms_master_key_id", r"KMSMasterKeyID", r"BucketEncryption",
    r"enable_key_rotation\s*=\s*true", r"enableKeyRotation\s*:\s*true",
    r"kmsKeyId", r"kms_key_id", r"encryption_configuration",
])
_PUBLIC_BLOCK = _compile([
    r"block_public_acls\s*=\s*true", r"BlockPublicAcls\s*:\s*true",
    r"aws_s3_bucket_public_access_block", r"PublicAccessBlockConfiguration",
    r"restrict_public_buckets\s*=\s*true", r"RestrictPublicBuckets\s*:\s*true",
    r"publicly_accessible\s*=\s*false", r"publiclyAccessible\s*:\s*false",
])
_PUBLIC_OPEN = _compile([
    r"publicly_accessible\s*=\s*true", r"publiclyAccessible\s*:\s*true",
    r"""acl\s*=\s*["']public-read""", r"AccessControl\s*:\s*PublicRead",
    r"0\.0\.0\.0/0",
])
_DELETION_SAFETY = _compile([
    r"force_destroy\s*=\s*false", r"DeletionPolicy\s*:\s*(Retain|Snapshot)",
    r"deletion_protection", r"deletionProtection", r"prevent_destroy\s*=\s*true",
    r"UpdateReplacePolicy\s*:\s*(Retain|Snapshot)",
])
_TLS = _compile([
    r"aws:SecureTransport", r"require_ssl", r"MinimumProtocolVersion",
    r"ssl_requests_only", r"enforce.?tls",
])
# Comments are stripped before matching, so a plain substring is safe here and
# matches both `aws_s3_bucket_versioning` / `versioning_configuration` (HCL) and
# `VersioningConfiguration` (CFN).
_VERSIONING = _compile([r"versioning"])
_REQUIRED_TAGS = _compile([r"managed-by", r"\benvironment\b"])

# A line that assigns a literal credential: `password`-ish LHS whose RHS is a
# bare/quoted literal rather than a reference or a generator.
_SECRET_KEY_RE = re.compile(
    r"""(?im)^\s*['"]?(master[_-]?user[_-]?password|password|secret|secret[_-]?key|access[_-]?key|api[_-]?key)['"]?\s*[:=]\s*(.+)$"""
)
_SAFE_RHS_MARKERS = (
    "var.", "local.", "data.", "!ref", "!sub", "!getatt", "{{", "${",
    "resolve:", "secretref", "passwordsecretref", "fromsecret", "valuefrom",
)


def _find_hardcoded_secret(content: str) -> str | None:
    for m in _SECRET_KEY_RE.finditer(content):
        key, rhs = m.group(1), m.group(2).strip()
        rhs_l = rhs.lower()
        if rhs_l in ("true", "false", "{", "[", "null", "~", ""):
            continue
        if any(marker in rhs_l for marker in _SAFE_RHS_MARKERS):
            continue
        literal = rhs.strip().strip('"').strip("'")
        if re.fullmatch(r"[A-Za-z0-9!@#%^&*_.+\-]{3,}", literal):
            return f"{key} = {rhs[:40]}"
    return None


# ---------------------------------------------------------------------------
# Validators (run the strongest static check available; NA if no tool present).
# `terraform validate` needs `init` (provider download / network), so we use
# `fmt -check` as the always-offline syntax gate; YAML parse for the rest.
# ---------------------------------------------------------------------------

def _validate(iac: str, directory: Path) -> CheckResult:
    if iac == "terraform":
        binary = shutil.which("tofu") or shutil.which("terraform")
        if not binary:
            return CheckResult("validator_passes", NA, "no tofu/terraform on PATH")
        proc = subprocess.run(
            [binary, "fmt", "-check", "-recursive", str(directory)],
            capture_output=True, text=True,
        )
        ok = proc.returncode == 0
        return CheckResult("validator_passes", PASS if ok else FAIL, f"{Path(binary).name} fmt -check")

    if iac == "cloudformation":
        cfn = shutil.which("cfn-lint")
        template = next(iter(directory.glob("template.y*")), None) or next(
            iter(directory.glob("*.template")), None
        )
        if cfn and template:
            proc = subprocess.run([cfn, str(template)], capture_output=True, text=True)
            return CheckResult("validator_passes", PASS if proc.returncode == 0 else FAIL, "cfn-lint")
        return _yaml_parses(directory, "cfn-lint absent; YAML parse", cfn_tags=True)

    if iac == "crossplane":
        return _yaml_parses(directory, "YAML parse", cfn_tags=False)

    return CheckResult("validator_passes", NA, f"no validator for {iac}")


def _yaml_parses(directory: Path, detail: str, *, cfn_tags: bool) -> CheckResult:
    import yaml

    loader = yaml.SafeLoader
    if cfn_tags:
        class _CfnLoader(yaml.SafeLoader):
            pass

        def _multi(loader, tag_suffix, node):  # noqa: ANN001
            if isinstance(node, yaml.ScalarNode):
                return loader.construct_scalar(node)
            if isinstance(node, yaml.SequenceNode):
                return loader.construct_sequence(node)
            return loader.construct_mapping(node)

        _CfnLoader.add_multi_constructor("!", _multi)
        loader = _CfnLoader

    files = [p for p in directory.rglob("*.y*ml") if p.is_file()]
    files += [p for p in directory.glob("*.template") if p.is_file()]
    if not files:
        return CheckResult("validator_passes", NA, "no YAML files")
    try:
        for f in files:
            list(yaml.load_all(f.read_text(encoding="utf-8"), Loader=loader))
        return CheckResult("validator_passes", PASS, detail)
    except yaml.YAMLError as e:  # pragma: no cover - exercised by negative fixtures
        return CheckResult("validator_passes", FAIL, f"{detail}: {e}")


# ---------------------------------------------------------------------------
# The check registry.
# ---------------------------------------------------------------------------

def _c_encryption(iac, d, c):  # noqa: ANN001
    return CheckResult("encryption_at_rest", PASS if _matches_any(c, _ENCRYPTION) else FAIL)


def _c_public_block(iac, d, c):  # noqa: ANN001
    blocked = _matches_any(c, _PUBLIC_BLOCK)
    open_ = _matches_any(c, _PUBLIC_OPEN)
    ok = blocked and not open_
    detail = "" if ok else ("explicit public exposure found" if open_ else "no public-access block")
    return CheckResult("public_access_blocked", PASS if ok else FAIL, detail)


def _c_required_tags(iac, d, c):  # noqa: ANN001
    ok = _matches_any(c, [_REQUIRED_TAGS[0]]) and _matches_any(c, [_REQUIRED_TAGS[1]])
    return CheckResult("required_tags_present", PASS if ok else FAIL,
                       "" if ok else "missing managed-by and/or environment tag")


def _c_no_secrets(iac, d, c):  # noqa: ANN001
    hit = _find_hardcoded_secret(c)
    return CheckResult("no_hardcoded_secrets", FAIL if hit else PASS, hit or "")


def _c_deletion_safety(iac, d, c):  # noqa: ANN001
    return CheckResult("deletion_safety", PASS if _matches_any(c, _DELETION_SAFETY) else FAIL)


def _c_tls(iac, d, c):  # noqa: ANN001
    return CheckResult("tls_enforced", PASS if _matches_any(c, _TLS) else FAIL)


def _c_versioning(iac, d, c):  # noqa: ANN001
    return CheckResult("versioning_enabled", PASS if _matches_any(c, _VERSIONING) else FAIL)


CHECKS = {
    "validator_passes": lambda iac, d, c: _validate(iac, d),
    "encryption_at_rest": _c_encryption,
    "public_access_blocked": _c_public_block,
    "required_tags_present": _c_required_tags,
    "no_hardcoded_secrets": _c_no_secrets,
    "deletion_safety": _c_deletion_safety,
    "tls_enforced": _c_tls,
    "versioning_enabled": _c_versioning,
}


def score(iac: str, directory: Path, checks: list[str]) -> list[CheckResult]:
    """Run ``checks`` against the generated code in ``directory`` for ``iac``."""
    directory = Path(directory)
    content = _load(iac, directory)
    results = []
    for name in checks:
        fn = CHECKS.get(name)
        if fn is None:
            results.append(CheckResult(name, NA, "unknown check"))
            continue
        results.append(fn(iac, directory, content))
    return results


def summarize(results: list[CheckResult]) -> dict:
    passed = sum(1 for r in results if r.status == PASS)
    failed = sum(1 for r in results if r.status == FAIL)
    na = sum(1 for r in results if r.status == NA)
    applicable = passed + failed
    return {
        "passed": passed,
        "failed": failed,
        "na": na,
        "applicable": applicable,
        "pct": (100.0 * passed / applicable) if applicable else 100.0,
    }
