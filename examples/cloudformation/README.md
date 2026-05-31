# CloudFormation example — `s3-secure-bucket`

Reproduce a complete, end-to-end InfraKit run for an AWS CloudFormation template against a fictional platform team (Northwind Logistics) that requires KMS-encrypted S3 buckets with the usual security gates: public access blocked, TLS-only access, versioning, and lifecycle tiering on noncurrent versions.

This directory contains everything you need to *re-run* the workflow yourself:

- The Northwind project standards under [`.infrakit/`](./.infrakit/) — context, coding style, tagging standard.
- The final template produced by the run under [`templates/s3-secure-bucket/`](./templates/s3-secure-bucket/).

The intermediate artifacts (spec, plan, tasks, reviews) are **not** committed — they're generated when you run the workflow.

---

## Prerequisites

- [InfraKit CLI](https://pypi.org/project/infrakit-cli/) — install with `uv tool install infrakit-cli` (or `pipx install infrakit-cli`).
- An AI coding agent — this guide uses Claude Code; substitute your favourite (see the [supported list](../../README.md#-supported-ai-coding-agents)).
- The [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and (recommended) [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) for validation.

---

## Run the workflow against this scenario

### 1. Copy the example into a fresh project

```bash
cp -r examples/cloudformation/ /tmp/northwind-cfn
cd /tmp/northwind-cfn
```

The `.infrakit/` directory is already populated with Northwind's standards. The `templates/` directory contains the *final* output for reference — feel free to delete it before re-running:

```bash
rm -rf templates
```

### 2. Bootstrap the project for your AI agent

```bash
infrakit init --here --ai claude --iac cloudformation --script sh --force --no-git
```

This is idempotent: existing `.infrakit/*.md` files are preserved. The command writes per-agent slash-command files into `.claude/commands/` (or `.gemini/commands/`, `.github/agents/`, etc.) based on `--ai`.

### 3. Start your AI agent in this directory

```bash
claude              # or: gemini, codex, copilot, etc.
```

You should see `/infrakit:*` slash commands available.

### 4. Walk through the multi-persona pipeline

Run these commands in order. Each one writes its output to `.infrakit_tracks/tracks/<track-name>/`.

```text
/infrakit:create_cloudformation_code s3-secure-bucket ./templates/s3-secure-bucket
```

This launches the four-persona pipeline:

- **Cloud Solutions Engineer** — asks clarifying questions about the bucket's purpose, environment, data classification, lifecycle needs. Use the answers below ("Reference inputs") to reproduce the example.
- **Cloud Architect** — presents 2–3 design options with cost/reliability trade-offs (KMS key choice, lifecycle tiering, whether to gate cross-region replication behind a Condition). Pick the default.
- **Cloud Security Engineer** — asks which compliance frameworks apply. For this example, select **SOC 2 + PCI-DSS**.

Once the spec is confirmed:

```text
/infrakit:plan <track-name>
/infrakit:implement <track-name>
/infrakit:analyze <track-name>
/infrakit:architect-review <track-name>
/infrakit:security-review <track-name>
/infrakit:review ./templates/s3-secure-bucket
```

`<track-name>` follows the format `s3-secure-bucket-<YYYYMMDD-HHMMSS>`.

> **Lighter path:** for a routine change you can skip the multi-persona spec ceremony:
> `/infrakit:quick_fix Add server access logging to ./templates/s3-secure-bucket`.
> The CloudFormation Engineer plans the change, generates a task list, shows you `plan.md` +
> `tasks.md` to approve, then implements — verifying property names against the AWS docs,
> applying the required tags, and gating on `cfn-lint`.

### 5. Verify the produced template

```bash
cd templates/s3-secure-bucket
cfn-lint template.yaml
aws cloudformation validate-template --template-body file://template.yaml
```

Both should pass.

---

## Reference inputs

When the Cloud Solutions Engineer asks clarifying questions, use these answers to reproduce the bundled template verbatim:

| Question | Answer |
|---|---|
| Bucket purpose | Application data storage |
| Environment | flexible — caller provides via the `Environment` parameter |
| Data classification | flexible — caller provides via `DataClassification` |
| Encryption | Customer-managed KMS key, rotation enabled, 30-day deletion window |
| Public access | All four `PublicAccessBlockConfiguration` flags `true`; never overridable |
| Object ownership | `BucketOwnerEnforced` (ACLs disabled) |
| TLS | Bucket policy denies `aws:SecureTransport == false` |
| Versioning | Always enabled |
| Lifecycle | Noncurrent → STANDARD_IA at 30d, GLACIER at 90d, expire at 365d (all configurable) |
| Cross-region replication | Out of scope for the template; documented as a prod follow-up |
| Deletion safety | `DeletionPolicy: Retain` + `UpdateReplacePolicy: Retain` on the bucket and KMS key |

The Architect-review step should choose the **per-instance customer-managed KMS key** design.

The Security-review step should mark CC6.1, CC6.7, CC6.8, PCI 3.5, PCI 4.2 as `COMPLIANT`, with two `LOW` notes (server access logging and Object Lock are explicitly out of scope for this template).

---

## What lands in your project after a complete run

```text
northwind-cfn/
├── .claude/commands/              # 12 rendered slash commands
├── .infrakit/
│   ├── config.yaml
│   ├── context.md                 # Northwind's constitution
│   ├── coding-style.md            # CloudFormation coding standards
│   ├── tagging-standard.md
│   ├── agent_personas/            # 3 generic + cloudformation_engineer
│   └── memory/
├── .infrakit_tracks/
│   ├── tracks.md
│   └── tracks/s3-secure-bucket-20260415-093000/
│       ├── spec.md                # from /infrakit:create_cloudformation_code
│       ├── plan.md                # from /infrakit:plan
│       ├── tasks.md               # auto-generated by /infrakit:plan
│       ├── analyze.md             # from /infrakit:analyze
│       ├── architect-review.md
│       ├── security-review.md
│       └── review.md
└── templates/s3-secure-bucket/
    ├── template.yaml
    ├── parameters/
    │   ├── dev.json
    │   └── prod.json
    └── README.md
```

The `.infrakit_tracks/` directory is the audit trail. Commit it to git alongside the code so future readers can see every decision, every clarifying question, every compliance finding that led to the current implementation.

---

## See also

- [`examples/terraform/`](../terraform/) — the same secure-bucket scenario as a Terraform module.
- [`examples/crossplane/`](../crossplane/) — an `XPostgreSQLInstance` Crossplane composition.
