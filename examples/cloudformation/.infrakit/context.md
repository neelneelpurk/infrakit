# Northwind Platform Infrastructure Constitution

## Project Information

| Property | Value |
|----------|-------|
| **Project Name** | Northwind Platform Engineering |
| **Cloud Provider** | AWS |
| **Environments** | dev, staging, prod |
| **Last Updated** | 2026-04-12 |

## Overview

Northwind Logistics' Platform Engineering team manages shared AWS infrastructure for 5 product teams
(orders, fulfillment, returns, analytics, customer-portal) using AWS CloudFormation. Reusable
templates live in a central `infra-templates` monorepo; product teams deploy them via a CI pipeline
that creates and reviews **change sets** before executing. Stacks are named
`{env}-{team}-{resource}` and deployed per environment account.

---

## Architecture Decisions

### IaC Tool & Strategy

| Decision | Choice |
|----------|--------|
| **IaC Tool** | AWS CloudFormation — YAML templates (`AWSTemplateFormatVersion: "2010-09-09"`) |
| **Deployment Engine** | GitHub Actions → `aws cloudformation create-change-set` on PR; reviewed change set executed on merge. No `aws cloudformation deploy` direct-to-prod from laptops. |
| **Linting** | `cfn-lint` pinned in CI (fail on `E` and `W` rules); `cfn-guard` policy rules for tagging + encryption; Checkov for security scanning. |
| **Template Distribution** | Templates referenced by Git tag from `infra-templates` (SemVer); nested stacks pull child templates from a versioned S3 artifacts bucket. |

### Cloud Account Structure

AWS Organizations with 1 management account and 5 member accounts: `shared-services`, `dev`,
`staging`, `prod`, and `security-audit`. All member accounts reside under the Platform OU inside
the Northwind Root OU. Cross-account access is via STS AssumeRole from the `shared-services` account
only; product accounts have no direct cross-account trust with each other.

**Organization Hierarchy:**

```text
Root OU (Northwind Logistics)
└── Platform OU
    ├── shared-services  (Transit Gateway, Route53 private zones, central CloudTrail, CI runners)
    ├── dev              (development workloads)
    ├── staging          (staging workloads, mirrors prod config)
    ├── prod             (production workloads, full DR + compliance)
    └── security-audit   (read-only CloudTrail aggregation, GuardDuty master, Security Hub)
```

### Network Architecture

| Property | Value |
|----------|-------|
| **Topology** | Hub-and-spoke via AWS Transit Gateway in the `shared-services` account |
| **VPC Strategy** | Per-account VPCs — `dev` 10.10.0.0/16, `staging` 10.11.0.0/16, `prod` 10.12.0.0/16, `shared-services` 10.0.0.0/16 |
| **Connectivity** | Prod: private subnets only, egress via NAT Gateway in `shared-services`. Dev: public subnets permitted with mandatory restrictive security groups. No direct internet ingress to prod workloads except via ALB+WAF. |

---

## Resource Organization

### Environments

Three environments — `dev`, `staging`, `prod` — each mapping to a separate AWS account.

- **dev**: Active development; no DR requirement; relaxed controls (public subnets allowed for testing).
- **staging**: Mirrors prod configuration; single-AZ acceptable; 8h RTO / 4h RPO.
- **prod**: Full security, compliance, and DR policies; Multi-AZ mandatory; 4h RTO / 1h RPO.

### Naming Conventions

**Convention**: `kebab-case` for stacks; `PascalCase` for template logical IDs.

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| Stack name | `{env}-{team}-{resource}` | `prod-orders-s3-events`, `dev-analytics-rds-warehouse` |
| Logical ID (in template) | `PascalCase` | `EventsBucket`, `EventsBucketKey` |
| Template directory | `templates/<template-name>/` | `templates/s3-secure-bucket/` |
| Exported output | `${AWS::StackName}-<Name>` | `prod-orders-s3-events-BucketArn` |
| Track Name | `<template>-<YYYYMMDD-HHMMSS>` | `s3-secure-bucket-20260415-093000` |

