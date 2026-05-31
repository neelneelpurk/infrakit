# InfraKit evals

Until this existed, every claim about InfraKit's output quality was a guess. This
is the measuring stick: a mechanical, headless scorer that checks whether
generated IaC actually carries the secure-defaults the personas promise.

## The two halves of an eval

An eval has a **generator** (produces IaC) and a **scorer** (grades it). They are
separate on purpose:

- **`scorer.py`** — deterministic, offline, dependency-light. Reads generated
  Terraform / Crossplane / CloudFormation as text (comments stripped) and runs
  the secure-default checks. This is the reusable half and the part CI runs.
- **generator** — what produced the code:
  - `committed` (default): score the example deliverables checked into `examples/`.
    Free, deterministic, runs in CI. It answers *"do our own shipped examples meet
    the bar, and does the scorer work?"*
  - `llm` (hook, not yet wired): drive the real InfraKit pipeline
    (`create_* → plan → implement`) with an agent against each case's requirement,
    then score whatever it writes. This is what answers the real question —
    *does the 4-persona pipeline produce secure IaC, and does it beat one prompt?*
    It needs an agent/API key and is non-deterministic, so it is intentionally
    kept out of CI. See the hook in `run.py`.

## The checks (secure-defaults)

| Check | What it verifies |
|-------|------------------|
| `validator_passes` | `tofu fmt -check` / `cfn-lint` / YAML parse passes (NA if no tool) |
| `encryption_at_rest` | KMS/SSE encryption is configured |
| `public_access_blocked` | public access is blocked and not explicitly opened |
| `required_tags_present` | `managed-by` + `environment` tags are applied |
| `no_hardcoded_secrets` | no literal password/secret (refs & generators are fine) |
| `deletion_safety` | `force_destroy=false` / `DeletionPolicy: Retain` / deletion protection |
| `tls_enforced` | secure-transport enforced (storage only) |
| `versioning_enabled` | object versioning on (storage only) |

The checks are heuristic by design — they confirm the secure-default *made it into
the code*. That's the signal: a dropped `block_public_acls` shows up as a failing
check no matter what the surrounding prose claims.

## Cases

- **golden** — the 3 committed example deliverables (`examples/{terraform,crossplane,cloudformation}/…`). Must score **100%** of applicable checks.
- **negative** — deliberately-insecure fixtures under `fixtures/`. Must score **≤40%**. They prove the scorer can fail; an eval that can't fail is worthless. (They currently score 12% — only syntax passes.)

## Run it

```bash
python evals/run.py            # scorecard, non-zero exit on any miss
python evals/run.py --verbose  # show every check
uv run pytest tests/test_evals.py   # the same suite under pytest (what CI runs)
```

## Adding a case

Add a `Case(...)` to `cases.py` pointing at a directory of generated IaC and the
checks that apply (drop `tls_enforced`/`versioning_enabled` for non-storage
resources). Golden cases must hit 100%; negative cases must stay under their bar.

## Wiring the LLM generator (the next step)

Implement the `llm` branch in `run.py`: for each case, run the InfraKit pipeline
headless against a fixed requirement string, write the output to a temp dir, and
call `scorer.score(case.iac, tmp, case.checks)`. Run a single-prompt baseline the
same way. The delta between "full pipeline" and "one prompt" — measured by this
scorer — is the empirical answer to whether the multi-persona pipeline earns its
complexity.
