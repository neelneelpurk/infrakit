# Tagging Standard

All CloudFormation-managed resources at Northwind Platform MUST carry the tags listed below. The
`managed-by`, `environment`, `cost-center`, `team`, `project`, and `data-classification` tags are
enforced by AWS Config rules in the `security-audit` account — non-compliant resources page the
platform on-call within 30 minutes.

---

## Required Tags

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `managed-by` | Static: `cloudformation` | Identifies CloudFormation-managed resources. Used by audit tooling to distinguish from console-created or ad-hoc resources. |
| `environment` | `!Ref Environment` | One of `dev`, `staging`, `prod`. |
| `cost-center` | `!Ref CostCenter` | Billing allocation code. Format: `CC-NNNN` (e.g., `CC-3017`). |
| `team` | `!Ref Team` | Owning team name. Allowed values: `orders`, `fulfillment`, `returns`, `analytics`, `customer-portal`, `platform`. |
| `project` | `!Ref Project` | Project identifier (default `northwind-platform`). |
| `data-classification` | `!Ref DataClassification` | One of `public`, `internal`, `confidential`, `restricted`. Drives encryption-key choice and access-review cadence. |

## Optional Tags

| Tag Key | Description |
|---------|-------------|
| `owner` | Individual owner email for escalation. |
| `created-by` | CI/CD pipeline or user that initiated the deploy (`github-actions` for normal flow). |
| `compliance-scope` | `pci`, `sox`, `hipaa` — only set when the resource is in scope for the named framework. |

## Application Pattern

Every taggable resource sets a `Tags` property listing the six required tags, each sourced from a
template `Parameter` (or a static value for `managed-by`). In addition, the CI deploy step passes the
same tags at the **stack** level (`aws cloudformation deploy --tags managed-by=cloudformation
environment=prod …`) so stack-level tags propagate to every resource that supports tagging —
defense-in-depth coverage for any resource whose `Tags` property is missed.

## Enforcement

- **At deploy time**: `cfn-guard` rules verify every taggable resource carries the required tag keys before a change set is created.
- **In account**: AWS Config managed rule `required-tags` runs every 6 hours on all supported resource types.
- **In CI**: `cfn-lint` and Checkov scans block PRs that introduce resources without required tags.

## Exception Process

Resource types that genuinely do not support a `Tags` property (some AWS service internals) must be
documented in the resource's track `spec.md` under "Tagging Exceptions". Stack-level `--tags` cover
most of these. The track must be reviewed and approved by the platform team lead before deploy.