### Tagging Strategy

**Required Tags** (every taggable resource MUST carry these — enforced via AWS Config rules in `security-audit`):

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `managed-by` | Static: `cloudformation` | Identifies CloudFormation-managed resources |
| `environment` | `!Ref Environment` | Target environment (`dev`/`staging`/`prod`) |
| `cost-center` | `!Ref CostCenter` | Billing allocation code (e.g., `CC-3017`) |
| `team` | `!Ref Team` | Owning team (e.g., `orders`, `analytics`) |
| `project` | `!Ref Project` | Project identifier (e.g., `northwind-platform`) |
| `data-classification` | `!Ref DataClassification` | One of `public`, `internal`, `confidential`, `restricted` |

Org-wide tags are additionally applied at the **stack** level via `aws cloudformation deploy --tags`
so even resources missed by a per-resource `Tags` property inherit them.

---

## Cloud Provider Defaults

**Provider**: AWS

| Setting | Default Value |
|---------|---------------|
| Default Region | `us-east-1` (primary), `us-west-2` (DR for prod) |
| Deploy Authentication | CI OIDC role: `arn:aws:iam::<account>:role/cfn-deployer` (assumed per-env) |
| Change Sets | Required for staging and prod; `--no-execute-changeset` then review then execute |

---

## Security Standards

- **Encryption at rest required** on all storage resources (S3, RDS, EBS, Secrets Manager, SQS, SNS).
- **Customer-managed KMS keys** for `confidential` and `restricted` data classifications; AWS-managed keys acceptable for `internal` and `public`.
- **TLS 1.2+ required** for all data in transit; enforce via bucket/endpoint policies.
- **No public network access** in prod; any exception requires a documented security review and an approved waiver in the resource's track directory, plus a `Parameter` + `Condition` gating the exposure.
- **MFA required** for all AWS console access (enforced via SCP on the Platform OU).
- **Least-privilege IAM**: no wildcard `*` actions in production policies.
- **No plaintext secrets** in templates — sensitive parameters use `NoEcho: true`; secret values resolve at deploy time via dynamic references (`{{resolve:secretsmanager:...}}`, `{{resolve:ssm-secure:...}}`).
- **Stateful resources** set `DeletionPolicy` and `UpdateReplacePolicy` to `Retain` (or `Snapshot` for databases) in prod.

---

## Compliance

- **SOC 2 Type II** — CloudTrail logging enabled on all accounts with 1-year retention in S3 (Glacier after 90 days); quarterly access reviews via automated report.
- **PCI-DSS** — Customer-portal workloads isolated to a dedicated VPC subnet group with security groups restricted to required egress only; cardholder data tokenized at the edge, never stored in S3 or RDS in cleartext.

---

## DR & HA

| Requirement | Production | Staging | Dev |
|-------------|------------|---------|-----|
| RTO | 4 hours | 8 hours | N/A |
| RPO | 1 hour | 4 hours | N/A |
| HA | Multi-AZ mandatory for RDS, ElastiCache, ALB, NAT Gateway | Single-AZ acceptable | None |

Prod S3 critical buckets: cross-region replication to `us-west-2` (out of scope for the example
template — see its README). DR runbook: `docs/runbooks/disaster-recovery.md`.

**Availability SLOs**:

| Environment | Availability SLO | Latency Target |
|-------------|------------------|----------------|
| `prod` | 99.9% monthly | p99 < 500ms for control-plane API calls |
| `staging` | 99.5% monthly | best-effort |
| `dev` | best-effort | best-effort |

---

## Organization Standards

- All stacks and resources must follow the naming conventions above.
- All taggable resources must carry the required tags (see `.infrakit/tagging-standard.md`).
- All production resources must meet the security baseline above.
- Template outputs must expose any value a downstream stack would otherwise hardcode (ARNs, IDs, endpoints, KMS key ARNs) and `Export` them when consumed cross-stack.
- Stateful resources in prod must set `DeletionPolicy`/`UpdateReplacePolicy`.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-08 | **Last Amended**: 2026-04-12
