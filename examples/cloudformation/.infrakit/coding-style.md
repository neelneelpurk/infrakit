# Northwind Platform Engineering CloudFormation Coding Style Guide

> This document captures both universal CloudFormation standards (non-negotiable) and Northwind's
> project-specific conventions.

All CloudFormation engineers **MUST** follow these standards when generating infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Template Format** | YAML |
| **Template Format Version** | `2010-09-09` (only valid value) |
| **Tooling** | `aws cloudformation create-change-set` via GitHub Actions; change sets reviewed before execute in staging/prod |
| **Linter** | `cfn-lint` pinned in CI (fail on `E` and `W`); `cfn-guard` for tagging + encryption rules; Checkov for security scanning |

---

## 2. File Organization

**Template directory structure:**

```text
templates/
  s3-secure-bucket/
    template.yaml
    parameters/
      dev.json
      prod.json
    README.md
  rds-postgres/
    template.yaml
    parameters/
      dev.json
      prod.json
    README.md
```

**Non-negotiable rules:**

- One template per directory; each reusable unit gets its own `template.yaml`.
- YAML over JSON; format version `2010-09-09`.
- Example parameter files live under `parameters/`, one per environment.
- A `README.md` per template documents usage, parameters, outputs, and validation commands.

---

## 3. Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Logical ID (resource) | `PascalCase`, descriptive | `EventsBucket`, `EventsBucketKey` |
| Parameter name | `PascalCase` | `Environment`, `DataClassification` |
| Output name | `PascalCase` | `BucketArn` |
| Condition / Mapping | `PascalCase` | `IsProd`, `RegionMap` |

**Stack & physical naming**

- Stack name pattern: `{env}-{team}-{resource}` — e.g. `prod-orders-s3-events`.
- Never hardcode globally-unique physical names (S3 bucket names). Derive them with `!Sub` from
  `AWS::StackName` / parameters, or omit the name and let CloudFormation generate it.
- Export names are global per region/account — namespace with `!Sub "${AWS::StackName}-..."`.

---

## 4. Template Structure (MANDATORY STANDARDS)

### Section order

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: <required, one line>
Metadata:        # optional — parameter groups
Parameters:
Mappings:        # optional
Conditions:      # optional
Resources:       # required
Outputs:
```

### Intrinsic functions

- Prefer short form in YAML (`!Ref`, `!GetAtt`, `!Sub`, `!If`); never mix short/long form in one node.
- Use `!Sub` over `!Join`.
- Use pseudo parameters (`AWS::Region`, `AWS::AccountId`, `AWS::Partition`, `AWS::StackName`) — never hardcode.
- Gate environment-specific behaviour with `Conditions`, not duplicated templates.

### Formatting

- 2-space indentation. Group resources logically (security/keys → data → compute).
- Use `DependsOn` only when CloudFormation cannot infer ordering.

---

## 5. Parameters

```yaml
Parameters:
  DataClassification:
    Type: String
    Description: Data sensitivity tier; drives KMS key choice
    AllowedValues: [public, internal, confidential, restricted]
```

**Non-negotiable rules:**

- `Description` is **MANDATORY** for every parameter.
- Use the most specific `Type` available; constrain with `AllowedValues` / `AllowedPattern` / `MinValue`/`MaxValue` wherever the spec implies a constraint.
- Sensitive parameters set `NoEcho: true` with no plaintext `Default`.

---

## 6. Resource Tagging

Every taggable resource sets a `Tags` property with the six Northwind required tags:

| Tag Key | Value | Description |
|---------|-------|-------------|
| `managed-by` | `cloudformation` | Indicates CloudFormation-managed |
| `environment` | `!Ref Environment` | Deployment environment |
| `cost-center` | `!Ref CostCenter` | Billing allocation code |
| `team` | `!Ref Team` | Owning team |
| `project` | `!Ref Project` | Project identifier |
| `data-classification` | `!Ref DataClassification` | Data sensitivity tier |

**Strategy**: per-resource `Tags` lists in the template, plus org-wide tags applied at the stack level
via `aws cloudformation deploy --tags` (propagates to taggable resources missed by per-resource Tags).
Resource types that do not support `Tags` are documented in the template README.

---

## 7. Security Standards

- **Secrets**: never hardcoded; sensitive parameters `NoEcho: true`; values resolved at deploy via dynamic references.
- **Public access**: never default-open. S3 sets `PublicAccessBlockConfiguration` with all four flags `true`; any exposure is gated by a `Parameter` + `Condition`.
- **Encryption**: encryption at rest on all storage; customer-managed KMS keys for `confidential`/`restricted` data classifications.
- **Transit**: enforce TLS via resource/bucket policies (deny `aws:SecureTransport: false`).
- **Deletion safety**: prod stateful resources set `DeletionPolicy`/`UpdateReplacePolicy` to `Retain` (or `Snapshot` for databases).

---

## 8. Outputs & Exports

```yaml
Outputs:
  BucketArn:
    Description: ARN of the secure bucket
    Value: !GetAtt EventsBucket.Arn
    Export:
      Name: !Sub "${AWS::StackName}-BucketArn"
```

- `Description` mandatory on every output. Output specific attributes, not whole objects.
- `Export` only when consumed cross-stack; namespace export names with `!Sub "${AWS::StackName}-..."`.
- Never output a secret in plaintext.

---

## 9. Deployment & Change Management

- All staging/prod changes go through `aws cloudformation create-change-set` + review before execute.
- Stack policies protect stateful resources from accidental replacement.
- A change set showing `Replacement: True` on a stateful resource is a breaking change — document migration steps.
- Weekly drift detection runs across prod stacks.

---

## 10. Reference Example

See [`templates/s3-secure-bucket/template.yaml`](../templates/s3-secure-bucket/template.yaml) in this
example project for a complete, lint-clean template following every rule above.
