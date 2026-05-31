"""Eval cases: what we score and what we expect.

Two kinds:

- **golden** — the committed example deliverables. They are InfraKit's own claim
  of what good output looks like, so they must score 100% of their applicable
  security checks. If a golden case drops below 100%, either the example
  regressed or the bar moved — both worth a CI failure.
- **negative** — deliberately-insecure fixtures under ``evals/fixtures/``. They
  must score *below* a threshold. Their job is to prove the scorer actually
  discriminates: an eval that can't fail is worthless.

The full security check set is 8 checks. S3-style storage uses all 8; the
Crossplane RDS case drops the two S3-specific ones (TLS-in-transit and bucket
versioning don't apply to an RDS instance manifest).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ALL_CHECKS = [
    "validator_passes",
    "encryption_at_rest",
    "public_access_blocked",
    "required_tags_present",
    "no_hardcoded_secrets",
    "deletion_safety",
    "tls_enforced",
    "versioning_enabled",
]
# Storage-at-rest-only resources (e.g. an RDS instance) don't carry bucket
# versioning or an S3 TLS bucket policy.
NON_STORAGE_CHECKS = [c for c in ALL_CHECKS if c not in ("tls_enforced", "versioning_enabled")]


@dataclass
class Case:
    id: str
    iac: str
    path: Path
    checks: list[str]
    kind: str = "golden"  # golden | negative
    # negative cases must score AT OR BELOW this percentage to "pass" the eval.
    max_pct_if_negative: float = 40.0
    notes: str = ""


GOLDEN: list[Case] = [
    Case(
        id="terraform/s3-secure-bucket",
        iac="terraform",
        path=REPO_ROOT / "examples/terraform/modules/s3-secure-bucket",
        checks=ALL_CHECKS,
        notes="KMS, public-access block, TLS-only policy, versioning, force_destroy=false",
    ),
    Case(
        id="cloudformation/s3-secure-bucket",
        iac="cloudformation",
        path=REPO_ROOT / "examples/cloudformation/templates/s3-secure-bucket",
        checks=ALL_CHECKS,
        notes="BucketEncryption, PublicAccessBlock, SecureTransport deny, versioning, DeletionPolicy Retain",
    ),
    Case(
        id="crossplane/xpostgresql-instance",
        iac="crossplane",
        path=REPO_ROOT / "examples/crossplane/compositions/xpostgresql-instance",
        checks=NON_STORAGE_CHECKS,
        notes="storageEncrypted, publiclyAccessible=false, autoGeneratePassword, deletionProtection, required tag patches",
    ),
]

NEGATIVE: list[Case] = [
    Case(
        id="fixtures/insecure-terraform",
        iac="terraform",
        path=REPO_ROOT / "evals/fixtures/insecure-terraform",
        checks=ALL_CHECKS,
        kind="negative",
        notes="public bucket, no encryption, hardcoded password, no tags, force_destroy=true",
    ),
    Case(
        id="fixtures/insecure-cloudformation",
        iac="cloudformation",
        path=REPO_ROOT / "evals/fixtures/insecure-cloudformation",
        checks=ALL_CHECKS,
        kind="negative",
        notes="public bucket, no encryption, hardcoded MasterUserPassword, no tags, DeletionPolicy Delete",
    ),
]

ALL_CASES = GOLDEN + NEGATIVE
